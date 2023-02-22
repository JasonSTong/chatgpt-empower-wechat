from typing import Union

from wechaty import Contact, Room
from wechaty_puppet import ContactQueryFilter

from util import http_utils
from util.http_utils import WeatherUtil


async def sendWeather(conversation: Union[Contact, Room], city: str, day: str,name:str):
    weatherInfoStr = WeatherUtil().get_weather_str(city, day)
    if weatherInfoStr is not None:
        await conversation.say(weatherInfoStr)


async def sendTodo(conversation: Union[Contact, Room], todo: str):
    if todo is not None:
        await conversation.say(todo)
