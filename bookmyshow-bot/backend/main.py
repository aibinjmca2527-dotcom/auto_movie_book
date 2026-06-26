from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import httpx
import asyncio
import json
import os
import re
import time
from datetime import datetime
from contextlib import asynccontextmanager
from twilio.rest import Client as TwilioClient

# ─── Twilio Config ─────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_PHONE  = os.getenv("TWILIO_FROM_PHONE", "")   # e.g. +1415XXXXXXX
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_PHONE         = os.getenv("USER_PHONE", "")           # e.g. +919XXXXXXXXX
USER_WHATSAPP      = os.getenv("USER_WHATSAPP", "")        # e.g. +919XXXXXXXXX

# ─── DB Setup ──────────────────────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "bookmyshow.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monitors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_name  TEXT NOT NULL,
            movie_code  TEXT NOT NULL,
            movie_poster TEXT,
            city        TEXT NOT NULL,
            city_code   TEXT NOT NULL,
            theatre     TEXT,
            theatre_url TEXT,
            status      TEXT DEFAULT 'active',
            booking_url TEXT,
            notified    INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            opened_at   TEXT
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

# ─── BMS Scraper ───────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
}

async def search_movies(query: str):
    """Search movies from BookMyShow"""
    try:
        url = f"https://in.bookmyshow.com/api/explore/v1/search?q={query}&type=MT"
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                movies = []
                items = data.get("MovieData", {}).get("data", [])
                for item in items[:8]:
                    movies.append({
                        "name":   item.get("EventTitle", ""),
                        "code":   item.get("EventCode", ""),
                        "poster": item.get("EventImageUrl", ""),
                        "lang":   item.get("EventLanguage", ""),
                        "genre":  item.get("EventGenre", ""),
                    })
                return movies
    except Exception as e:
        print(f"Movie search error: {e}")
    return []

async def search_theatres(city_code: str, movie_code: str):
    """Get theatres for a movie in a city"""
    try:
        url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json&lat=0&lon=0&layoutId=5&ua=Desktop"
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                theatres = []
                venues = data.get("BookMyShow", {}).get("arrShowDetails", [])
                for venue in venues[:15]:
                    name = venue.get("ShowName", "")
                    area = venue.get("ShowAddress", "")
                    code = venue.get("ShowCode", "")
                    theatres.append({
                        "name": name,
                        "area": area,
                        "code": code,
                        "maps_url": f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}+{area.replace(' ', '+')}"
                    })
                return theatres
    except Exception as e:
        print(f"Theatre search error: {e}")
    return []

CITY_MAP = {
    "mumbai": "MUMBAI", "delhi": "NCR", "bangalore": "BANG", "chennai": "CHEN",
    "hyderabad": "HYD", "kolkata": "KOLKATA", "pune": "PUNE", "ahmedabad": "ABAD",
    "kochi": "KOCHI", "thiruvananthapuram": "TVM", "kozhikode": "CALICUT",
    "thrissur": "TCR", "jaipur": "JAIPUR", "lucknow": "LKO", "surat": "SURAT",
    "nagpur": "NAGPUR", "indore": "INDORE", "bhopal": "BHOPAL", "patna": "PATNA",
    "chandigarh": "CHANDI", "goa": "GOA", "vizag": "VIZAG", "coimbatore": "COIMB",
    "madurai": "MADURAI", "mysore": "MYSORE", "mangalore": "MANG",
}

def get_city_code(city: str) -> str:
    return CITY_MAP.get(city.lower().strip(), city.upper())

def build_bms_url(movie_code: str, city_code: str, movie_name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', movie_name.lower()).strip('-')
    return f"https://in.bookmyshow.com/buytickets/{slug}/movie-{city_code.lower()}-{movie_code}-MT/"

async def check_booking_open(movie_code: str, city_code: str) -> bool:
    """Check if booking is open for this movie"""
    try:
        url = f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14310&language=en&eventCode={movie_code}&regionCode={city_code}&subRegion={city_code}&format=json"
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                shows = data.get("BookMyShow", {}).get("arrShowDetails", [])
                return len(shows) > 0
    except Exception as e:
        print(f"Check booking error: {e}")
    return False

# ─── Notifications ─────────────────────────────────────────────────────────────
def send_whatsapp(message: str):
    try:
        if not TWILIO_ACCOUNT_SID:
            print("Twilio not configured")
            return
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{USER_WHATSAPP}",
            body=message
        )
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
        client.calls.create(
            from_=TWILIO_FROM_PHONE,
            to=USER_PHONE,
            twiml=twiml
        )
        print("Call sent!")
    except Exception as e:
        print(f"Call error: {e}")

# ─── Background Monitor ────────────────────────────────────────────────────────
monitoring_task = None

async def monitor_loop():
    print("Monitor loop started...")
    while True:
        try:
            conn = get_db()
            monitors = conn.execute(
                "SELECT * FROM monitors WHERE status='active' AND notified=0"
            ).fetchall()
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
                    conn.execute(
                        "INSERT INTO logs (monitor_id, message) VALUES (?, ?)",
                        (mid, f"Booking opened! URL: {booking_url}")
                    )
                    conn.commit()
                    conn.close()

                    msg = (
                        f"🎬 BOOKING OPEN! {movie_name}\n"
                        f"🏙️ City: {city_code}\n"
                        f"🎭 Theatre: {theatre}\n"
                        f"🔗 Book now: {booking_url}"
                    )
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

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="BookMyShow Auto Booker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ────────────────────────────────────────────────────────────────────
class MonitorCreate(BaseModel):
    movie_name:   str
    movie_code:   str
    movie_poster: Optional[str] = ""
    city:         str
    theatre:      Optional[str] = ""
    theatre_url:  Optional[str] = ""

# ─── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "BookMyShow Auto Booker API is running!"}

@app.get("/api/search/movies")
async def api_search_movies(q: str):
    if len(q) < 2:
        return {"movies": []}
    movies = await search_movies(q)
    return {"movies": movies}

@app.get("/api/search/cities")
def api_cities(q: str = ""):
    cities = list(CITY_MAP.keys())
    if q:
        cities = [c for c in cities if q.lower() in c.lower()]
    return {"cities": [{"name": c.title(), "code": CITY_MAP[c]} for c in cities]}

@app.get("/api/search/theatres")
async def api_search_theatres(city: str, movie_code: str):
    city_code = get_city_code(city)
    theatres = await search_theatres(city_code, movie_code)
    return {"theatres": theatres}

@app.post("/api/monitor")
def create_monitor(data: MonitorCreate):
    city_code = get_city_code(data.city)
    conn = get_db()
    # Check if already monitoring same movie+city
    existing = conn.execute(
        "SELECT id FROM monitors WHERE movie_code=? AND city_code=? AND status='active'",
        (data.movie_code, city_code)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Already monitoring this movie in this city!")

    cur = conn.execute(
        """INSERT INTO monitors (movie_name, movie_code, movie_poster, city, city_code, theatre, theatre_url)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data.movie_name, data.movie_code, data.movie_poster, data.city, city_code,
         data.theatre, data.theatre_url)
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
        raise HTTPException(404, "Monitor not found")
    return dict(row)

@app.get("/api/logs")
def get_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}
