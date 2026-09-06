# Smart Farming Assistant

Field-deployable AI assistant for early crop disease/pest/nutrient detection
and climate-risk resilience (drought, flood, heatwave), built for Indian
farmers. FastAPI backend, plain HTML/CSS/JS frontend.

## Project structure

```
smart-farming-assistant/
├── backend/
│   ├── main.py                    ← FastAPI app, all routes
│   ├── requirements.txt
│   ├── .env.example               ← copy to .env, add your HF token
│   ├── models/
│   │   └── vision_model.py        ← disease (LIVE) + pest/nutrient (STUBS, swap in later)
│   └── services/
│       └── climate_rules.py       ← irrigation + climate-risk logic (weather-driven)
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

## What's live today vs. what's a placeholder

| Feature | Status | How |
|---|---|---|
| Disease detection | **Live** | Calls a free, pre-trained plant disease model (MobileNetV2 on PlantVillage) hosted on Hugging Face's Inference API |
| Pest detection | Placeholder | Returns a clear "not implemented" response + generic tip. Swap in your teammate's model when ready. |
| Nutrient deficiency | Placeholder | Same pattern as pest detection. |
| Irrigation advisor | **Live** | Rule-based on real-time weather (soil moisture you enter + live rainfall/temp forecast) |
| Climate risk (drought/flood/heatwave) | **Live** | Rule-based on 30-day historical + 7-day forecast weather data |

Why disease detection uses a hosted API instead of running a model locally:
Render's free tier gives ~512MB RAM. Loading PyTorch + a vision model locally
would blow past that. Calling Hugging Face's hosted inference endpoint keeps
our backend lightweight (`httpx` sending image bytes over HTTP) and still
gives you real AI predictions today.

## Setting up the Hugging Face token (needed for disease detection)

1. Create a free account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens → create a token (read access is enough)
3. In `backend/`, copy `.env.example` to `.env` and paste your token in:
   ```
   HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```
4. Do the same as an environment variable in Render when you deploy (Section below)

Note: Hugging Face's free Inference API can "cold start" — the first request
to a model that hasn't been called recently may return a 503 while it loads
(the app handles this and tells you to retry in ~20 seconds). Calling it once
a few minutes before your demo warms it up.

## Running it in VS Code

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
python main.py
```
Runs at `http://localhost:8000`. Check `http://localhost:8000/api/health`,
and see interactive docs at `http://localhost:8000/docs`.

### 2. Frontend
Right-click `frontend/index.html` → **Open with Live Server** (VS Code extension).
It's pointed at `http://localhost:8000` by default — edit `API_BASE` in
`script.js` if your backend runs elsewhere.

## Where your teammate's model plugs in

Open `backend/models/vision_model.py`. `detect_pest()` and
`detect_nutrient_deficiency()` currently return placeholder responses.
There are two ways to wire in the real model, matching how your teammate
finishes it:

- **They also host it on Hugging Face** → just point a new `HF_MODEL_*` +
  `HF_API_URL` at their model, same pattern as `diagnose_disease()`.
- **They hand you a model file** (`.pt`, `.h5`, `.onnx`, etc.) → write a new
  function that loads it once at startup and runs inference locally, keeping
  the same input (`image_bytes: bytes`) and output shape
  (`{"status", "label", "confidence", "tip"}`) so `main.py` doesn't change.

## Deploying

### Backend → Render
1. Push this repo to GitHub
2. Render dashboard → New → Web Service → connect your repo
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `HF_API_TOKEN` = your token
7. Free tier will "spin down" after inactivity — first request after idle
   takes ~30-60 seconds to wake up. Worth mentioning to judges if it happens live.

### Frontend → Netlify (recommended)
Netlify over Vercel here mainly because drag-and-drop deploy needs zero config
for a plain HTML/CSS/JS site with no build step — you literally drag the
`frontend` folder onto their dashboard and get a live URL in seconds. Vercel
works too if your team already uses it, but Netlify's free tier is the path
of least resistance for a static site under time pressure.

1. Go to https://app.netlify.com → log in (free)
2. Drag the `frontend` folder onto the "Deploy manually" area, OR connect
   your GitHub repo and set publish directory to `frontend`
3. Once deployed, open `frontend/script.js`, change `API_BASE` to your Render
   backend URL (e.g. `https://your-app.onrender.com`), redeploy

## Git setup
```bash
git init
git add .
git commit -m "Smart Farming Assistant: disease/pest/nutrient + climate risk"
```
