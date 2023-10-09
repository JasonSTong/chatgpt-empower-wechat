import configparser
import json
import os

config = configparser.ConfigParser()
config_dict = {}
config_path = 'config.json'
if not os.path.exists(config_path):
    raise RuntimeError('读取配置失败.请看README.md')
with open(config_path, 'r') as load_f:
    cf = load_f.read()
    config_dict = json.loads(cf)

config["env"] = {'env': 'LOCAL'}
""" 本地redis配置 """
config["REDIS_LOCAL"] = {'URL': config_dict.get('redis_url'),
                         'DECODE': True,
                         'ENCODING': 'utf-8',
                         'MAX_COLLECTIONS': 10,
                         'SOCKET_TIMEOUT': 5,
                         'SOCKET_CONNECT_TIMEOUT': 5
                         }
config["OPENAI_LOCAL"] = {'KEY': config_dict.get('open_ai_api_key') or [],  # api-key
                          'ORGANIZATION': ''  # api-user
                          }
config["TELEGRAM_LOCAL"] = {'TOKEN': config_dict.get('telegram_bot_token') or '',  # bot-token
                            }

config["QWEATHER_LOCAL"] = {'KEY': config_dict.get('qweather_api_key') or '',  # 和风天气api-Key
                            'LOCATION_PATH': 'https://geoapi.qweather.com/v2/city/lookup',
                            'WEATHER_PATH': 'https://devapi.qweather.com/v7/weather/3d',
                            'AIR_PATH': 'https://devapi.qweather.com/v7/air/5d'
                            }
config["ROOT_LOCAL"] = {"ROOT_USER_UUID": config_dict.get('root_user_uuid') or []}

config["STABLE_DIFFUSION"] = {"sd_ip": config_dict.get('sd_ip') or '127.0.0.1',
                              "sd_port": config_dict.get('sd_port') or '7860',
                              "sd_max_generate": config_dict.get('sd_max_generate') or 3,
                              "sd_server_error_msg": config_dict.get(
                                  'sd_server_error_msg') or '❌ SD Server Error 404 \n 📲 请联系管理员让他上线服务',
                              "sd_max_generate_msg": config_dict.get(
                                  'sd_max_generate_msg') or f"🙈 超过生成最大次数了[{config_dict.get('sd_max_generate') or 3}]\n 📲 联系管理员解决吧",
                              "sd_models": str(config_dict.get('sd_models'))}


def generation_config():
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = config_dict.get('wechaty_url') or ''  # ip+port
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = config_dict.get('wechaty_token') or ''  # uuid
    if config_dict.get('proxy') is not None and len(config_dict.get('proxy').get('http')) > 8:
        os.environ['http_proxy'] = config_dict.get('proxy').get('http')
    if config_dict.get('proxy') is not None and len(config_dict.get('proxy').get('https')) > 8:
        os.environ['https_proxy'] = config_dict.get('proxy').get('https')
    if config_dict.get('Tpart') is not None:
        os.environ['OPENAI_API_BASE'] = config_dict.get('Tpart')
    with open('cfg.ini', 'w') as configfile:
        config.write(configfile)
