import requests

# wttr.in 免费天气 API：https://github.com/chubin/wttr.in
API_URL = "https://wttr.in/{city}?format=j1"


def fetch_weather(city: str = "北京") -> dict:
    """获取指定城市今日天气"""
    try:
        resp = requests.get(API_URL.format(city=city), timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; DailyEmailBot/1.0)"
        })
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_condition", [{}])[0]
        weather_info = data.get("weather", [{}])[0]

        return {
            "city": city,
            "date": weather_info.get("date", ""),
            "temp_min": weather_info.get("mintempC", ""),
            "temp_max": weather_info.get("maxtempC", ""),
            "temp_current": current.get("temp_C", ""),
            "humidity": current.get("humidity", ""),
            "weather_desc": current.get("weatherDesc", [{}])[0].get("value", ""),
            "wind_speed": current.get("windspeedKmph", ""),
            "wind_dir": current.get("winddir16Point", ""),
            "success": True,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "city": city}
