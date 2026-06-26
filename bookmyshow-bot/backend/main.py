from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3, httpx, asyncio, os, re, json
from datetime import datetime
from contextlib import asynccontextmanager
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
    "sulthan bathery": "WYD", "iritty": "KANN", "taliparamba": "KANN",
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
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            code       TEXT UNIQUE NOT NULL,
            poster     TEXT,
            language   TEXT,
            genre      TEXT,
            status     TEXT DEFAULT 'now_showing',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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

# ─── BMS Mobile API Headers ────────────────────────────────────────────────────
# These mimic the BookMyShow Android app — not blocked by servers
MOBILE_HEADERS = {
    "User-Agent":      "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-IN",
    "appCode":         "MOBAND2",
    "appVersion":      "14310",
    "x-region-code":   "KOCHI",
    "x-region-slug":   "kochi",
    "Content-Type":    "application/json",
}

WEB_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer":         "https://in.bookmyshow.com/",
}

# ─── Fetch Movies via BMS APIs ─────────────────────────────────────────────────
REGION_CODES = ["KOCHI", "TVM", "ALPY", "KTYM", "TCR", "CALICUT", "KANN", "PKD", "MLM"]

async def fetch_movies_from_api(region: str, status: str) -> list:
    """Try multiple BMS API endpoints to get movie list"""
    movies = []

    endpoints = [
        # Mobile API — most reliable
        f"https://in.bookmyshow.com/api/explore/v1/get-movies-by-region?appCode=MOBAND2&appVersion=14310&regionCode={region}&language=en&status={'nowShowing' if status=='now_showing' else 'comingSoon'}",
        # Alternative mobile endpoint
        f"https://in.bookmyshow.com/serv/getData?cmd={'GETMOVIELIST' if status=='now_showing' else 'GETCOMINGSOON'}&region={region}&format=json",
        # Another endpoint
        f"https://in.bookmyshow.com/api/movies-data/movies-by-region?regionCode={region}&status={'nowShowing' if status=='now_showing' else 'comingSoon'}&appCode=MOBAND2",
    ]

    for endpoint in endpoints:
        try:
            headers = MOBILE_HEADERS.copy()
            headers["x-region-code"] = region
            async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
                resp = await client.get(endpoint)
                print(f"  API [{region}] {status}: {resp.status_code} → {endpoint[:60]}...")

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except:
                        continue

                    # Try different response structures
                    items = (
                        data.get("MovieData", {}).get("data", []) or
                        data.get("movieData", {}).get("data", []) or
                        data.get("BookMyShow", {}).get("arrEvents", []) or
                        data.get("arrEvents", []) or
                        data.get("data", []) or
                        data.get("movies", []) or
                        data.get("results", []) or
                        []
                    )

                    # Sometimes it's nested differently
                    if not items and isinstance(data, list):
                        items = data

                    for item in items:
                        name   = (item.get("EventTitle") or item.get("title") or
                                  item.get("name") or item.get("MovieTitle") or "").strip()
                        code   = (item.get("EventCode") or item.get("code") or
                                  item.get("id") or item.get("MovieCode") or "").strip()
                        poster = (item.get("EventImageUrl") or item.get("posterUrl") or
                                  item.get("poster") or item.get("imageUrl") or
                                  item.get("MovieImageUrl") or "").strip()
                        lang   = (item.get("EventLanguage") or item.get("language") or
                                  item.get("Languages") or "").strip()
                        genre  = (item.get("EventGenre") or item.get("genre") or
                                  item.get("Genre") or "").strip()

                        if name and code:
                            movies.append({
                                "name": name, "code": code, "poster": poster,
                                "language": lang, "genre": genre, "status": status
                            })

                    if movies:
                        print(f"  ✅ Got {len(movies)} movies from {region}/{status}")
                        return movies

        except Exception as e:
            print(f"  ❌ Error [{region}]: {e}")

    return movies

