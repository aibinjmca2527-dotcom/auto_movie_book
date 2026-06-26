from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import httpx
import asyncio
import os
import re
from datetime import datetime
from contextlib import asynccontextmanager
from bs4 import BeautifulSoup
from twilio.rest import Client as TwilioClient

# ─── Config ────────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_PHONE    = os.getenv("TWILIO_FROM_PHONE", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_PHONE           = os.getenv("USER_PHONE", "")
USER_WHATSAPP        = os.getenv("USER_WHATSAPP", "")
DB_PATH              = os.getenv("DB_PATH", "cinealert.db")

# ─── Kerala Cities ─────────────────────────────────────────────────────────────
KERALA_CITIES = {
    "thiruvananthapuram": "TVM", "trivandrum": "TVM",
    "kollam": "KOLL", "pathanamthitta": "PTNA",
    "alappuzha": "ALPY", "alapuzha": "ALPY", "alleppey": "ALPY",
    "kottayam": "KTYM", "changanassery": "KTYM", "changanacherry": "KTYM",
    "pala": "KTYM", "ettumanoor": "KTYM", "vaikom": "KTYM",
    "idukki": "IDK", "thodupuzha": "IDK",
    "ernakulam": "ERNAKULAM", "kochi": "KOCHI", "cochin": "KOCHI",
    "aluva": "ERNAKULAM", "angamaly": "ERNAKULAM", "perumbavoor": "ERNAKULAM",
    "muvattupuzha": "ERNAKULAM", "kothamangalam": "ERNAKULAM",
    "thrissur": "TCR", "trichur": "TCR", "irinjalakuda": "TCR",
    "chalakudy": "TCR", "guruvayur": "TCR", "kunnamkulam": "TCR",
    "palakkad": "PKD", "palghat": "PKD", "ottapalam": "PKD", "shoranur": "PKD",
    "malappuram": "MLM", "manjeri": "MLM", "tirur": "MLM",
    "perinthalmanna": "MLM", "ponnani": "MLM", "nilambur": "MLM",
    "kozhikode": "CALICUT", "calicut": "CALICUT", "vatakara": "CALICUT",
    "wayanad": "WYD", "kalpetta": "WYD", "mananthavady": "WYD",
    "kannur": "KANN", "cannanore": "KANN", "thalassery": "KANN", "payyannur": "KANN",
    "kasaragod": "KSD", "kanhangad": "KSD",
    "kayamkulam": "ALPY", "cherthala": "ALPY", "haripad": "ALPY",
    "mavelikkara": "ALPY", "ambalapuzha": "ALPY",
    "punalur": "KOLL", "karunagappally": "KOLL",
    "nedumangad": "TVM", "neyyattinkara": "TVM", "attingal": "TVM",
    "varkala": "TVM", "kazhakkoottam": "TVM",
    "adoor": "PTNA", "thiruvalla": "PTNA", "ranni": "PTNA",
    "kalamassery": "ERNAKULAM", "tripunithura": "ERNAKULAM",
    "edappally": "ERNAKULAM", "kakkanad": "ERNAKULAM",
    "fort kochi": "KOCHI", "mattancherry": "KOCHI",
    "chavakkad": "TCR", "kodungallur": "TCR", "wadakkanchery": "TCR",
    "kondotty": "MLM", "tanur": "MLM", "parappanangadi": "MLM",
    "mukkam": "CALICUT", "kunnamangalam": "CALICUT", "feroke": "CALICUT",
    "sulthan bathery": "WYD", "mananthavady": "WYD",
    "iritty": "KANN", "taliparamba": "KANN",
    "hosdurg": "KSD",
}

def search_kerala_cities(q: str):
    q = q.lower().strip()
    results = []
    for city, code in KERALA_CITIES.items():
        if q in city.lower():
            results.append({"name": city.title(), "code": code})
    results.sort(key=lambda x: (not x["name"].lower().startswith(q), x["name"]))
    return results[:15]

def get_city_code(city: str) -> str:
    return KERALA_CITIES.get(city.lower().strip(), city.upper())

