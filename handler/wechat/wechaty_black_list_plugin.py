import json
from typing import Union

from wechaty import WechatyPlugin, Wechaty, Contact, Room, Message, Friendship
from wechaty_puppet import ContactQueryFilter

from base import root_user_uuid_list, redis


class WechatyBlackListPlugin(WechatyPlugin):

    def __init__(self):
        super().__init__()

    async def on_message(self, msg: Message) -> None:
        fromContact = msg.talker()
        text = msg.text()
        room = msg.room()
        conversation: Union[
            Room, Contact] = fromContact if room is None else room
        if "#" in text and "root" in text:
            redis.set("root:" + fromContact.get_id(), 1)
        is_root = redis.get("root:" + fromContact.get_id())
        if is_root is None:
            return
        talker_alias = await msg.talker().alias()
        if talker_alias not in root_user_uuid_list:
            return
        if "#" in text and "初始化列表" in text:
            redis.delete("contact_list")
            find_all = await msg.talker().find_all()
            resp_contact_list = []
            i = 1
            for contact in find_all:
                name = contact.name
                redis.rpush('contact_list', json.dumps({"contact_name": name, "contact_id": contact.get_id()}))
                resp_contact_list.append(f"{i}.{name}")
                i += 1
                if len(resp_contact_list) > 9:
                    await msg.say("\n".join(resp_contact_list))
                    resp_contact_list = []
                    continue
                if i > len(find_all):
                    resp_contact_list.append("初始化完成")
                    await msg.say("\n".join(resp_contact_list))
        if "#拉黑" in text:
            index = text.split('#拉黑')[1].replace(" ", "")
            index_value = redis.lindex('contact_list', int(index) - 1)
            redis.rpush("black_list", index_value)
            await msg.say("操作成功")
            return
        if "#" in text and "解除黑名单" in text:
            index = text.split('#解除黑名单')[1].replace(" ", "")
            index_value = redis.lindex('black_list', int(index) - 1)
            redis.lrem("black_list", 1, index_value)
            await msg.say("操作成功")
            return
        if "#黑名单" in text:
            black_list = redis.lrange("black_list", 0, -1)
            await dumps2Dict2StrList(black_list, conversation)
            return
        if "#限制名单" in text:
            restrict_list = redis.lrange("restrict_list", 0, -1)
            await dumps2Dict2StrList(restrict_list, conversation)
            return
        if "#限制" in text:
            index = text.split('#限制')[1].replace(" ", "")
            index_value = redis.lindex('contact_list', int(index) - 1)
            redis.rpush("restrict_list", index_value)
            await msg.say("操作成功")
            return
        if "#" in text and "解除限制" in text:
            index = text.split('#解除限制')[1].replace(" ", "")
            index_value = redis.lindex('restrict_list', int(index) - 1)
            redis.lrem("restrict_list", 1, index_value)
            await msg.say("操作成功")
            return


async def dumps2Dict2StrList(dumps: list, conversation: Union[Room, Contact]):
    contact_list = []
    i = 1
    for contact in dumps:
        contact_dict: dict = json.loads(contact)
        contact_name = contact_dict.get('contact_name')
        contact_list.append(f"{i}.{contact_name}")
        i = i + 1
        if len(contact_list) >= 9:
            await conversation.say("\n".join(contact_list))
            contact_list = []
            continue
        if len(dumps) < i:
            contact_list.append("获取完成")
            await conversation.say("\n".join(contact_list))
