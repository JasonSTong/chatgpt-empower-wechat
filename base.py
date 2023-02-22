import json
import logging
import os
import random

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.client import Redis
from telegram.ext import PicklePersistence, Application, CommandHandler

import openai
from config.config import collection_get, get_env
from config.generation_config import generation_config

""" 初始化日志 """
logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='log.log',
                    filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format='%(levelname)s-%(asctime)s-%(message)s [%(filename)s-%(funcName)s-%(lineno)d]',
                    datefmt='%m/%d/%Y %I:%M:%S %p'
                    # 日志格式
                    )
logging.getLogger('apscheduler').setLevel('DEBUG')
"""初始化连接信息配置"""
generation_config()
"""获取当前环境信息"""
env = get_env()
"""配置Redis"""
redis_config_key = 'REDIS_' + env
redis_url = collection_get(redis_config_key, 'url') or 'redis://localhost:6379/0'
redis = Redis.from_url(
    redis_url,
    decode_responses=collection_get(redis_config_key, 'decode'),
    encoding=collection_get(redis_config_key, 'encoding'),
    max_connections=int(collection_get(redis_config_key, 'MAX_COLLECTIONS')) or 500,
    socket_timeout=int(collection_get(redis_config_key, 'socket_timeout')),
    socket_connect_timeout=int(collection_get(redis_config_key, 'socket_connect_timeout'))
)

""" 初化scheduler """
redis_info_List = redis_url.replace("redis://", "").replace("/0", "").split(":")
jobstores = {
    'default': RedisJobStore(host=redis_info_List[0], port=redis_info_List[1])
}
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
# scheduler.start()
# scheduler.resume()
""" 初始化tgBOT """
if len(collection_get('TELEGRAM_' + env, 'TOKEN')) > 1:
    persistence = PicklePersistence(filepath='arbitrarycallbackdatabot')
    tg_application = (
        Application.builder()
            .token(collection_get('TELEGRAM_' + env, 'TOKEN'))
            .persistence(persistence)
            .arbitrary_callback_data(True)
            .proxy_url('http://127.0.0.1:58591')
            .build()
    )
    """ 初始化tgBOT命令组 """
    # tg_application.add_handler(CommandHandler('bind', bind_wechat))

""" 初始化OpenAi """
# 获取OpenAIkey
openai_keys = collection_get('OPENAI_' + env, 'key')
openai_keys = openai_keys.strip('[')
openai_keys = openai_keys.strip(']')
openai_keys = openai_keys.replace("'", "")
openai_key_list = openai_keys.split(',')
openai_org = collection_get('OPENAI_' + env, 'ORGANIZATION')

""" 初始化管理员列表 """
root_user_uuids = collection_get('ROOT_' + env, 'ROOT_USER_UUID')
root_user_uuids = root_user_uuids.strip('[')
root_user_uuids = root_user_uuids.strip(']')
root_user_uuids = root_user_uuids.replace("'", "")
root_user_uuid_list = root_user_uuids.split(',')
"""初始化帮助信息"""
base_help_list = []
base_menu_list = []
secondary_menu_list = []
final_menu_list = []