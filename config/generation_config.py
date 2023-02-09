import configparser
import os

config = configparser.ConfigParser()

config["env"] = {'env': 'LOCAL'}
""" 本地redis配置 """
config["REDIS_LOCAL"] = {'URL': 'redis://localhost:6379/0',
                         'DECODE': True,
                         'ENCODING': 'utf-8',
                         'MAX_COLLECTIONS': 10,
                         'SOCKET_TIMEOUT': 5,
                         'SOCKET_CONNECT_TIMEOUT': 5
                         }
config["OPENAI_LOCAL"] = {'KEY': '',  # api-key
                          'ORGANIZATION': 'chensitong'  # api-user
                          }
config["TELEGRAM_LOCAL"] = {'TOKEN': '',  # bot-token
                            }

config["QWEATHER_LOCAL"] = {'KEY': '' ,# 和风天气api-Key
                            'LOCATION-PATH': 'https://geoapi.qweather.com/v2/city/lookup',
                            'WEATHER-PATH': 'https://devapi.qweather.com/v7/weather/3d'
                            }


def generation_config():
    os.environ['WECHATY_PUPPET_SERVICE_ENDPOINT'] = ''  # ip+port
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = ''  # uuid
    with open('cfg.ini', 'w') as configfile:
        config.write(configfile)
