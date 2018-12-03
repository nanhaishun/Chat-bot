import yaml

def read_mysql_config():
    with open("./rasa_core/configs/config-dev.yml", "r") as f:
        yaml_load = yaml.load(f.read())
        MYSQL_CONF = yaml_load['MYSQL_CONF'][0]
        return MYSQL_CONF


def read_redis_config():
    with open("./rasa_core/configs/config-dev.yml", "r") as f:
        yaml_load = yaml.load(f.read())
        REDIS_CONF = yaml_load['REDIS_CONF'][0]
        return REDIS_CONF


def read_api_config():
    with open("./rasa_core/configs/config-dev.yml", "r") as f:
        yaml_load = yaml.load(f.read())
        API_CONF = yaml_load['API_CONF'][0]
        return API_CONF