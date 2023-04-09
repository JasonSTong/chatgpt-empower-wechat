import json
import logging
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Message, Contact, Room
from wechaty_puppet import get_logger

from base import base_help_list
from handler.scheduler_h.schedulers_handler import sendWeather
from ai_.openai_default import text_ai
from util.scheduler_ import schedulerWeatherTask

log = get_logger(__name__)


class WechatyWeatherPoster(WechatyPlugin):

    def set_helper(self):
        base_help_list.append(
            {"推送天气消息": [{"1.实时推送": "1.#推送+地区+今/明/后+天气\n不要求顺序\ne.g. #推送明天武汉天气",
                         "2.定时推送": "#时间+推送+地区+今/明/后+天气\n不要求顺序\ne.g. #每天8点20推送武汉天气\n不填今/明/后参数 默认为今天"}]})

    def __init__(self):
        super().__init__()
        self.set_helper()

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
                    f'(You:解析这句话中的时间地点日期事件"每天8点20推送武汉天气"，如果其中有时间则格式化时间为cron形式以"minute, hour, day of month, month, day of week"排序时间参数并且忽略秒，如果这句话里有今天，明天，后天作为日期提取出来放在第三个参数中，如果没有默认为今天。以["时间","地点","日期","事件"],其中引号需要变为双引号返回给我。例如:["0 18 * * *","武汉","今天","18点推送武汉今天天气"] ,[None,"武汉","今天","立即推送武汉今天天气"])["20 8 * * *","武汉","今天","8点20推送武汉今天天气"](You:推送武汉天气)["None","武汉","今天","立即推送武汉今天天气"](You:)推送成都天气(Chatgpt:)["None","成都","今天","立即推送成都天气"](You:' + text + ')')
                # index0:dict 时间,index1:地点 index2:日期
                time_corn_and_city: list = json.loads(
                    response_text[0].replace("\n", "").replace("答案", "").replace("answer", "").replace("=", "").replace(
                        "#：", "").replace("#:", "").replace("'", '"').replace("None,", 'None",')
                )
                time_dict: str = time_corn_and_city[0]
                city = time_corn_and_city[1]
                day = time_corn_and_city[2]
                name = time_corn_and_city[3]
                if time_dict.__eq__('None'):
                    await sendWeather(conversation, city, day, "")
                    return
                await schedulerWeatherTask(conversation=conversation, timer=time_dict,
                                           args=[conversation, city, day, name])
            except Exception as e:
                log.error(e)
                if "already" not in e.__str__():
                    await conversation.say("初始化失败,请稍后再试!")
                else:
                    await conversation.say("设置成功!")
