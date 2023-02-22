import json
import logging
import random
from typing import Union, List

from wechaty import WechatyPlugin, Wechaty, Message, Room, Contact
from wechaty.user import room
from wechaty_grpc.wechaty.puppet import MessageType
from wechaty_puppet import FileBox

from base import redis, base_help_list, base_menu_list, secondary_menu_list, final_menu_list
from openai_.openai_default import text_ai, img_ai


class WechatAI(WechatyPlugin):

    def set_helper(self):
        base_help_list.append(
            {"对话": [{"1.正常对话": "发送文字既可,暂时不支持语音,图片,表情包", "2.如果觉得bot在胡言乱语": "#清除上下文\n说明:可能存在上下文混乱,建议清除上下文."}]})

        base_help_list.append({"生成周/日报": [{"1.生成周报": "#生成周报+本周干的事", "2.生成日报": "#生成日报+今天干的事"}]})
        base_help_list.append({"生成图片": "#生成图片+文字描述\n❗️注意:生成图片可能会被拉进bot限制名单或黑名单,请谨慎使用!"})

    def __init__(self):
        super().__init__()
        self.set_helper()

    async def init_plugin(self, wechaty: Wechaty) -> None:
        await super().init_plugin(wechaty)

    async def on_message(self, msg: Message) -> None:
        # 判断是否为文字消息
        if msg.type() != MessageType.MESSAGE_TYPE_TEXT:
            return
        is_mention_bot = await msg.mention_self()
        is_self = msg.talker().is_self()
        conversation: Union[
            Room, Contact] = msg.talker() if msg.room() is None else msg.room()
        mention_user = None
        if is_mention_bot:
            mention_user = [msg.talker().contact_id]
        is_room = msg.room()
        # 处理疯狂回复微信团队消息
        if is_room is None and conversation.get_id().__eq__('weixin'):
            return
        if "HandOffMaster" in msg.text():
            return
        if "weixin://dl/feedback?from=" in msg.text():
            return
        # 处理黑名单
        if await pass_black_list(msg, is_room, mention_user, conversation):
            return
        # 处理受限名单
        if await pass_restrict_list(msg, is_room, mention_user, conversation):
            return
        if await helper(msg, is_room, mention_user, conversation):
            return
        # 上下文存储在redis
        chat_id = 'context'
        if is_room is not None:
            chat_id = chat_id + is_room.room_id
        chat_id = chat_id + msg.talker().contact_id
        context_str = redis.get(chat_id) or ''
        if "#清除上下文" in msg.text():
            if is_room is not None:
                chat_id = chat_id + is_room.room_id
            redis.delete(chat_id)
            await msg.say("清除成功")
            return
        # 处理对话
        if is_self is not True and (
                (is_room is not None and is_mention_bot and "#" not in msg.text()) or
                (is_room is None and "#" not in msg.text())
        ):
            try:
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
            await mention_and_say("由于生成图片质量太低,下线了", msg.room(), mention_user, conversation)
        #     generate_text = msg.text().split('#生成图片')[1]
        #     img_url = img_ai(generate_text)
        #     if len(img_url) < 2:
        #         await mention_and_say("生成图片失败", msg.room(), mention_user, conversation)
        #     else:
        #         img_file_box = FileBox.from_url(img_url, name=generate_text + '.jpeg')
        #         await mention_and_say(img_file_box, msg.room(), mention_user, conversation)
        #     return

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
                await mention_and_say("生成周报失败", msg.room(), mention_user, conversation)
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


async def mention_and_say(response_obj, room_, mention_users: List[str], conversation: Union[Room, Contact]):
    if room_ is not None:
        await conversation.say(response_obj, mention_users)
    else:
        await conversation.say(response_obj)


async def pass_black_list(msg: Message, room_, mention_users: List[str], conversation: Union[Room, Contact]) -> bool:
    name = msg.talker().name
    is_mention_bot = await msg.mention_self()
    black_list = redis.lrange("black_list", 0, -1)
    if json.dumps({"contact_name": name, "contact_id": msg.talker().contact_id}) in black_list:
        if room_ is not None and is_mention_bot:
            await mention_and_say("当前账号封禁中,请联系管理员.", room_, mention_users, conversation)
        return True
    return False


