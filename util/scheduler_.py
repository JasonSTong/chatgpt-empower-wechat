from typing import Union, Any

from apscheduler.triggers.cron import CronTrigger
from wechaty import Contact, Room

from base import scheduler
from handler.scheduler_h.schedulers_handler import sendWeather


def addOrUpdateScheduler(scheduler_name: str, timer: str, func: Any, args=None):
    # trigger = CronTrigger(**timer)
    trigger = CronTrigger.from_crontab(timer, timezone="Asia/Shanghai")

    s = scheduler.get_job(scheduler_name)
    if s is not None:
        scheduler.remove_job(scheduler_name)
    scheduler.add_job(func,
                      trigger=trigger,
                      args=args,
                      id=scheduler_name,
                      timezone='Asia/Shanghai'
                      )
    scheduler.start()


async def schedulerWeatherTask(conversation: Union[Contact, Room], timer: str, args: list):
    """
    定时推送天气
    :param conversation:
    :param timer:
    :param args:
    :return:
    """
    id = conversation.contact_id if isinstance(conversation, Contact) else conversation.room_id
    addOrUpdateScheduler(f"Push-Weather-{id}", func=sendWeather, timer=timer, args=args)
    await args[0].say("设置成功!")
