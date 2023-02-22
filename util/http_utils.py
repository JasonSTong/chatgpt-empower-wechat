import json

import jsonpath as jsonpath
import requests

from config.config import get_env, collection_get


class WeatherUtil:
    env = get_env()
    weather_config_key = 'QWEATHER_' + env
    location_path = collection_get(weather_config_key, 'LOCATION_PATH')
    weather_path = collection_get(weather_config_key, 'WEATHER_PATH')
    air_path = collection_get(weather_config_key, 'AIR_PATH')
    key = collection_get(weather_config_key, 'KEY')

    def get_weather_now(self, location_id: int):
        response = requests.get(self.weather_path, params={'location': location_id, 'key': self.key})
        if response.status_code == 200:
            data = response.text
            jsondata = json.loads(data)
            weather = jsondata['daily']
            return weather
        return None

    def get_air_now(self, location_id: int):
        response = requests.get(self.air_path, params={'location': location_id, 'key': self.key})
        if response.status_code == 200:
            data = response.text
            jsondata = json.loads(data)
            air = jsondata['daily']
            return air
        return None

    def create_weather_str(self, city_name: str, air, weather, day: str):
        weatherStr = f""
        if day == '今天':
            weatherStr = "今日 "
            weather = weather[0]
            air = air[0]
        elif day == '明天':
            weatherStr = "明天 "
            weather = weather[1]
            air = air[1]
        elif day == '后天':
            weatherStr = "后天 "
            weather = weather[2]
            air = air[2]
        if city_name is not None:
            weatherStr = weatherStr + f"{city_name} 天气：{weather['textDay']}\n" \
                                      f" ⬆️ 最高气温:{weather['tempMax']}°C\n" \
                                      f" ⬇️ 最低气温:{weather['tempMin']}°C\n" \
                                      f" 🌞 紫外线等级:{weather['uvIndex']}\n" \
                                      f" 🌪 最高风速:{weather['windScaleDay']}级\n" \
                                      f" 🌫 空气质量:{air['category']}\n" \
                                      f" 🔢 空气指数:{air['aqi']}"
        return weatherStr

    def get_weather_str(self, city_name: str, day: str):
        location_id = self.getLocationId(city_name)
        weather = self.get_weather_now(location_id)
        air = self.get_air_now(location_id)

        return self.create_weather_str(weather=weather, air=air, city_name=city_name, day=day)

    def getLocationId(self, city):
        response = requests.get(self.location_path, params={'location': city, 'key': self.key})
        if response.status_code == 200:
            return json.loads(response.text)['location'][0]['id']