async def pass_restrict_list(msg: Message, room_, mention_users: List[str], conversation: Union[Room, Contact]) -> bool:
    name = msg.talker().name
    is_mention_bot = await msg.mention_self()
    restrict_list = redis.lrange("restrict_list", 0, -1)
    # 上下文存储在redis
    chat_id = 'context'
    if room_ is not None:
        chat_id = chat_id + room_.room_id
    chat_id = chat_id + msg.talker().contact_id
    context_str = redis.get(chat_id) or ''
    if json.dumps({"contact_name": name, "contact_id": msg.talker().contact_id}) in restrict_list:
        if len(context_str) > 100:
            if room_ is not None and is_mention_bot:
                await mention_and_say("当前账号限制中,请稍后再试或请联系管理员.", room_, mention_users, conversation)
                return True
        return False


async def helper(msg: Message, room_, mention_users: List[str], conversation: Union[Room, Contact]) -> bool:
    talker_id = msg.talker().contact_id
    if "#stop help" in msg.text():
        redis.delete("helper:" + talker_id)
        await mention_and_say("已退出help", room_, mention_users, conversation)
        return True
    if redis.exists("helper:" + talker_id):
        try:
            i = int(msg.text())
            if i > 10:
                raise RuntimeError
        except:
            await mention_and_say("输入错误,请重新输入", room_, mention_users, conversation)
            return True
        redis.set("helper:" + talker_id, msg.text() if len(redis.get("helper:wxid_41i9g973qtuj21")) < 1 else redis.get(
            "helper:wxid_41i9g973qtuj21") + f",{msg.text()}", 60)
        helper_code = redis.get("helper:" + talker_id)
        help_len = len(helper_code)
        # 判断是否输入0
        if helper_code.split(",")[len(helper_code.split(",")) - 1] == '0':
            await mention_and_say("\n".join(base_menu_list), room_, mention_users, conversation)
            redis.set("helper:" + talker_id, '', 60)
            return True
        try:
            # 第一次选择之后返回的str
            if 0 < help_len < 2:
                help_obj = secondary_menu_list[int(helper_code.split(",")[0]) - 1]
                if isinstance(help_obj, str):
                    await mention_and_say(help_obj, room_, mention_users, conversation)
                else:
                    await mention_and_say("\n".join(help_obj), room_, mention_users, conversation)
            if help_len > 2:
                await mention_and_say(
                    final_menu_list[int(helper_code.split(",")[0]) - 1][int(helper_code.split(",")[1]) - 1], room_,
                    mention_users, conversation)
            return True
        except:
            await mention_and_say("输入错误,请重新输入\n"+"\n".join(base_menu_list), room_, mention_users, conversation)
            redis.set("helper:" + talker_id, '', 60)
            return True
    if "#help" in msg.text():
        # 处理初始化base_help_list.append(
        #             {"对话": [{"1.正常对话": "发送文字既可,暂时不支持语音,图片,表情包", "2.如果觉得bot在胡言乱语": "#清除上下文\n说明:可能存在上下文混乱,建议清除上下文."}]})
        if len(base_menu_list) < 1:
            init_helper_index = 1
            for plugin_help_dict in base_help_list:
                for key, value in plugin_help_dict.items():
                    # 第一层 base_menu_list
                    base_menu_list.append(str(init_helper_index) + "." + key)
                    init_helper_index += 1
                    # 第二层 secondary_menu_list
                    if len(secondary_menu_list) != len(final_menu_list):
                        final_menu_list.append("")
                    if isinstance(value, list):
                        for secondary_menu_dict in value:
                            secondary_menu_list.append(list(secondary_menu_dict.keys()))
                            # for s_key, s_value in secondary_menu_dict.items():
                            final_menu_list.append(list(secondary_menu_dict.values()))
                    if isinstance(value, str):
                        secondary_menu_list.append(value)
            base_menu_list.append("帮助提示会在2分钟内失效,或对机器人说#stop help\n输入0可返回主菜单")

        # #help 返回的str
        await mention_and_say("\n".join(base_menu_list), room_, mention_users, conversation)
        redis.set("helper:" + talker_id, '', 60)
        return True
    return False