# ─── DB ────────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            code        TEXT UNIQUE NOT NULL,
            poster      TEXT,
            language    TEXT,
            genre       TEXT,
            status      TEXT DEFAULT 'now_showing',
            updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monitors (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_name   TEXT NOT NULL,
            movie_code   TEXT NOT NULL,
            movie_poster TEXT,
            city         TEXT NOT NULL,
            city_code    TEXT NOT NULL,
            theatre      TEXT,
            theatre_url  TEXT,
            status       TEXT DEFAULT 'active',
            booking_url  TEXT,
            notified     INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            opened_at    TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_id INTEGER,
            message    TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ─── BMS Headers ───────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,ml;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://in.bookmyshow.com/",
}

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "x-app-code": "WEB",
}

# ─── Scrape Movies From BMS ────────────────────────────────────────────────────
SCRAPE_URLS = [
    ("https://in.bookmyshow.com/movies/kochi",               "now_showing"),
    ("https://in.bookmyshow.com/movies-coming-soon/kochi",   "coming_soon"),
    ("https://in.bookmyshow.com/movies/alappuzha",           "now_showing"),
    ("https://in.bookmyshow.com/movies-coming-soon/alappuzha","coming_soon"),
]

async def scrape_movies_from_page(url: str, status: str) -> list:
    movies = []
    try:
        async with httpx.AsyncClient(timeout=20, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"Scraping {url} → {resp.status_code}")
            if resp.status_code != 200:
                return movies
            soup = BeautifulSoup(resp.text, "html.parser")

            # Method 1: Look for __NEXT_DATA__ JSON (Next.js)
            next_data = soup.find("script", {"id": "__NEXT_DATA__"})
            if next_data:
                import json
                try:
                    data = json.loads(next_data.string)
                    # Navigate the Next.js data structure
                    props = data.get("props", {}).get("pageProps", {})
                    movie_list = (
                        props.get("moviesData", []) or
                        props.get("movies", []) or
                        props.get("data", {}).get("movies", []) or
                        []
                    )
                    for m in movie_list:
                        name   = m.get("name") or m.get("title") or m.get("EventTitle") or ""
                        code   = m.get("code") or m.get("id") or m.get("EventCode") or ""
                        poster = m.get("imageUrl") or m.get("poster") or m.get("EventImageUrl") or ""
                        lang   = m.get("language") or m.get("EventLanguage") or ""
                        genre  = m.get("genre") or m.get("EventGenre") or ""
                        if name and code:
                            movies.append({"name": name, "code": code, "poster": poster,
                                         "language": lang, "genre": genre, "status": status})
                    if movies:
                        print(f"  Got {len(movies)} movies from __NEXT_DATA__")
                        return movies
                except Exception as e:
                    print(f"  Next data parse error: {e}")

            # Method 2: Scrape HTML elements
            # BMS uses various class names
            selectors = [
                "a[data-test='movie-card-link']",
                ".movie-card-container a",
                "div[class*='MovieCard'] a",
                "div[class*='movie-card'] a",
                ".card-container",
                "li[class*='movie']",
            ]
            cards = []
            for sel in selectors:
                cards = soup.select(sel)
                if cards:
                    print(f"  Found {len(cards)} cards with selector: {sel}")
                    break

            for card in cards[:30]:
                name   = (card.get("title") or card.get("aria-label") or
                         (card.select_one("p, span, div[class*='name'], div[class*='title']") or card).get_text(strip=True))
                href   = card.get("href", "")
                code   = ""
                if href:
                    match = re.search(r'-([A-Z0-9]+)-MT', href)
                    if match:
                        code = match.group(1)
                img    = card.select_one("img")
                poster = img.get("src") or img.get("data-src") or "" if img else ""
                if name and code and len(code) > 3:
                    movies.append({"name": name, "code": code, "poster": poster,
                                 "language": "", "genre": "", "status": status})

            print(f"  Got {len(movies)} movies from HTML scraping")
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
    return movies

