import uuid

from wechaty import WechatyPlugin, Wechaty, Message

from base import redis
from util.uuid_util import getUUIDWithoutLine


class WechatBindToTelegram(WechatyPlugin):

    def __init__(self):
        super().__init__()

    async def init_plugin(self, wechaty: Wechaty) -> None:
        await super().init_plugin(wechaty)

    async def on_message(self, msg: Message) -> None:
        room = msg.room()
        if room is not None:
            return
        msg_text = msg.text()
        name = msg.talker().name
        id = msg.talker().get_id()
        if msg_text.find('#bind tg') < -1:
            return
        uuid: str = getUUIDWithoutLine()[4:16]
        user_key = msg_text.split("#bind tg")[1]
        # 存储绑定秘钥m
        redis.set(uuid+user_key+"name", name, 3600)
        redis.set(uuid+user_key+"id", id, 3600)
        await msg.say(f"复制机器人返回的秘钥,在tg机器人中输入\n"
                      f"机器人秘钥+用户秘钥\n"
                      f"例:9204647c4650123456\n"
                      f"其中123456为用户秘钥")
        await msg.say(uuid)

