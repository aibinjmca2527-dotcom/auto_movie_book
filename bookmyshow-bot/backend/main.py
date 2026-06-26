from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import httpx
import asyncio
import os
import re
from datetime import datetime
from contextlib import asynccontextmanager
from twilio.rest import Client as TwilioClient

# ─── Twilio Config ─────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_PHONE    = os.getenv("TWILIO_FROM_PHONE", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_PHONE           = os.getenv("USER_PHONE", "")
USER_WHATSAPP        = os.getenv("USER_WHATSAPP", "")
DB_PATH              = os.getenv("DB_PATH", "bookmyshow.db")

# ─── Kerala Cities & Districts ─────────────────────────────────────────────────
KERALA_CITIES = {
    # Major cities / districts
    "thiruvananthapuram": "TVM",
    "trivandrum":         "TVM",
    "kollam":             "KOLL",
    "pathanamthitta":     "PTNA",
    "alappuzha":          "ALPY",
    "alapuzha":           "ALPY",
    "alleppey":           "ALPY",
    "kottayam":           "KTYM",
    "idukki":             "IDK",
    "ernakulam":          "ERNAKULAM",
    "kochi":              "KOCHI",
    "cochin":             "KOCHI",
    "thrissur":           "TCR",
    "trichur":            "TCR",
    "palakkad":           "PKD",
    "palghat":            "PKD",
    "malappuram":         "MLM",
    "kozhikode":          "CALICUT",
    "calicut":            "CALICUT",
    "wayanad":            "WYD",
    "kannur":             "KANN",
    "cannanore":          "KANN",
    "kasaragod":          "KSD",
    # Towns & sub-districts
    "changanassery":      "KTYM",
    "changanacherry":     "KTYM",
    "pala":               "KTYM",
    "ettumanoor":         "KTYM",
    "vaikom":             "KTYM",
    "kayamkulam":         "ALPY",
    "cherthala":          "ALPY",
    "ambalapuzha":        "ALPY",
    "haripad":            "ALPY",
    "mavelikkara":        "ALPY",
    "punalur":            "KOLL",
    "karunagappally":     "KOLL",
    "nedumangad":         "TVM",
    "neyyattinkara":      "TVM",
    "attingal":           "TVM",
    "varkala":            "TVM",
    "adoor":              "PTNA",
    "thiruvalla":         "PTNA",
    "ranni":              "PTNA",
    "thodupuzha":         "IDK",
    "kothamangalam":      "ERNAKULAM",
    "muvattupuzha":       "ERNAKULAM",
    "aluva":              "ERNAKULAM",
    "angamaly":           "ERNAKULAM",
    "perumbavoor":        "ERNAKULAM",
    "north paravur":      "ERNAKULAM",
    "irinjalakuda":       "TCR",
    "chalakudy":          "TCR",
    "guruvayur":          "TCR",
    "kunnamkulam":        "TCR",
    "ottapalam":          "PKD",
    "shoranur":           "PKD",
    "mannarkkad":         "PKD",
    "tirur":              "MLM",
    "perinthalmanna":     "MLM",
    "ponnani":            "MLM",
    "manjeri":            "MLM",
    "kalpetta":           "WYD",
    "mananthavady":       "WYD",
    "sulthan bathery":    "WYD",
    "thalassery":         "KANN",
    "payyannur":          "KANN",
    "iritty":             "KANN",
    "kanhangad":          "KSD",
    "hosdurg":            "KSD",
    "vatakara":           "CALICUT",
    "feroke":             "CALICUT",
    "koduvally":          "CALICUT",
    "perambra":           "CALICUT",
    "payyanur":           "KANN",
    "nilambur":           "MLM",
    "tiruvambadi":        "CALICUT",
    "wandoor":            "MLM",
    "thrithala":          "PKD",
    "chittur":            "PKD",
    "nemmara":            "PKD",
    "parappanangadi":     "MLM",
    "kondotty":           "MLM",
    "tanur":              "MLM",
    "pandikkad":          "MLM",
    "edappal":            "MLM",
    "angadipuram":        "MLM",
    "cherpulassery":      "PKD",
    "shornur":            "PKD",
    "palakkad city":      "PKD",
    "kunnamangalam":      "CALICUT",
    "mukkam":             "CALICUT",
    "balussery":          "CALICUT",
    "ramanattukara":      "CALICUT",
    "chavakkad":          "TCR",
    "kodungallur":        "TCR",
    "mala":               "TCR",
    "thrissur city":      "TCR",
    "wadakkanchery":      "TCR",
    "chelakkara":         "TCR",
    "ollur":              "TCR",
    "puthukad":           "TCR",
    "kalamassery":        "ERNAKULAM",
    "tripunithura":       "ERNAKULAM",
    "edappally":          "ERNAKULAM",
    "kakkanad":           "ERNAKULAM",
    "fort kochi":         "KOCHI",
    "mattancherry":       "KOCHI",
    "ernakulam city":     "KOCHI",
    "palarivattom":       "KOCHI",
    "thampanoor":         "TVM",
    "pattom":             "TVM",
    "kowdiar":            "TVM",
    "medical college":    "TVM",
    "kesavadasapuram":    "TVM",
    "kazhakkoottam":      "TVM",
    "technopark":         "TVM",
    "vellayambalam":      "TVM",
    "sreekaryam":         "TVM",
    "menamkulam":         "TVM",
    "karyavattom":        "TVM",
    "ulloor":             "TVM",
    "peroorkada":         "TVM",
    "thirumala":          "TVM",
    "poonthura":          "TVM",
    "vizhinjam":          "TVM",
    "kovalam":            "TVM",
    "pothencode":         "TVM",
    "palode":             "TVM",
    "aruvikkara":         "TVM",
    "kilimanoor":         "TVM",
    "chirayinkeezhu":     "TVM",
    "parassala":          "TVM",
    "vellanad":           "TVM",
    "maranalloor":        "TVM",
    "kallambalam":        "TVM",
    "venjaramoodu":       "TVM",
    "balaramapuram":      "TVM",
    "navaikulam":         "TVM",
    "karickom":           "TVM",
    "mangalapuram":       "TVM",
}

