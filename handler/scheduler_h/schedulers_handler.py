from typing import Union, Any

from wechaty import Contact, Room, Wechaty
from wechaty_puppet import ContactQueryFilter

from base import bot
from util import http_utils
from util.http_utils import WeatherUtil


async def sendWeather(conversation: Union[Contact, Room], city: str, day: str,name:str):
    weatherInfoStr = WeatherUtil().get_weather_str(city, day)
    if weatherInfoStr is not None:
        await conversation.say(weatherInfoStr)


async def sendTodo(conversation: Union[Contact, Room], todo: str):
    if todo is not None:
        await conversation.say(todo)


async def get_conversation(room_or_user: int, conv_id: str):

    conversation: Union[Any, Contact, Room]
    if room_or_user is 0:
        conversation = await bot.Room.find(conv_id)
        if conversation is not None:
            return conversation
    if conv_id is None:
        raise RuntimeError(f" user_id:{conv_id}不存在,查看是否过期.")
    conversation = await bot.Contact.find(conv_id)
    if conversation is None:
        raise RuntimeError(f"user_id:{conv_id}不存在,查看是否过期.")
    return conversation


async def scheduler_pusher(room_or_user: int, conv_id: str, func: Any, true_args:list):
    conversation = await get_conversation(room_or_user, conv_id)
    # true_args.pop(0)
    await func(conversation, *true_args)
