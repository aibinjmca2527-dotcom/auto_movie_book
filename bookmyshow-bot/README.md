# 🎬 CineAlert — BookMyShow Auto Monitor
**Developed by Aibin Joseph**

Monitors BookMyShow every 30 seconds. When your movie's booking opens → sends WhatsApp message + phone call + shows "Book Now" button.

---

## 📁 Project Structure

```
bookmyshow-bot/
├── backend/
│   ├── main.py              ← FastAPI app + monitor logic
│   ├── requirements.txt     ← Python dependencies
│   ├── .env.example         ← Copy to .env and fill values
│   ├── Procfile             ← For Railway/Render deploy
│   └── railway.toml         ← Railway config
├── frontend/
│   ├── index.html           ← Main website
│   ├── css/style.css        ← Styling
│   └── js/app.js            ← All frontend logic
├── vercel.json              ← Vercel frontend deploy config
└── README.md
```

---

## 🚀 Deployment Guide

### Step 1 — Get Twilio (Free)
1. Go to https://www.twilio.com → Sign up free
2. Get your **Account SID**, **Auth Token**
3. Get a **Twilio phone number** (free trial)
4. Enable **WhatsApp Sandbox**: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
5. Send the join message from your WhatsApp to activate sandbox

### Step 2 — Deploy Backend on Railway (Free)
1. Go to https://railway.app → Sign up with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your repo, set **Root Directory** to `backend`
4. Go to **Variables** tab, add these:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
   TWILIO_FROM_PHONE=+1XXXXXXXXXX
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   USER_PHONE=+91XXXXXXXXXX
   USER_WHATSAPP=+91XXXXXXXXXX
   DB_PATH=bookmyshow.db
   ```
5. Railway will give you a URL like: `https://cinealert.up.railway.app`

### Step 3 — Update Frontend API URL
Open `frontend/js/app.js` line 3:
```js
: 'https://your-backend.railway.app'; // ← Replace with your Railway URL
```
Change to your actual Railway URL.

### Step 4 — Deploy Frontend on Vercel (Free)
1. Go to https://vercel.com → Sign up with GitHub
2. Click **Add New Project** → Import your repo
3. Set **Root Directory** to `frontend`
4. Click Deploy → Done!
5. Vercel gives you URL like: `https://cinealert.vercel.app`

---

## 💻 Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill .env with your values
uvicorn main:app --reload --port 8000

# Frontend
# Just open frontend/index.html in browser
# Or use Live Server in VS Code
```

---

## ✅ How It Works

1. Open your website (Vercel URL)
2. Type movie name → select from suggestions (with poster)
3. Type city → select
4. Type theatre → select → Google Maps opens to confirm location
5. Click **Start Monitoring**
6. Backend checks BookMyShow every **30 seconds**
7. When booking opens:
   - 📱 WhatsApp message sent to you
   - 📞 Phone call made to you
   - Website shows **"Book Now"** button → opens exact BMS page

---

## ⚠️ Notes

- Twilio free trial: 150 free minutes + WhatsApp sandbox (free)
- Railway free tier: $5 credit/month (enough for this app)
- Vercel frontend: completely free
- BookMyShow scraping: works on normal days; may need updates if BMS changes their API

---

*Developed by Aibin Joseph · CineAlert v1.0*