def search_kerala_cities(q: str):
    q = q.lower().strip()
    results = []
    seen_codes = set()
    for city, code in KERALA_CITIES.items():
        if q in city.lower():
            if code not in seen_codes:
                seen_codes.add(code)
                results.append({"name": city.title(), "code": code})
            else:
                # add alternate name too
                results.append({"name": city.title(), "code": code})
    # Sort: exact start matches first
    results.sort(key=lambda x: (not x["name"].lower().startswith(q), x["name"]))
    return results[:15]

# ─── DB ────────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9,ml;q=0.8",
    "Referer": "https://in.bookmyshow.com/",
    "Origin": "https://in.bookmyshow.com",
    "x-region-code": "KOCHI",
    "x-region-slug": "kochi",
    "x-app-code": "WEB",
}

# ─── Movie Search ───────────────────────────────────────────────────────────────
async def search_movies_bms(query: str):
    urls_to_try = [
        f"https://in.bookmyshow.com/api/explore/v1/search?q={query}&type=MT&region=KOCHI",
        f"https://in.bookmyshow.com/api/explore/v1/search?q={query}&type=MT",
        f"https://in.bookmyshow.com/serv/getData?cmd=QUICKSEARCH&q={query}&type=MT&region=KOCHI",
    ]
    for url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
                resp = await client.get(url)
                print(f"Movie search URL: {url} → {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    movies = []
                    # Try different response structures
                    items = (
                        data.get("MovieData", {}).get("data", []) or
                        data.get("movieData", {}).get("data", []) or
                        data.get("result", {}).get("data", []) or
                        data.get("data", []) or
                        []
                    )
                    for item in items[:10]:
                        name = (item.get("EventTitle") or item.get("title") or item.get("name") or "").strip()
                        code = (item.get("EventCode") or item.get("code") or item.get("id") or "").strip()
                        poster = (item.get("EventImageUrl") or item.get("poster") or item.get("image") or "").strip()
                        lang = (item.get("EventLanguage") or item.get("language") or "").strip()
                        genre = (item.get("EventGenre") or item.get("genre") or "").strip()
                        if name and code:
                            movies.append({"name": name, "code": code, "poster": poster, "lang": lang, "genre": genre})
                    if movies:
                        return movies
        except Exception as e:
            print(f"Movie search error ({url}): {e}")
    return []

# ─── Theatre Search ─────────────────────────────────────────────────────────────
async def search_theatres_bms(city_code: str, movie_code: str):
    urls_to_try = [
        f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json&lat=0&lon=0&layoutId=5&ua=Desktop",
        f"https://in.bookmyshow.com/serv/getData?cmd=GETSHOWTIMES&code={movie_code}&region={city_code}&format=json",
    ]
    for url in urls_to_try:
        try:
            async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
                resp = await client.get(url)
                print(f"Theatre search: {url} → {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    theatres = []
                    venues = data.get("BookMyShow", {}).get("arrShowDetails", []) or data.get("arrShowDetails", []) or []
                    for venue in venues[:20]:
                        name = venue.get("ShowName", "") or venue.get("VenueName", "")
                        area = venue.get("ShowAddress", "") or venue.get("VenueAddress", "")
                        code = venue.get("ShowCode", "") or venue.get("VenueCode", "")
                        if name:
                            theatres.append({
                                "name": name,
                                "area": area,
                                "code": code,
                                "maps_url": f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}+{area.replace(' ', '+')}"
                            })
                    if theatres:
                        return theatres
        except Exception as e:
            print(f"Theatre search error: {e}")
    return []

def get_city_code(city: str) -> str:
    c = city.lower().strip()
    return KERALA_CITIES.get(c, city.upper())

def build_bms_url(movie_code: str, city_code: str, movie_name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', movie_name.lower()).strip('-')
    return f"https://in.bookmyshow.com/buytickets/{slug}/movie-{city_code.lower()}-{movie_code}-MT/"

async def check_booking_open(movie_code: str, city_code: str) -> bool:
    try:
        url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json"
        async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                shows = data.get("BookMyShow", {}).get("arrShowDetails", [])
                return len(shows) > 0
    except Exception as e:
        print(f"Check booking error: {e}")
    return False

# ─── Notifications ──────────────────────────────────────────────────────────────
def send_whatsapp(message: str):
    try:
        if not TWILIO_ACCOUNT_SID:
            print("Twilio not configured")
            return
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=f"whatsapp:{USER_WHATSAPP}", body=message)
        print("WhatsApp sent!")
    except Exception as e:
        print(f"WhatsApp error: {e}")

def send_call(message: str):
    try:
        if not TWILIO_ACCOUNT_SID:
            print("Twilio not configured")
            return
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twiml = f"<Response><Say>{message}</Say><Say>Booking is now open. Go book your tickets now!</Say></Response>"
        client.calls.create(from_=TWILIO_FROM_PHONE, to=USER_PHONE, twiml=twiml)
        print("Call sent!")
    except Exception as e:
        print(f"Call error: {e}")

# ─── Monitor Loop ───────────────────────────────────────────────────────────────
async def monitor_loop():
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
                        (mid, f"Booking opened! URL: {booking_url}"))
                    conn.commit()
                    conn.close()
                    msg = (f"🎬 BOOKING OPEN! {movie_name}\n🏙️ City: {city_code}\n"
                           f"🎭 Theatre: {theatre}\n🔗 Book now: {booking_url}")
                    send_whatsapp(msg)
                    send_call(f"Alert! Booking is now open for {movie_name}.")
                    print(f"NOTIFIED for {movie_name}!")
        except Exception as e:
            print(f"Monitor loop error: {e}")
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(monitor_loop())
    yield
    task.cancel()

# ─── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="CineAlert API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MonitorCreate(BaseModel):
    movie_name:   str
    movie_code:   str
    movie_poster: Optional[str] = ""
    city:         str
    theatre:      Optional[str] = ""
    theatre_url:  Optional[str] = ""

@app.get("/")
def root():
    return {"status": "CineAlert API running!"}

@app.get("/api/search/movies")
async def api_search_movies(q: str):
    if len(q) < 2:
        return {"movies": []}
    movies = await search_movies_bms(q)
    return {"movies": movies}

@app.get("/api/search/cities")
def api_cities(q: str = ""):
    if not q:
        return {"cities": []}
    results = search_kerala_cities(q)
    return {"cities": results}

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
        (data.movie_name, data.movie_code, data.movie_poster, data.city, city_code, data.theatre, data.theatre_url)
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return {"id": mid, "message": f"Now monitoring {data.movie_name} in {data.city}!"}

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
    return {"message": "Monitor cancelled"}

@app.get("/api/monitor/{mid}/status")
def monitor_status(mid: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM monitors WHERE id=?", (mid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)

@app.get("/api/logs")
def get_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}
