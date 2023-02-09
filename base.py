import logging
import os

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.client import Redis
from telegram.ext import PicklePersistence, Application, CommandHandler

import openai
from config.config import collection_get, get_env
from config.generation_config import generation_config

"""
    本地环境
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '127.0.0.1:18181'
"""

"""
    家庭nas环境
os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = '192.168.31.137:9001'
"""

"""
    外部环境
"""
os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = ''  # ip+port

os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = ''  # uuid

""" 初始化日志 """
logging.basicConfig()
logging.getLogger('apscheduler').setLevel('DEBUG')

""" 初始化scheduler """
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')

"""初始化连接信息配置"""
generation_config()
"""获取当前环境信息"""
env = get_env()
redis_config_key = 'REDIS_' + env

redis = Redis.from_url(
    collection_get(redis_config_key, 'url') or 'redis://localhost:6379/0',
    decode_responses=collection_get(redis_config_key, 'decode'),
    encoding=collection_get(redis_config_key, 'encoding'),
    max_connections=int(collection_get(redis_config_key, 'MAX_COLLECTIONS')) or 500,
    socket_timeout=int(collection_get(redis_config_key, 'socket_timeout')),
    socket_connect_timeout=int(collection_get(redis_config_key, 'socket_connect_timeout'))
)

""" 初始化tgBOT """
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
openai_key = collection_get('OPENAI_' + env, 'key')
openai_org = collection_get('OPENAI_' + env, 'ORGANIZATION')
openai.api_key = openai_key
openai.organization = openai_org

# 初始化openAI调用
completion_ai_api = openai.Completion
image_ai_api = openai.Image
