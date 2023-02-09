import configparser


def get_env():
    config = configparser.ConfigParser()
    config.read('cfg.ini')
    return config.get('env', 'env')


def collection_get(section, key):
    config = configparser.ConfigParser()
    config.read('cfg.ini')
    return config.get(section, key)
