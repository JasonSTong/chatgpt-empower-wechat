import logging
import random
from typing import Union, List

from wechaty import WechatyPlugin, Wechaty, Message, Room, Contact
from wechaty.user import room
from wechaty_puppet import FileBox

from base import redis
from openai_.openai_default import text_ai, img_ai


class WechatAI(WechatyPlugin):

    def __init__(self):
        super().__init__()

    async def init_plugin(self, wechaty: Wechaty) -> None:
        await super().init_plugin(wechaty)

    async def on_message(self, msg: Message) -> None:
        is_mention_bot = await msg.mention_self()
        mention_user = None
        if is_mention_bot:
            mention_user = [msg.talker().contact_id]
        is_room = msg.room()
        if "HandOffMaster" in msg.text():
            return
        if "weixin://dl/feedback?from=" in msg.text():
            return
        is_self = msg.talker().is_self()
        conversation: Union[
            Room, Contact] = msg.talker() if msg.room() is None else msg.room()
        # 处理疯狂处理微信团队消息
        if is_room is None and conversation.get_id().__eq__('weixin'):
            return
        # 处理对话
        if is_self is not True and (
                (is_room is not None and is_mention_bot and "#" not in msg.text()) or
                (is_room is None and "#" not in msg.text())
        ):
            try:
                # 上下文存储在redis
                chat_id = ''
                if is_room is not None:
                    chat_id = chat_id + is_room.room_id
                chat_id = chat_id + msg.talker().contact_id
                context_str = redis.get(chat_id) or ''
                context_str = context_str + f"(You:{msg.text()})"
                response_list = text_ai(context_str)
                i: int = 1
                for response_text in response_list:
                    context_str = context_str + response_text
                    # 每次新的对话进来,增加过期时间
                    redis.set(chat_id, context_str)
                    redis.expire(chat_id, 120)
                    size = len(response_list)
                    if size == 1:
                        await mention_and_say(response_text, msg.room(), mention_user, conversation)
                        return
                    await mention_and_say(
                        f"第" + str(i) + "页/总计" + str(size) + "页\n"
                                                             "================\n" +
                        response_text, msg.room(), mention_user, conversation
                    )
                    i = i + 1
                return
            except Exception as e:
                logging.error(e)
                return

        # 处理生成图片
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成图片" in msg.text()) or (
                is_room is None and "#生成图片" in msg.text())):
            print("需要生成的信息:" + msg.text())

            generate_text = msg.text().split('#生成图片')[1]
            img_url = img_ai(generate_text)
            if len(img_url) < 2:
                await mention_and_say("生成图片失败", msg.room(), mention_user, conversation)
            else:
                img_file_box = FileBox.from_url(img_url, name=generate_text + '.jpeg')
                await mention_and_say(img_file_box, msg.room(), mention_user, conversation)
            return

        # 处理生成周报
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成日报" in msg.text()) or
                                    (is_room is None and "#生成日报" in msg.text())
        ):
            generate_text = msg.text().split('#生成日报')[1]
            weekly_list = text_ai(f"请帮我把以下的工作内容填充为一篇完整的日报,以分点叙述的形式输出.'{generate_text}'")
            if len(weekly_list) < 1:
                await mention_and_say("生成日报失败", msg.room(), mention_user, conversation)
            else:
                await create_ai_text(weekly_list, msg.room(), mention_user, conversation)

        # 处理生成周报
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成周报" in msg.text()) or
                                    (is_room is None and "#生成周报" in msg.text())
        ):
            generate_text = msg.text().split('#生成周报')[1]
            weekly_list = text_ai(f"请帮我把以下的工作内容填充为一篇完整的周报,以分点叙述的形式输出.'{generate_text}'")
            if len(weekly_list) < 1:
                await mention_and_say("生成周报", msg.room(), mention_user, conversation)
            else:
                await create_ai_text(weekly_list, msg.room(), mention_user, conversation)


async def create_ai_text(response_list: list, room_, mention_user, conversation: Union[Room, Contact]):
    i: int = 1
    for response in response_list:
        size = len(response_list)
        if size == 1:
            await mention_and_say(response, room_, mention_user, conversation)
            return
        await mention_and_say(
            f"第" + str(i) + "页/总计" + str(size) + "页\n"
                                                 "================\n" +
            response, room_, mention_user, conversation)
        i = i + 1


async def mention_and_say(response_obj, room_, mention_users: List[str], conversion: Union[Room, Contact]):
    if room_ is not None:
        await conversion.say(response_obj, mention_users)
    else:
        await conversion.say(response_obj)
