import requests
import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

env_loc = find_dotenv()
load_dotenv(env_loc)
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def format_time(ts, tz_offset):
    return datetime.utcfromtimestamp(ts + tz_offset).strftime('%I:%M %p')

def get_day_name(ts):
    return datetime.utcfromtimestamp(ts).strftime('%A')

def get_weather(city_name):
    if not API_KEY: return {"error": "API Key missing"}
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200: return {"error": data.get("message")}

        # --- THIS PART IS CRITICAL ---
        # We ensure all keys exist to prevent errors in app.py
        return {
            "city": data["name"],
            "temp": round(data["main"]["temp"], 1),
            "condition": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "visibility": data.get("visibility", 10000) / 1000, # Convert to KM
            "pressure": data["main"]["pressure"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "sunrise": format_time(data["sys"]["sunrise"], data["timezone"]),
            "sunset": format_time(data["sys"]["sunset"], data["timezone"])
        }
    except Exception as e:
        return {"error": str(e)}

def get_forecast(city_name):
    if not API_KEY: return [], []
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        
        chart_data = []
        for entry in data['list'][:9]:
            chart_data.append({"time": entry['dt_txt'], "temp": entry['main']['temp']})
            
        daily_data = []
        seen_days = set()
        for entry in data['list']:
            day = get_day_name(entry['dt'])
            if day not in seen_days and len(daily_data) < 7:
                daily_data.append({
                    "day": day,
                    "temp": round(entry['main']['temp']),
                    "icon": entry['weather'][0]['icon']
                })
                seen_days.add(day)

        return chart_data, daily_data
    except:
        return [], []

def get_aqi(lat, lon):
    if not API_KEY: return {"val": 0, "comp": {}}
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        data = requests.get(url).json()
        return {
            "val": data['list'][0]['main']['aqi'],
            "comp": data['list'][0]['components']
        }
    except:
        return {"val": 0, "comp": {}}