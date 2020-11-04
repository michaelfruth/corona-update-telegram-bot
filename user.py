import logging

import corona
from redis_storage import RedisDB

logger = logging.getLogger(__name__)

_DATABSE_FILE = "user.db"
_redis_user_city = RedisDB(_DATABSE_FILE, "user_city")


def add_city(city_key, user_id):
    if corona.exists(city_key):
        _redis_user_city.sadd(user_id, city_key)
        return True
    else:
        return False


def users(plain_keys=True):
    if plain_keys:
        return [_redis_user_city.remove_namespace(key) for key in _redis_user_city.keys()]
    return _redis_user_city.keys()


def remove_city(city_key, user_id):
    return _redis_user_city.srem(user_id, city_key)


def delete(user_id):
    return _redis_user_city.delete(user_id)


def all_cities(user_id):
    city_keys = _redis_user_city.smembers(user_id)

    result = []
    for city_key in city_keys:
        data = corona.get_data(city_key)
        if data:
            result.append(data)
    return result
