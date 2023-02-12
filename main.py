import os
import asyncio

from flask.cli import load_dotenv
from wechaty import Wechaty,  WechatyOptions

from base import scheduler
from handler.wechat.wechat_ai import WechatAI
from handler.wechat.wechaty_todo_plugin import WechatyTodoPoster
from handler.wechat.wechaty_weather_plugin import WechatyWeatherPoster


async def run():
    """async run method"""
    load_dotenv()
    options = WechatyOptions(
        port=os.environ.get('port', 9001)
    )
    bot = Wechaty(options)
    wechat_ai = WechatAI()

    bot.use(wechat_ai).use(WechatyWeatherPoster()).use(WechatyTodoPoster())
    await bot.start()


if __name__ == '__main__':
    asyncio.run(run())