async def fetch_via_web_api(status: str) -> list:
    """Try web-based BMS APIs"""
    movies = []
    try:
        # This endpoint is used by BMS website's own JS
        url = f"https://in.bookmyshow.com/api/explore/v1/get-movies-by-category?appCode=WEB&categoryCode={'MT' if status=='now_showing' else 'MTCS'}&regionCode=KOCHI&language=en"
        async with httpx.AsyncClient(timeout=15, headers=WEB_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"  Web API [{status}]: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                items = (data.get("MovieData", {}).get("data", []) or
                         data.get("data", []) or [])
                for item in items:
                    name   = item.get("EventTitle", "").strip()
                    code   = item.get("EventCode", "").strip()
                    poster = item.get("EventImageUrl", "").strip()
                    lang   = item.get("EventLanguage", "")
                    genre  = item.get("EventGenre", "")
                    if name and code:
                        movies.append({"name": name, "code": code, "poster": poster,
                                      "language": lang, "genre": genre, "status": status})
    except Exception as e:
        print(f"  Web API error: {e}")
    return movies

async def refresh_movies():
    """Fetch all movies from BMS and save to DB"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === Refreshing movie list ===")
    all_movies = []

    # Try each region for now showing + coming soon
    for region in REGION_CODES[:4]:  # Start with main Kerala regions
        for status in ["now_showing", "coming_soon"]:
            movies = await fetch_movies_from_api(region, status)
            all_movies.extend(movies)
            if movies:
                break  # Got movies from this region, no need to try all
        await asyncio.sleep(0.5)

    # If still no movies, try web API
    if not all_movies:
        print("Mobile API got 0 movies, trying web API...")
        for status in ["now_showing", "coming_soon"]:
            movies = await fetch_via_web_api(status)
            all_movies.extend(movies)

    # Deduplicate by code
    seen, unique = set(), []
    for m in all_movies:
        if m["code"] not in seen:
            seen.add(m["code"])
            unique.append(m)

    print(f"Total unique movies: {len(unique)}")

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
        print(f"✅ Saved {len(unique)} movies to DB")
    else:
        print("⚠️ No movies fetched — BMS APIs may all be blocked from this server IP")

# ─── Theatre Search ─────────────────────────────────────────────────────────────
async def search_theatres_bms(city_code: str, movie_code: str):
    url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json&lat=0&lon=0&layoutId=5&ua=Desktop"
    try:
        async with httpx.AsyncClient(timeout=15, headers=MOBILE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"Theatre search [{city_code}]: {resp.status_code}")
            if resp.status_code == 200:
                data     = resp.json()
                venues   = data.get("BookMyShow", {}).get("arrShowDetails", [])
                theatres = []
                for v in venues[:25]:
                    name = v.get("ShowName", "")
                    area = v.get("ShowAddress", "")
                    if name:
                        theatres.append({
                            "name": name, "area": area, "code": v.get("ShowCode",""),
                            "maps_url": f"https://www.google.com/maps/search/?api=1&query={name.replace(' ','+')}+{area.replace(' ','+')}"
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
        async with httpx.AsyncClient(timeout=12, headers=MOBILE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data  = resp.json()
                shows = data.get("BookMyShow", {}).get("arrShowDetails", [])
                return len(shows) > 0
    except Exception as e:
        print(f"Booking check error: {e}")
    return False

# ─── Notifications ──────────────────────────────────────────────────────────────
def send_whatsapp(message: str):
    try:
        if not TWILIO_ACCOUNT_SID: return
        TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
            from_=TWILIO_WHATSAPP_FROM, to=f"whatsapp:{USER_WHATSAPP}", body=message)
        print("✅ WhatsApp sent!")
    except Exception as e:
        print(f"WhatsApp error: {e}")

def send_call(message: str):
    try:
        if not TWILIO_ACCOUNT_SID: return
        twiml = f"<Response><Say>{message}</Say><Say>Booking is now open. Go book your tickets now!</Say></Response>"
        TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).calls.create(
            from_=TWILIO_FROM_PHONE, to=USER_PHONE, twiml=twiml)
        print("✅ Call sent!")
    except Exception as e:
        print(f"Call error: {e}")

# ─── Background Tasks ───────────────────────────────────────────────────────────
async def movie_refresh_loop():
    while True:
        await refresh_movies()
        await asyncio.sleep(3600)

async def monitor_loop():
    print("Monitor loop started...")
    while True:
        try:
            conn     = get_db()
            monitors = conn.execute("SELECT * FROM monitors WHERE status='active' AND notified=0").fetchall()
            conn.close()
            for m in monitors:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking: {m['movie_name']} in {m['city_code']}")
                if await check_booking_open(m["movie_code"], m["city_code"]):
                    url = build_bms_url(m["movie_code"], m["city_code"], m["movie_name"])
                    conn = get_db()
                    conn.execute("UPDATE monitors SET notified=1,status='opened',booking_url=?,opened_at=? WHERE id=?",
                                 (url, datetime.now().isoformat(), m["id"]))
                    conn.execute("INSERT INTO logs (monitor_id,message) VALUES (?,?)",
                                 (m["id"], f"🎬 Booking opened! {m['movie_name']} → {url}"))
                    conn.commit(); conn.close()
                    msg = f"🎬 BOOKING OPEN!\n🎥 {m['movie_name']}\n🏙️ {m['city']}\n🎭 {m['theatre']}\n🔗 {url}"
                    send_whatsapp(msg)
                    send_call(f"Alert! Booking is now open for {m['movie_name']}!")
        except Exception as e:
            print(f"Monitor error: {e}")
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    t1 = asyncio.create_task(movie_refresh_loop())
    t2 = asyncio.create_task(monitor_loop())
    yield
    t1.cancel(); t2.cancel()

# ─── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="CineAlert v3", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MonitorCreate(BaseModel):
    movie_name: str; movie_code: str; movie_poster: Optional[str] = ""
    city: str; theatre: Optional[str] = ""; theatre_url: Optional[str] = ""

@app.get("/")
def root():
    conn  = get_db()
    count = conn.execute("SELECT COUNT(*) as c FROM movies").fetchone()["c"]
    conn.close()
    return {"status": "CineAlert v3 running!", "movies_in_db": count}

@app.get("/api/search/movies")
def api_search_movies(q: str):
    if len(q) < 2: return {"movies": []}
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM movies WHERE name LIKE ? ORDER BY status ASC, name ASC LIMIT 12",
        (f"%{q}%",)).fetchall()
    conn.close()
    return {"movies": [{"name":r["name"],"code":r["code"],"poster":r["poster"],
                        "lang":r["language"],"genre":r["genre"],"status":r["status"]} for r in rows]}

@app.get("/api/movies/all")
def api_all_movies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM movies ORDER BY name ASC").fetchall()
    conn.close()
    return {"movies": [dict(r) for r in rows], "total": len(rows)}

@app.get("/api/movies/refresh")
async def api_refresh_movies():
    asyncio.create_task(refresh_movies())
    return {"message": "Refresh started!"}

@app.get("/api/search/cities")
def api_cities(q: str = ""):
    if not q: return {"cities": []}
    return {"cities": search_kerala_cities(q)}

@app.get("/api/search/theatres")
async def api_search_theatres(city: str, movie_code: str):
    return {"theatres": await search_theatres_bms(get_city_code(city), movie_code)}

@app.post("/api/monitor")
def create_monitor(data: MonitorCreate):
    city_code = get_city_code(data.city)
    conn = get_db()
    if conn.execute("SELECT id FROM monitors WHERE movie_code=? AND city_code=? AND status='active'",
                    (data.movie_code, city_code)).fetchone():
        conn.close(); raise HTTPException(400, "Already monitoring this movie in this city!")
    cur = conn.execute(
        "INSERT INTO monitors (movie_name,movie_code,movie_poster,city,city_code,theatre,theatre_url) VALUES (?,?,?,?,?,?,?)",
        (data.movie_name,data.movie_code,data.movie_poster,data.city,city_code,data.theatre,data.theatre_url))
    conn.commit(); mid = cur.lastrowid; conn.close()
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
    conn.commit(); conn.close()
    return {"message": "Cancelled"}

@app.get("/api/logs")
def get_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}
