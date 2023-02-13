import json
import logging
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Contact, Room, Message

from openai_.openai_default import text_ai
from util.scheduler_ import schedulerTodoTask, removeTask, getTaskList


class WechatyTodoPoster(WechatyPlugin):

    def __init__(self):
        super().__init__()

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
                    '解析这句话中的时间和提醒事件，格式化时间为cron形式以"[minute, hour, day of month, month, day of week]"排序时间参数,并且忽略秒，以["时间","事件"],其中引号需要变为双引号返回给我。例如:["0 18 * * *","提醒我下班打卡"]' + f"'{text}'")
                # index0:dict 时间,index1:地点
                time_corn_and_todo: list = json.loads(
                    response_text[0].replace("\n", "").replace("答案", "").replace("answer", "").replace("=", "").replace(
                        "#：", "").replace("#:", "")
                )
                time_dict: str = time_corn_and_todo[0]
                todo = time_corn_and_todo[1]
                await schedulerTodoTask(conversation=conversation, timer=time_dict, args=[conversation, todo])
            except Exception as e:
                logging.error(e)
                if "already" not in e.__str__():
                    await conversation.say("初始化失败,请稍后再试!")
                else:
                    await conversation.say("设置成功!")
        conv_id = conversation.contact_id if isinstance(conversation, Contact) else conversation.room_id
        if "#" in text and ("删除任务" in text or "删除" in text):
            index_msg = ''
            if len(msg.text().split('#删除任务') ) > 1:
                index_msg = msg.text().split('#删除任务')[1].replace(" ", "")
            else:
                index_msg= msg.text().split('#删除')[1].replace(" ", "")

            await removeTask(conv_id, int(index_msg),conversation)
        if "#" in text and ("推送列表" in text or "任务列表" in text):
            task_str = "\n".join(getTaskList(conv_id))
            await conversation.say(task_str)
