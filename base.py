import json
import os
from mitmproxy import http

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask.cli import load_dotenv
from redis.client import Redis
from telegram.ext import PicklePersistence, Application

from wechaty import WechatyOptions, Wechaty

from config.config import collection_get, get_env
from config.generation_config import generation_config

""" 初始化日志 """
os.environ['WECHATY_LOG_FILE'] = 'logs.log'
os.environ['WECHATY_LOG'] = 'verbose'
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
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai',jobstores= jobstores)
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
""" 初始化stable_diffusion 配置信息"""
sd_ = "STABLE_DIFFUSION"
sd_ip = collection_get(sd_, 'sd_ip')
sd_port = int(collection_get(sd_, 'sd_port'))
sd_max_generate = int(collection_get(sd_, 'sd_max_generate'))
sd_max_generate_msg = collection_get(sd_, 'sd_max_generate_msg')
sd_server_error_msg = collection_get(sd_, 'sd_server_error_msg')
print(collection_get(sd_, 'sd_models'))
print(collection_get(sd_, 'sd_models').__len__())
sd_models = json.loads(collection_get(sd_, 'sd_models').replace("'", '"')) if collection_get(sd_, 'sd_models').__len__() > 4 else {}
"""
Wechaty
"""
load_dotenv()
options = WechatyOptions(
    port=os.environ.get('port', 9001)
)
bot = Wechaty(options)