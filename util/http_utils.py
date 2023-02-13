import json

import jsonpath as jsonpath
import requests

from config.config import get_env, collection_get


class WeatherUtil:
    env = get_env()
    weather_config_key = 'QWEATHER_' + env
    location_path = collection_get(weather_config_key,'LOCATION-PATH')
    weather_path = collection_get(weather_config_key,'WEATHER-PATH')
    key = collection_get(weather_config_key,'KEY')


    def getWeatherNow(self, location_id: int):
        response = requests.get(self.weather_path, params={'location': location_id, 'key': self.key})
        if response.status_code == 200:
            data = response.text
            jsondata = json.loads(data)
            weather = jsondata['daily']
            return weather
        return None

    def createWeatherStr(self, city_name: str, weather: dict, day: str):
        weatherStr = f""
        if day == '今天':
            weatherStr = "今日 "
            weather = weather[0]
        elif day == '明天':
            weatherStr = "明天 "
            weather = weather[1]
        elif day == '后天':
            weatherStr = "后天 "
            weather = weather[2]
        if city_name is not None:
            weatherStr = weatherStr + f"{city_name} 天气：{weather['textDay']}\n" \
                                      f" ⬆️ 最高气温{weather['tempMax']}°C\n" \
                                      f" ⬇️ 最低气温{weather['tempMin']}°C\n" \
                                      f" 🌞 紫外线等级{weather['uvIndex']}\n" \
                                      f" 🌪 最高风速{weather['windScaleDay']}级"
        return weatherStr

    def getWeatherNowStr(self, city_name: str, day: str):
        location_id = self.getLocationId(city_name)
        weather = self.getWeatherNow(location_id)

        return self.createWeatherStr(weather=weather, city_name=city_name, day=day)

    def getLocationId(self, city):
        response = requests.get(self.location_path, params={'location': city, 'key': self.key})
        if response.status_code == 200:
            return json.loads(response.text)['location'][0]['id']
