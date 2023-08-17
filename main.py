import os
import asyncio

from flask.cli import load_dotenv
from wechaty import Wechaty,  WechatyOptions

from base import scheduler, bot
from handler.wechat.wechat_ai import WechatAI
from handler.wechat.wechaty_black_list_plugin import WechatyBlackListPlugin
from handler.wechat.wechaty_todo_plugin import WechatyTodoPoster
from handler.wechat.wechaty_weather_plugin import WechatyWeatherPoster


async def run():
    wechat_ai = WechatAI()
    bot.use(wechat_ai)\
        .use(WechatyWeatherPoster())\
        .use(WechatyTodoPoster())\
        .use(WechatyBlackListPlugin())

    scheduler.start()
    await bot.start()


if __name__ == '__main__':
    asyncio.run(run())
