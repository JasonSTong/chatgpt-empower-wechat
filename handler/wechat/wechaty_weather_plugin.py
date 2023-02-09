import json
import logging
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Message, Contact, Room

from openai_.openai_default import text_ai
from util.scheduler_ import schedulerWeatherTask


class WechatyWeatherPoster(WechatyPlugin):

    def __init__(self):
        super().__init__()

    async def init_plugin(self, wechaty: Wechaty) -> None:
        await super().init_plugin(wechaty)

    async def on_message(self, msg: Message) -> None:
        """
               推送 天气
               :param msg:
               :return:
               """
        text = msg.text()
        fromContact = msg.talker()
        room = msg.room()
        conversation: Union[
            Room, Contact] = fromContact if room is None else room
        if "#" in text and "天气" in text and "推送" in text:
            try:
                response_text = text_ai(
                    '解析这句话中的时间地点，格式化时间为cron形式以"minute, hour, day of month, month, day of week"排序时间参数,并且忽略秒，以["时间","地点"],其中引号需要变为双引号返回给我。' + f"'{text}'")
                # index0:dict 时间,index1:地点
                print(response_text)
                time_corn_and_city: list = json.loads(
                    response_text[0].replace("\n", "").replace("答案", "").replace("answer", "").replace("=", "").replace(
                        "#：", "").replace("#:", "")
                )
                time_dict: str = time_corn_and_city[0]
                city = time_corn_and_city[1]
                print("时间:", time_dict)
                print("城市:", city)
                await schedulerWeatherTask(conversation=conversation, timer=time_dict, args=[conversation, city])
            except:
                await conversation.say("初始化失败,请稍后再试!")
