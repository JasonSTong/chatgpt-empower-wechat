from typing import Union

from wechaty import Contact, Room

from util import http_utils
from util.http_utils import WeatherUtil


async def sendWeather(conversation: Union[Contact, Room],city:str):
    weatherInfoStr = WeatherUtil().getWeatherNowStr(city,0)
    if weatherInfoStr is not None:
        await conversation.say(weatherInfoStr)
