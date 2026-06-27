from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3, httpx, asyncio, os, re, json
from datetime import datetime
from contextlib import asynccontextmanager
from twilio.rest import Client as TwilioClient
from theatres import get_theatres_for_city

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
    "ernakulam": "KOCHI", "kochi": "KOCHI", "cochin": "KOCHI",
    "aluva": "KOCHI", "angamaly": "KOCHI", "perumbavoor": "KOCHI",
    "muvattupuzha": "KOCHI", "kothamangalam": "KOCHI",
    "thrissur": "TCR", "trichur": "TCR", "irinjalakuda": "TCR",
    "chalakudy": "TCR", "guruvayur": "TCR", "kunnamkulam": "TCR",
    "palakkad": "PKD", "palghat": "PKD", "ottapalam": "PKD",
    "malappuram": "MLM", "manjeri": "MLM", "tirur": "MLM",
    "perinthalmanna": "MLM", "ponnani": "MLM", "nilambur": "MLM",
    "kozhikode": "CALICUT", "calicut": "CALICUT", "vatakara": "CALICUT",
    "wayanad": "WYD", "kalpetta": "WYD", "mananthavady": "WYD",
    "kannur": "KANN", "cannanore": "KANN", "thalassery": "KANN",
    "kasaragod": "KSD", "kanhangad": "KSD",
    "kayamkulam": "ALPY", "cherthala": "ALPY", "haripad": "ALPY",
    "mavelikkara": "ALPY", "ambalapuzha": "ALPY",
    "punalur": "KOLL", "karunagappally": "KOLL",
    "nedumangad": "TVM", "neyyattinkara": "TVM", "attingal": "TVM",
    "varkala": "TVM", "kazhakkoottam": "TVM",
    "adoor": "PTNA", "thiruvalla": "PTNA", "ranni": "PTNA",
    "kalamassery": "KOCHI", "tripunithura": "KOCHI",
    "edappally": "KOCHI", "kakkanad": "KOCHI",
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
    seen = set()
    for city, code in KERALA_CITIES.items():
        if q in city.lower() and city not in seen:
            seen.add(city)
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
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_name    TEXT NOT NULL,
            movie_code    TEXT NOT NULL,
            movie_poster  TEXT,
            city          TEXT NOT NULL,
            city_code     TEXT NOT NULL,
            theatre       TEXT,
            theatre_code  TEXT,
            theatre_url   TEXT,
            maps_url      TEXT,
            status        TEXT DEFAULT 'active',
            booking_url   TEXT,
            notified      INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            opened_at     TEXT
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
MOBILE_HEADERS = {
    "User-Agent":      "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-IN",
    "appCode":         "MOBAND2",
    "appVersion":      "14310",
    "Content-Type":    "application/json",
}

