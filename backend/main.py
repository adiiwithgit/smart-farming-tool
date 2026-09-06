"""
Smart Farming Assistant - Backend
Field-deployable AI assistant: crop disease/pest/nutrient detection from
photos, weather-driven irrigation and climate-risk advisories, and a
trained soil health classifier from sensor readings.
"""

from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
print("TOKEN LOADED:", repr(os.environ.get("HF_API_TOKEN")))

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx

from models.vision_model import diagnose_disease, detect_pest, detect_nutrient_deficiency
from services.climate_rules import irrigation_advice, climate_risk_assessment
from services.soil_model_service import predict_soil_health

app = FastAPI(
    title="Smart Farming Assistant API",
    description="Disease/pest/nutrient detection, irrigation, climate-risk, and soil health",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IrrigationRequest(BaseModel):
    soil_moisture_pct: float
    lat: float
    lon: float


class ClimateRiskRequest(BaseModel):
    lat: float
    lon: float


class SoilHealthRequest(BaseModel):
    temperature: float
    humidity: float
    moisture: float
    rainfall: float


@app.get("/api/health")
def health_check():
    return {"status": "ok", "token_set": bool(os.environ.get("HF_API_TOKEN"))}


MAX_IMAGE_SIZE_MB = 8


async def _validate_and_read(image: UploadFile) -> bytes:
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Please upload a JPEG, PNG, or WEBP image.")
    data = await image.read()
    if len(data) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image too large — max {MAX_IMAGE_SIZE_MB}MB.")
    return data


@app.post("/api/diagnose/disease")
async def diagnose_disease_endpoint(image: UploadFile = File(...)):
    data = await _validate_and_read(image)
    return await diagnose_disease(data)


@app.post("/api/diagnose/pest")
async def diagnose_pest_endpoint(image: UploadFile = File(...)):
    data = await _validate_and_read(image)
    return await detect_pest(data)


@app.post("/api/diagnose/nutrient")
async def diagnose_nutrient_endpoint(image: UploadFile = File(...)):
    data = await _validate_and_read(image)
    return await detect_nutrient_deficiency(data)


async def _fetch_weather(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,precipitation"
        "&daily=precipitation_sum,temperature_2m_max"
        "&past_days=30&forecast_days=7&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


@app.get("/api/weather")
async def get_weather(lat: float = Query(...), lon: float = Query(...)):
    try:
        return await _fetch_weather(lat, lon)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Weather service unavailable: {e}")


@app.post("/api/irrigation-advice")
async def get_irrigation_advice(req: IrrigationRequest):
    try:
        weather = await _fetch_weather(req.lat, req.lon)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Weather service unavailable: {e}")

    current_temp = weather["current"]["temperature_2m"]
    daily = weather["daily"]
    precip_next_3d = sum(daily["precipitation_sum"][-7:-4] or daily["precipitation_sum"][:3])

    result = irrigation_advice(
        soil_moisture_pct=req.soil_moisture_pct,
        forecast_precip_mm_next_3d=round(precip_next_3d, 1),
        current_temp_c=current_temp,
    )
    return result


@app.post("/api/climate-risk")
async def get_climate_risk(req: ClimateRiskRequest):
    try:
        weather = await _fetch_weather(req.lat, req.lon)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Weather service unavailable: {e}")

    daily = weather["daily"]
    precip_series = daily["precipitation_sum"]
    temp_max_series = daily["temperature_2m_max"]

    past_precip = precip_series[:30]
    forecast_precip = precip_series[30:]
    forecast_temp_max = temp_max_series[30:]

    avg_precip_last_30d = sum(past_precip) / len(past_precip) if past_precip else 0
    total_precip_next_7d = sum(forecast_precip)
    max_temp_forecast = max(forecast_temp_max) if forecast_temp_max else weather["current"]["temperature_2m"]

    result = climate_risk_assessment(
        max_temp_forecast_c=round(max_temp_forecast, 1),
        total_precip_next_7d_mm=round(total_precip_next_7d, 1),
        avg_precip_last_30d_mm=round(avg_precip_last_30d, 1),
    )
    return result


@app.post("/api/soil-health")
def get_soil_health(req: SoilHealthRequest):
    return predict_soil_health(
        temperature=req.temperature,
        humidity=req.humidity,
        moisture=req.moisture,
        rainfall=req.rainfall,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)