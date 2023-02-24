import json
import logging
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Contact, Room, Message
from wechaty_puppet import get_logger

from base import base_help_list
from openai_.openai_default import text_ai
from util.scheduler_ import schedulerTodoTask, removeTask, getTaskList

log = get_logger(__name__)


class WechatyTodoPoster(WechatyPlugin):
    def set_helper(self):
        base_help_list.append(
            {"备忘录": [{"1.添加备忘录": "1.#提醒我+时间+事件\ne.g. #提醒我8点55上班打卡", "2.获取备忘录列表": "#任务列表", "3.删除备忘录": "#删除任务+id"}]})

    def __init__(self):
        super().__init__()
        self.set_helper()

    async def init_plugin(self, wechaty: Wechaty) -> None:
        await super().init_plugin(wechaty)

    async def on_message(self, msg: Message) -> None:
        text = msg.text()
        fromContact = msg.talker()
        room = msg.room()
        conversation: Union[
            Room, Contact] = fromContact if room is None else room
        if "#" in text and "提醒我" in text:
            try:
                response_text = text_ai(
                    '(You:解析这句话中的时间地点日期事件"每天8点20提醒我打卡上班"，如果其中有时间则格式化时间为cron形式以"minute, hour, day of month, month, day of week"排序时间参数并且忽略秒，以["时间","事件"],其中引号需要变为双引号返回给我。例如:["0 18 * * *","打卡下班"])["20 8 * * *","打卡上班"](You:每天11点45提醒我准备吃饭)["45 11 * * *","准备吃饭"](You: ' + text + ')')
                # index0:dict 时间,index1:地点
                time_corn_and_todo: list = json.loads(
                    response_text[0].replace("\n", "").replace("答案", "").replace("answer", "").replace("=", "").replace(
                        "#：", "").replace("#:", "")
                )
                time_dict: str = time_corn_and_todo[0]
                todo = time_corn_and_todo[1]
                await schedulerTodoTask(conversation=conversation, timer=time_dict, args=[conversation, todo])
            except Exception as e:
                log.info(e)
                if "already" not in e.__str__():
                    await conversation.say("初始化失败,请稍后再试!")
                else:
                    await conversation.say("设置成功!")
        conv_id = conversation.contact_id if isinstance(conversation, Contact) else conversation.room_id
        if "#" in text and ("删除任务" in text or "删除" in text):
            index_msg = ''
            if len(msg.text().split('#删除任务')) > 1:
                index_msg = msg.text().split('#删除任务')[1].replace(" ", "")
            else:
                index_msg = msg.text().split('#删除')[1].replace(" ", "")
            await removeTask(conv_id, int(index_msg), conversation)
        if "#" in text and ("任务列表" in text or "任务列表" in text):
            task_str = "\n".join(getTaskList(conv_id))
            await conversation.say(task_str)
