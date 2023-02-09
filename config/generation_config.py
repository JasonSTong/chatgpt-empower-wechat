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
config["REDIS_LOCAL"] = {'URL': 'redis://localhost:6379/0',
                         'DECODE': True,
                         'ENCODING': 'utf-8',
                         'MAX_COLLECTIONS': 10,
                         'SOCKET_TIMEOUT': 5,
                         'SOCKET_CONNECT_TIMEOUT': 5
                         }
config["OPENAI_LOCAL"] = {'KEY': config_dict.get('open_ai_api_key') or '',  # api-key
                          'ORGANIZATION': 'chensitong'  # api-user
                          }
config["TELEGRAM_LOCAL"] = {'TOKEN': config_dict.get('telegram_bot_token') or '',  # bot-token
                            }

config["QWEATHER_LOCAL"] = {'KEY': config_dict.get('qweather_api_key') or '',  # 和风天气api-Key
                            'LOCATION-PATH': 'https://geoapi.qweather.com/v2/city/lookup',
                            'WEATHER-PATH': 'https://devapi.qweather.com/v7/weather/3d'
                            }


def generation_config():
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = config_dict.get('wechaty_path') or ''  # ip+port
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = config_dict.get('wechaty_token') or ''  # uuid
    with open('cfg.ini', 'w') as configfile:
        config.write(configfile)