async def scrape_via_api(status: str) -> list:
    """Try BMS internal API as fallback"""
    movies = []
    try:
        regions = ["KOCHI", "ALPY", "TVM", "KTYM"]
        cmd = "GETMOVIELIST" if status == "now_showing" else "GETCOMINGSOON"
        for region in regions:
            url = f"https://in.bookmyshow.com/serv/getData?cmd={cmd}&region={region}"
            async with httpx.AsyncClient(timeout=12, headers=API_HEADERS, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    import json
                    try:
                        data = resp.json()
                        items = data.get("BookMyShow", {}).get("arrEvents", []) or []
                        for item in items:
                            name   = item.get("EventTitle", "")
                            code   = item.get("EventCode", "")
                            poster = item.get("EventImageUrl", "")
                            lang   = item.get("EventLanguage", "")
                            genre  = item.get("EventGenre", "")
                            if name and code:
                                movies.append({"name": name, "code": code, "poster": poster,
                                             "language": lang, "genre": genre, "status": status})
                    except:
                        pass
            if movies:
                break
    except Exception as e:
        print(f"API scrape error: {e}")
    return movies

async def refresh_movies():
    """Scrape BMS and save all movies to DB"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshing movie list...")
    all_movies = []

    # Scrape from pages
    for url, status in SCRAPE_URLS:
        movies = await scrape_movies_from_page(url, status)
        all_movies.extend(movies)
        await asyncio.sleep(1)  # polite delay

    # If scraping failed, try API
    if not all_movies:
        print("Page scraping got 0 movies, trying API...")
        for status in ["now_showing", "coming_soon"]:
            api_movies = await scrape_via_api(status)
            all_movies.extend(api_movies)

    # Deduplicate by code
    seen = set()
    unique = []
    for m in all_movies:
        if m["code"] not in seen:
            seen.add(m["code"])
            unique.append(m)

    print(f"Total unique movies found: {len(unique)}")

    # Save to DB
    if unique:
        conn = get_db()
        for m in unique:
            conn.execute("""
                INSERT INTO movies (name, code, poster, language, genre, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    name=excluded.name, poster=excluded.poster,
                    language=excluded.language, genre=excluded.genre,
                    status=excluded.status, updated_at=excluded.updated_at
            """, (m["name"], m["code"], m["poster"], m.get("language",""),
                  m.get("genre",""), m.get("status","now_showing"), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"Saved {len(unique)} movies to DB ✅")

# ─── Theatre Search ─────────────────────────────────────────────────────────────
async def search_theatres_bms(city_code: str, movie_code: str):
    url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json&lat=0&lon=0&layoutId=5&ua=Desktop"
    try:
        async with httpx.AsyncClient(timeout=15, headers=API_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"Theatre search: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                theatres = []
                venues = data.get("BookMyShow", {}).get("arrShowDetails", [])
                for venue in venues[:25]:
                    name = venue.get("ShowName", "")
                    area = venue.get("ShowAddress", "")
                    code = venue.get("ShowCode", "")
                    if name:
                        theatres.append({
                            "name": name, "area": area, "code": code,
                            "maps_url": f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}+{area.replace(' ', '+')}"
                        })
                return theatres
    except Exception as e:
        print(f"Theatre error: {e}")
    return []

# ─── Booking Check ──────────────────────────────────────────────────────────────
def build_bms_url(movie_code: str, city_code: str, movie_name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', movie_name.lower()).strip('-')
    return f"https://in.bookmyshow.com/buytickets/{slug}/movie-{city_code.lower()}-{movie_code}-MT/"

async def check_booking_open(movie_code: str, city_code: str) -> bool:
    try:
        url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json"
        async with httpx.AsyncClient(timeout=12, headers=API_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                shows = data.get("BookMyShow", {}).get("arrShowDetails", [])
                return len(shows) > 0
    except Exception as e:
        print(f"Booking check error: {e}")
    return False

# ─── Notifications ──────────────────────────────────────────────────────────────
def send_whatsapp(message: str):
    try:
        if not TWILIO_ACCOUNT_SID:
            return
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=f"whatsapp:{USER_WHATSAPP}", body=message)
        print("WhatsApp sent!")
    except Exception as e:
        print(f"WhatsApp error: {e}")

def send_call(message: str):
    try:
        if not TWILIO_ACCOUNT_SID:
            return
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twiml = f"<Response><Say>{message}</Say><Say>Booking is now open. Go book your tickets now!</Say></Response>"
        client.calls.create(from_=TWILIO_FROM_PHONE, to=USER_PHONE, twiml=twiml)
        print("Call sent!")
    except Exception as e:
        print(f"Call error: {e}")

# ─── Background Tasks ───────────────────────────────────────────────────────────
async def movie_refresh_loop():
    """Refresh movie list every 1 hour"""
    while True:
        await refresh_movies()
        await asyncio.sleep(3600)  # 1 hour

async def monitor_loop():
    """Check booking every 30 seconds"""
    print("Monitor loop started...")
    while True:
        try:
            conn = get_db()
            monitors = conn.execute("SELECT * FROM monitors WHERE status='active' AND notified=0").fetchall()
            conn.close()
            for monitor in monitors:
                mid        = monitor["id"]
                movie_name = monitor["movie_name"]
                movie_code = monitor["movie_code"]
                city_code  = monitor["city_code"]
                theatre    = monitor["theatre"] or ""
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking: {movie_name} in {city_code}")
                is_open = await check_booking_open(movie_code, city_code)
                if is_open:
                    booking_url = build_bms_url(movie_code, city_code, movie_name)
                    conn = get_db()
                    conn.execute(
                        "UPDATE monitors SET notified=1, status='opened', booking_url=?, opened_at=? WHERE id=?",
                        (booking_url, datetime.now().isoformat(), mid)
                    )
                    conn.execute("INSERT INTO logs (monitor_id, message) VALUES (?, ?)",
                        (mid, f"🎬 Booking opened! {movie_name} → {booking_url}"))
                    conn.commit()
                    conn.close()
                    msg = (f"🎬 BOOKING OPEN!\n🎥 {movie_name}\n🏙️ City: {city_code}\n"
                           f"🎭 Theatre: {theatre}\n🔗 {booking_url}")
                    send_whatsapp(msg)
                    send_call(f"Alert! Booking is now open for {movie_name}. Go book your tickets now!")
                    print(f"✅ NOTIFIED: {movie_name}")
        except Exception as e:
            print(f"Monitor loop error: {e}")
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start both background tasks
    t1 = asyncio.create_task(movie_refresh_loop())
    t2 = asyncio.create_task(monitor_loop())
    yield
    t1.cancel()
    t2.cancel()

# ─── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(title="CineAlert API v3", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MonitorCreate(BaseModel):
    movie_name:   str
    movie_code:   str
    movie_poster: Optional[str] = ""
    city:         str
    theatre:      Optional[str] = ""
    theatre_url:  Optional[str] = ""

# ─── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) as c FROM movies").fetchone()["c"]
    conn.close()
    return {"status": "CineAlert v3 running!", "movies_in_db": count}

@app.get("/api/search/movies")
def api_search_movies(q: str):
    if len(q) < 2:
        return {"movies": []}
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM movies WHERE name LIKE ? ORDER BY status ASC, name ASC LIMIT 12",
        (f"%{q}%",)
    ).fetchall()
    conn.close()
    movies = [{"name": r["name"], "code": r["code"], "poster": r["poster"],
               "lang": r["language"], "genre": r["genre"], "status": r["status"]} for r in rows]
    return {"movies": movies}

@app.get("/api/movies/all")
def api_all_movies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM movies ORDER BY status ASC, name ASC").fetchall()
    conn.close()
    return {"movies": [dict(r) for r in rows], "total": len(rows)}

@app.get("/api/movies/refresh")
async def api_refresh_movies():
    asyncio.create_task(refresh_movies())
    return {"message": "Movie refresh started!"}

@app.get("/api/search/cities")
def api_cities(q: str = ""):
    if not q:
        return {"cities": []}
    return {"cities": search_kerala_cities(q)}

@app.get("/api/search/theatres")
async def api_search_theatres(city: str, movie_code: str):
    city_code = get_city_code(city)
    theatres  = await search_theatres_bms(city_code, movie_code)
    return {"theatres": theatres}

@app.post("/api/monitor")
def create_monitor(data: MonitorCreate):
    city_code = get_city_code(data.city)
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM monitors WHERE movie_code=? AND city_code=? AND status='active'",
        (data.movie_code, city_code)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Already monitoring this movie in this city!")
    cur = conn.execute(
        "INSERT INTO monitors (movie_name,movie_code,movie_poster,city,city_code,theatre,theatre_url) VALUES (?,?,?,?,?,?,?)",
        (data.movie_name, data.movie_code, data.movie_poster, data.city,
         city_code, data.theatre, data.theatre_url)
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return {"id": mid, "message": f"Monitoring {data.movie_name} in {data.city}!"}

@app.get("/api/monitors")
def get_monitors():
    conn = get_db()
    rows = conn.execute("SELECT * FROM monitors ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"monitors": [dict(r) for r in rows]}

@app.delete("/api/monitor/{mid}")
def delete_monitor(mid: int):
    conn = get_db()
    conn.execute("UPDATE monitors SET status='cancelled' WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    return {"message": "Cancelled"}

@app.get("/api/logs")
def get_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}
