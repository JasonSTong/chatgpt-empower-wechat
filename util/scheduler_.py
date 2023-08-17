import json
import pickle
from typing import Union, Any

from apscheduler.triggers.cron import CronTrigger
from wechaty import Contact, Room, Wechaty

from base import scheduler, redis
from handler.scheduler_h.schedulers_handler import sendWeather, sendTodo, scheduler_pusher


def addOrUpdateScheduler(scheduler_name: str, conv_id: str, name: str, timer: str, func: Any, args=None):
    # trigger = CronTrigger(**timer)
    trigger = CronTrigger.from_crontab(timer, timezone="Asia/Shanghai")

    s = scheduler.get_job(scheduler_name)
    if s is not None:
        redis.lrem(conv_id, 1, json.dumps({"schedule_name": scheduler_name, "task_name": s.args[len(s.args) - 1]}))
        scheduler.remove_job(scheduler_name)
    scheduler.add_job(func,
                      trigger=trigger,
                      args=args,
                      id=scheduler_name,
                      timezone='Asia/Shanghai'
                      )
    redis.rpush(conv_id, json.dumps({"schedule_name": scheduler_name, "task_name": name}))
    scheduler.start()


def addOrUpdateSchedulerV2(scheduler_name: str, conv_id: str, name: str, timer: str,room_or_user: int, true_func: Any,
                           true_args=type[list]):
    trigger = CronTrigger.from_crontab(timer, timezone="Asia/Shanghai")

    s = scheduler.get_job(scheduler_name)
    # check this task exists
    if s is not None:
        redis.lrem(conv_id, 1, json.dumps({"schedule_name": scheduler_name, "task_name": name}))
        scheduler.remove_job(scheduler_name)
    # build true args to scheduler pusher
    args: list = []
    args.append(room_or_user)
    args.append(conv_id)
    args.append(true_func)
    args.append(true_args)
    scheduler.add_job(scheduler_pusher,
                      trigger=trigger,
                      args=args,
                      id=scheduler_name,
                      timezone='Asia/Shanghai'
                      )
    redis.rpush(conv_id, json.dumps({"schedule_name": scheduler_name, "task_name": name}))
    scheduler.start()


def getTaskList(name: str) -> list:
    task_name_list = []
    task_list = redis.lrange(name, 0, -1)
    i = 1
    for task_str in task_list:
        # id:xxxx name:taskName
        task_dict = json.loads(task_str)
        task_name_list.append(f"{i}.{task_dict['task_name']}")
        i = i + 1
    if len(task_name_list) < 1:
        task_name_list.append("暂时没有任务,请添加任务.\n例:#每天8点30推送当日武汉天气")
    else:
        task_name_list.append("如果删除,请从大到小删除")
    return task_name_list


async def removeTask(conv_id: str, index: int, conversation: Union[Contact, Room]):
    # 删除任务列表
    index_value = redis.lindex(conv_id, index - 1)
    redis.lrem(conv_id, 1, index_value)
    task_dict = json.loads(index_value)
    # 删除scheduler任务
    s = scheduler.get_job(task_dict['schedule_name'])
    if s is not None:
        scheduler.remove_job(task_dict['schedule_name'])
    await conversation.say("删除成功")


async def removeAll(conv_id: str, conversation: Union[Contact, Room]):

    task_list = redis.lrange(conv_id, 0, -1)
    i = 1
    for task_str in task_list:
        # id:xxxx name:taskName
        task_dict = json.loads(task_str)
        s = scheduler.get_job(task_dict['schedule_name'])
        if s is not None:
            scheduler.remove_job(task_dict['schedule_name'])
    redis.delete(conv_id)
    await conversation.say("删除成功")


async def schedulerWeatherTask(conversation: Union[Contact, Room], timer: str, args: list):
    """
    定时推送天气
    :param conversation:
    :param timer:
    :param args:
    :return:
    """
    conv_id = ''
    # 0:room 1:user
    room_or_user: int = 1
    if isinstance(conversation, Contact):
        conv_id = conversation.contact_id
    else:
        conv_id = conversation.room_id
        room_or_user = 0
    name = args[2]
    print(f"Push-Weather-{conv_id}-{args[1]}-{args[2]}")

    addOrUpdateSchedulerV2(scheduler_name=f"Push-Weather-{conv_id}-{args[0]}-{args[1]}", conv_id=conv_id, name=name,
                           timer=timer, true_func=sendWeather,
                           true_args=args, room_or_user=room_or_user)
    await conversation.say("设置成功!")


async def schedulerTodoTask(conversation: Union[Contact, Room], timer: str, args: list):
    conv_id = conversation.contact_id if isinstance(conversation, Contact) else conversation.room_id
    name = f"{args[1]}"
    addOrUpdateScheduler(f"Push-Todo-{conv_id}-{args[1]}", conv_id, name, func=sendTodo, timer=timer, args=args)
    await args[0].say("设置成功!")

async def schedulerTodoTaskV2(conversation: Union[Contact, Room], timer: str, args: list):
    conv_id = conversation.contact_id if isinstance(conversation, Contact) else conversation.room_id
    room_or_user: int = 1
    if isinstance(conversation, Contact):
        conv_id = conversation.contact_id
    else:
        conv_id = conversation.room_id
        room_or_user = 0
    addOrUpdateSchedulerV2(scheduler_name= f"Push-Todo-{conv_id}-{args[0]}", conv_id= conv_id,room_or_user=room_or_user, true_func=sendTodo, timer=timer, true_args=args)
    await args[0].say("设置成功!")