# ─── Booking Check ──────────────────────────────────────────────────────────────
def build_bms_url(movie_code: str, city_code: str, movie_name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', movie_name.lower()).strip('-')
    return f"https://in.bookmyshow.com/buytickets/{slug}/movie-{city_code.lower()}-{movie_code}-MT/"

async def check_booking_open(movie_code: str, city_code: str, theatre_name: str = "") -> dict:
    """
    Returns dict:
      found: bool
      theatre_found: bool (True if specific theatre is showing)
      all_theatres: list of theatre names showing the movie
    """
    try:
        url = (f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event"
               f"?appCode=MOBAND2&appVersion=14310&language=en"
               f"&eventCode={movie_code}&regionCode={city_code}"
               f"&subRegion={city_code}&format=json")
        async with httpx.AsyncClient(timeout=12, headers=MOBILE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data   = resp.json()
                shows  = data.get("BookMyShow", {}).get("arrShowDetails", [])
                if not shows:
                    return {"found": False, "theatre_found": False, "all_theatres": []}

                all_names = [s.get("ShowName", "") for s in shows]

                # If no specific theatre selected → any theatre is fine
                if not theatre_name:
                    return {"found": True, "theatre_found": True, "all_theatres": all_names}

                # Check if selected theatre is in the list
                theatre_found = any(
                    theatre_name.lower() in name.lower() or name.lower() in theatre_name.lower()
                    for name in all_names
                )
                return {"found": True, "theatre_found": theatre_found, "all_theatres": all_names}

    except Exception as e:
        print(f"Booking check error: {e}")
    return {"found": False, "theatre_found": False, "all_theatres": []}

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
        twiml = f"<Response><Say>{message}</Say></Response>"
        TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).calls.create(
            from_=TWILIO_FROM_PHONE, to=USER_PHONE, twiml=twiml)
        print("✅ Call sent!")
    except Exception as e:
        print(f"Call error: {e}")

# ─── Monitor Loop ───────────────────────────────────────────────────────────────
async def monitor_loop():
    print("✅ Monitor loop started — checking every 30 seconds")
    while True:
        try:
            conn     = get_db()
            monitors = conn.execute(
                "SELECT * FROM monitors WHERE status='active' AND notified=0"
            ).fetchall()
            conn.close()

            for m in monitors:
                mid          = m["id"]
                movie_name   = m["movie_name"]
                movie_code   = m["movie_code"]
                city_code    = m["city_code"]
                theatre_name = m["theatre"] or ""
                city         = m["city"]

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking: {movie_name} | {city} | Theatre: {theatre_name or 'Any'}")

                result = await check_booking_open(movie_code, city_code, theatre_name)

                # If specific theatre selected — wait only for that theatre
                if theatre_name:
                    if result["found"] and result["theatre_found"]:
                        # Selected theatre booking is open!
                        await notify_and_update(m, city_code, f"🎭 {theatre_name} booking open!")
                    elif result["found"] and not result["theatre_found"]:
                        # Other theatres open but not selected one yet
                        other = ", ".join(result["all_theatres"][:3])
                        print(f"  ℹ️ Booking open in other theatres ({other}) but NOT in {theatre_name} yet")
                        conn = get_db()
                        conn.execute("INSERT INTO logs (monitor_id, message) VALUES (?, ?)",
                            (mid, f"⏳ Booking open in other theatres but {theatre_name} not yet. Others: {other}"))
                        conn.commit()
                        conn.close()
                else:
                    # No theatre selected — notify when any theatre opens
                    if result["found"]:
                        theatres_str = ", ".join(result["all_theatres"][:3])
                        await notify_and_update(m, city_code, f"🎭 Now showing at: {theatres_str}")

        except Exception as e:
            print(f"Monitor loop error: {e}")
        await asyncio.sleep(30)

async def notify_and_update(m, city_code: str, theatre_msg: str):
    mid        = m["id"]
    movie_name = m["movie_name"]
    movie_code = m["movie_code"]
    city       = m["city"]
    theatre    = m["theatre"] or "Any Theatre"

    booking_url = build_bms_url(movie_code, city_code, movie_name)

    conn = get_db()
    conn.execute(
        "UPDATE monitors SET notified=1, status='opened', booking_url=?, opened_at=? WHERE id=?",
        (booking_url, datetime.now().isoformat(), mid)
    )
    conn.execute("INSERT INTO logs (monitor_id, message) VALUES (?, ?)",
        (mid, f"🎬 Booking opened! {movie_name} → {theatre_msg} → {booking_url}"))
    conn.commit()
    conn.close()

    msg = (
        f"🎬 BOOKING OPEN!\n"
        f"🎥 Movie: {movie_name}\n"
        f"🏙️ City: {city}\n"
        f"🎭 {theatre_msg}\n"
        f"🔗 Book Now: {booking_url}"
    )
    send_whatsapp(msg)
    send_call(f"Alert! Booking is now open for {movie_name} in {city}. Go book now!")
    print(f"✅ NOTIFIED: {movie_name} | {city}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(monitor_loop())
    yield
    task.cancel()

# ─── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(title="CineAlert v3", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MonitorCreate(BaseModel):
    movie_name:   str
    movie_code:   str
    movie_poster: Optional[str] = ""
    city:         str
    theatre:      Optional[str] = ""
    theatre_code: Optional[str] = ""
    theatre_url:  Optional[str] = ""
    maps_url:     Optional[str] = ""

class MovieAdd(BaseModel):
    name:     str
    code:     str
    poster:   Optional[str] = ""
    language: Optional[str] = ""
    genre:    Optional[str] = ""
    status:   Optional[str] = "now_showing"

# ─── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    conn  = get_db()
    count = conn.execute("SELECT COUNT(*) as c FROM movies").fetchone()["c"]
    mon   = conn.execute("SELECT COUNT(*) as c FROM monitors WHERE status='active'").fetchone()["c"]
    conn.close()
    return {"status": "CineAlert v3 running!", "movies_in_db": count, "active_monitors": mon}

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

@app.get("/api/search/cities")
def api_cities(q: str = ""):
    if not q: return {"cities": []}
    return {"cities": search_kerala_cities(q)}

@app.get("/api/search/theatres")
def api_search_theatres(city: str, q: str = ""):
    """Return theatres from local hardcoded data — always accurate, never blocked"""
    city_code = get_city_code(city)
    theatres  = get_theatres_for_city(city_code)
    if q:
        theatres = [t for t in theatres if q.lower() in t["name"].lower()]
    return {"theatres": theatres, "total": len(theatres)}

@app.post("/api/movies/add")
def add_movie_manual(data: MovieAdd):
    if not data.name or not data.code:
        raise HTTPException(400, "Movie name and code required!")
    conn = get_db()
    conn.execute("""
        INSERT INTO movies (name, code, poster, language, genre, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(code) DO UPDATE SET
            name=excluded.name, poster=excluded.poster,
            language=excluded.language, genre=excluded.genre,
            status=excluded.status, updated_at=excluded.updated_at
    """, (data.name.strip(), data.code.strip().upper(), data.poster,
          data.language, data.genre, data.status, datetime.now().isoformat()))
    conn.commit()
    count = conn.execute("SELECT COUNT(*) as c FROM movies").fetchone()["c"]
    conn.close()
    return {"message": f"✅ '{data.name}' added!", "total": count}

@app.get("/api/movies/list")
def list_movies():
    conn = get_db()
    rows = conn.execute("SELECT * FROM movies ORDER BY updated_at DESC").fetchall()
    conn.close()
    return {"movies": [dict(r) for r in rows], "total": len(rows)}

@app.delete("/api/movies/{code}")
def delete_movie(code: str):
    conn = get_db()
    conn.execute("DELETE FROM movies WHERE code=?", (code.upper(),))
    conn.commit(); conn.close()
    return {"message": "Deleted"}

@app.post("/api/monitor")
def create_monitor(data: MonitorCreate):
    city_code = get_city_code(data.city)
    conn = get_db()
    if conn.execute(
        "SELECT id FROM monitors WHERE movie_code=? AND city_code=? AND status='active'",
        (data.movie_code, city_code)).fetchone():
        conn.close()
        raise HTTPException(400, "Already monitoring this movie in this city!")
    cur = conn.execute("""
        INSERT INTO monitors
        (movie_name,movie_code,movie_poster,city,city_code,theatre,theatre_code,theatre_url,maps_url)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (data.movie_name, data.movie_code, data.movie_poster, data.city, city_code,
         data.theatre, data.theatre_code, data.theatre_url, data.maps_url))
    conn.commit(); mid = cur.lastrowid; conn.close()
    return {"id": mid, "message": f"✅ Monitoring {data.movie_name} in {data.city}!"}

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
