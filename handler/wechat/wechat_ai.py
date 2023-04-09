import json
from typing import Union, List

from wechaty import WechatyPlugin, Wechaty, Message, Room, Contact
from wechaty_grpc.wechaty.puppet import MessageType
from wechaty_puppet import FileBox, get_logger, ContactQueryFilter

from ai_.stable_diffusion import txt2img
from base import redis, base_help_list, base_menu_list, secondary_menu_list, final_menu_list, root_user_uuid_list, \
    sd_max_generate_msg, sd_max_generate
from ai_.openai_default import text_ai, img_ai, text_ai_v2, async_text_ai_v2

log = get_logger(__name__)


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
        if await self.pass_black_list(msg, is_room, mention_user, conversation):
            return
        if await self.helper(msg, is_room, mention_user, conversation):
            return
        # 上下文存储在redis
        new_model_context_key = "new_model_context:"
        if is_room is not None:
            new_model_context_key = new_model_context_key + is_room.room_id
        new_model_context_key = new_model_context_key + msg.talker().contact_id
        # 处理受限名单
        if await self.pass_restrict_list(msg, is_room, mention_user, conversation, new_model_context_key):
            return
        if "#清除上下文" in msg.text():
            if is_room is not None:
                new_model_context_key = new_model_context_key + is_room.room_id
            redis.delete(new_model_context_key)
            await msg.say("清除成功")
            return
        # 处理对话
        if is_self is not True and (
                (is_room is not None and is_mention_bot and "#" not in msg.text()) or
                (is_room is None and "#" not in msg.text())
        ):
            log.info(f"开始处理会话,处理信息:{msg.text()}")
            new_model_context = []
            await self.generate_ai_text(msg, new_model_context, new_model_context_key, mention_user, conversation)

        # 处理生成图片
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成图片" in msg.text()) or (
                is_room is None and "#生成图片" in msg.text())):
            stable_diffusion_key = "stable_diffusion:" + msg.talker().contact_id
            count_sd = 1
            if redis.exists(stable_diffusion_key):
                count_sd = int(redis.get(stable_diffusion_key))
                if count_sd > sd_max_generate:
                    await self.mention_and_say(sd_max_generate_msg, msg.room(), mention_user,
                                               conversation)
                    return None
            stable_diffusion_context = [{"role": "system",
                                         "content": 'prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，例如构图方式、镜头的远近、人物的外观、背景、颜色和光线效果，以及图像的主题和风格还有参考的艺术家等等。越靠前的词语对画面构成影响越大，这些prompt的格式经常包含括号内的加权数字，用于指定某些细节的重要性或强调，默认权重为1.0，大于1.0的值证明权重增加，小于1.0的值证明权重降低。例如"(masterpiece:1.5)"表示这个词的权重是1.5倍，是一张杰作，多个括号也有类似作用。'},
                                        {"role": "system",
                                         "content": '下面是一个prompt例子: "extremely detailed CG unity 8k wallpaper,best quality,noon,beautiful detailed water,long black hair,beautiful detailed girl,view straight on,eyeball,hair flower,retro artstyle, (masterpiece:1.3),illustration,mature,small breast,beautiful detailed eyes,long sleeves, bright skin,(Good light:1.2)"'},
                                        {"role": "system",
                                         "content": '根据上面规则，我会在之后的对话中的[]中给你中文词汇. 根据我给的词汇拆分并构建具有中国水墨画特色的(构图方式、镜头的远近、人物的外观、背景、颜色和光线效果)prompt后,以英文发送给我。禁止nsfw prompt!禁止发送其他无关信息,只需回复prompt字符串即可'},
                                        {"role": "user", "content": f"[{msg.text().split('#生成图片')[1]}]"}]
            await self.mention_and_say(f"⛽️ 准备生成... 可用次数{count_sd}/{sd_max_generate} \n 请勿重复生成,多次生成可能会进入黑名单", msg.room(), mention_user,
                                       conversation)
            sd_prompt = await async_text_ai_v2(stable_diffusion_context)
            is_online, file_path_or_error_msg = txt2img('二刺猿', next(iter(
                sd_prompt)) + '(((<lora:Moxin_10:0.85> ))),(traditional chinese ink painting:1.5),((4k,masterpiece,best quality))')
            if is_online is not True:
                await self.mention_and_say(file_path_or_error_msg, msg.room(), mention_user, conversation)
                return None
            redis.set(stable_diffusion_key, count_sd + 1)
            file = FileBox.from_file(file_path_or_error_msg)
            await self.mention_and_say(file, msg.room(), mention_user, conversation)
            return None

        # 处理生成周报
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成日报" in msg.text()) or
                                    (is_room is None and "#生成日报" in msg.text())
        ):
            generate_text = msg.text().split('#生成日报')[1]
            weekly_list = text_ai(f"请帮我把以下的工作内容填充为一篇完整的日报,以分点叙述的形式输出.'{generate_text}'")
            if len(weekly_list) < 1:
                await self.mention_and_say("生成日报失败", msg.room(), mention_user, conversation)
            else:
                await self.create_ai_text(weekly_list, msg.room(), mention_user, conversation)

        # 处理生成周报
        if is_self is not True and ((is_room is not None and is_mention_bot and "#生成周报" in msg.text()) or
                                    (is_room is None and "#生成周报" in msg.text())
        ):
            generate_text = msg.text().split('#生成周报')[1]
            weekly_list = text_ai(f"请帮我把以下的工作内容填充为一篇完整的周报,以分点叙述的形式输出.'{generate_text}'")
            if len(weekly_list) < 1:
                await self.mention_and_say("生成周报失败", msg.room(), mention_user, conversation)
            else:
                await self.create_ai_text(weekly_list, msg.room(), mention_user, conversation)

    async def generate_ai_text(self, msg: Message, new_model_context: list, new_model_context_key: str, mention_user,
                               conversation):
        response_list = []
        try:
            if redis.exists(new_model_context_key):
                new_model_context = redis.lrange(new_model_context_key, 0, -1)
                new_model_context = [json.loads(x) for x in new_model_context]
            new_model_context.append({"role": "user", "content": msg.text()})
            redis.rpush(new_model_context_key, json.dumps({"role": "user", "content": msg.text()}))
            response_list = await async_text_ai_v2(new_model_context)
            i = 1
            for response_text in response_list:
                # 每次新的对话进来,增加过期时间
                redis.rpush(new_model_context_key, json.dumps({"role": "assistant", "content": response_text}))
                redis.expire(new_model_context_key, 120)
                size = len(response_list)
                if size == 1:
                    await self.mention_and_say(response_text, msg.room(), mention_user, conversation)
                    return
                await self.mention_and_say(
                    f"第" + str(i) + "页/总计" + str(size) + "页\n"
                                                         "================\n" +
                    response_text, msg.room(), mention_user, conversation
                )
                i = i + 1
        except Exception as e:
            log.info(f"发成异常,原因:{e},请求gpt返回:{response_list}")
            await self.mention_and_say("生成回复失败,请稍后再试", msg.room(), mention_user, conversation)
            contact = await self.bot.Contact.find(ContactQueryFilter(alias=root_user_uuid_list[0]))
            await contact.say(f"用户[{msg.talker().name}].\n问bot:[{msg.text()}],发生异常.\nbot回复:[{response_list}]")
            return

            # 帮助页面

    async def helper(self, msg: Message, room_, mention_users: List[str], conversation: Union[Room, Contact]) -> bool:
        talker_id = msg.talker().contact_id
        if "#stop help" in msg.text():
            redis.delete("helper:" + talker_id)
            await self.mention_and_say("已退出help", room_, mention_users, conversation)
            return True
        if redis.exists("helper:" + talker_id):
            try:
                i = int(msg.text())
                if i > 10:
                    raise RuntimeError
            except Exception as e:
                log.error(f"输入数字过大,或者输入文字了.{msg.text()}")
                await self.mention_and_say("\n".join(base_menu_list), room_, mention_users, conversation)
                redis.set("helper:" + talker_id, '', 60)
                return True
            helper_code = msg.text() if len(redis.get("helper:wxid_41i9g973qtuj21")) < 1 else redis.get(
                "helper:wxid_41i9g973qtuj21") + f",{msg.text()}"
            redis.set("helper:" + talker_id, helper_code, 60)
            help_len = len(helper_code)
            help_code_split = helper_code.split(",")
            # 判断是否输入0
            if help_code_split[len(help_code_split) - 1] == '0':
                await self.mention_and_say("\n".join(base_menu_list), room_, mention_users, conversation)
                redis.set("helper:" + talker_id, '', 60)
                return True
            try:
                # 第一次选择之后返回的str
                if 0 < help_len < 2:
                    help_obj = secondary_menu_list[int(help_code_split[0]) - 1]
                    if isinstance(help_obj, str):
                        await self.mention_and_say(help_obj, room_, mention_users, conversation)
                    else:
                        await self.mention_and_say("\n".join(help_obj), room_, mention_users, conversation)
                if help_len > 2:
                    await self.mention_and_say(
                        final_menu_list[int(helper_code.split(",")[0]) - 1][int(helper_code.split(",")[1]) - 1], room_,
                        mention_users, conversation)
                return True
            except Exception as e:
                log.error(f"选择异常:error:{e},helper_code:{helper_code}")
                await self.mention_and_say("输入错误,请重新输入\n" + "\n".join(base_menu_list), room_, mention_users,
                                           conversation)
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
            await self.mention_and_say("\n".join(base_menu_list), room_, mention_users, conversation)
            redis.set("helper:" + talker_id, '', 60)
            return True
        return False

    async def create_ai_text(self, response_list: list, room_, mention_user, conversation: Union[Room, Contact]):
        i: int = 1
        for response in response_list:
            size = len(response_list)
            if size == 1:
                await self.mention_and_say(response, room_, mention_user, conversation)
                return
            await self.mention_and_say(
                f"第" + str(i) + "页/总计" + str(size) + "页\n"
                                                     "================\n" +
                response, room_, mention_user, conversation)
            i = i + 1

    async def mention_and_say(self, response_obj, room_, mention_users: List[str], conversation: Union[Room, Contact]):
        if room_ is not None:
            await conversation.say(response_obj, mention_users)
        else:
            await conversation.say(response_obj)

    async def pass_black_list(self, msg: Message, room_, mention_users: List[str],
                              conversation: Union[Room, Contact]) -> bool:
        name = msg.talker().name
        is_mention_bot = await msg.mention_self()
        black_list = redis.lrange("black_list", 0, -1)
        if json.dumps({"contact_name": name, "contact_id": msg.talker().contact_id}) in black_list:
            if room_ is not None and is_mention_bot:
                await self.mention_and_say("当前账号封禁中,请联系管理员.", room_, mention_users, conversation)
            return True
        return False

    async def pass_restrict_list(self, msg: Message, room_, mention_users: List[str],
                                 conversation: Union[Room, Contact], new_model_context_key) -> bool:
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
                    await self.mention_and_say("当前账号限制中,请稍后再试或请联系管理员.", room_, mention_users, conversation)
                    return True
            return False

    async def change_completion_mode(self, contact: str) -> bool:
        mode_context = redis.get("mode_context:" + contact)
        if mode_context is None:
            return False

    mode_dict = {"code-helper": "", "mao": "", "interviewer": ""}

    # 旧模型使用
    # response_list = []
    # try:
    #     context_str = context_str + f"(You:{msg.text()})"
    #     response_list = text_ai(context_str)
    #     i: int = 1
    #     for response_text in response_list:
    #         context_str = context_str + response_text
    #         # 每次新的对话进来,增加过期时间
    #         redis.set(chat_id, context_str)
    #         redis.expire(chat_id, 120)
    #         size = len(response_list)
    #         if size == 1:
    #             await self.mention_and_say(response_text, msg.room(), mention_user, conversation)
    #             return
    #         await self.mention_and_say(
    #             f"第" + str(i) + "页/总计" + str(size) + "页\n"
    #                                                  "================\n" +
    #             response_text, msg.room(), mention_user, conversation
    #         )
    #         i = i + 1
    #     return
    # except Exception as e:
    #     log.info(f"发成异常,原因:{e},请求gpt返回:{response_list}")
    #     await self.mention_and_say("生成回复失败,请稍后再试", msg.room(), mention_user, conversation)
    #     contact = await self.bot.Contact.find(ContactQueryFilter(alias=root_user_uuid_list[0]))
    #     await contact.say(f"用户[{msg.talker().name}].\n问bot:[{msg.text()}],发生异常.\nbot回复:[{response_list}]")
    #     return
