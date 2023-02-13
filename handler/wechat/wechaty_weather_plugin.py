import json
import logging
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Message, Contact, Room

from handler.scheduler_h.schedulers_handler import sendWeather
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
                    f'解析这句话中的时间地点日期'+text+'，如果其中有时间则格式化时间为cron形式以"minute, hour, day of month, month, day of week"排序时间参数并且忽略秒，如果这句话里有今天，明天，后天作为日期提取出来放在第三个参数中，如果没有默认为今天。以["时间","地点","日期"],其中引号需要变为双引号返回给我。例如:["0 18 * * *","武汉","今天"] ,[None,"武汉","今天"]')
                # index0:dict 时间,index1:地点 index2:日期
                time_corn_and_city: list = json.loads(
                    response_text[0].replace("\n", "").replace("答案", "").replace("answer", "").replace("=", "").replace(
                        "#：", "").replace("#:", "")
                )
                time_dict: str = time_corn_and_city[0]
                city = time_corn_and_city[1]
                day = time_corn_and_city[2]
                if time_dict.__eq__('None'):
                    await sendWeather(conversation, city,day)
                    return
                await schedulerWeatherTask(conversation=conversation, timer=time_dict, args=[conversation, city,day])
            except Exception as e:
                logging.error(e)
                if "already" not in e.__str__():
                    await conversation.say("初始化失败,请稍后再试!")
                else:
                    await conversation.say("设置成功!")
