from redislite import Redis
import logging
from config import get_config

_redis_instances = {}

logger = logging.getLogger(__name__)


def _get_redis_instance(filename):
    import os

    db_dir = get_config()["databaseDirectory"]
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)

    filename = db_dir + "/" + filename
    if filename not in _redis_instances:
        _redis_instances[filename] = Redis(filename, decode_responses=True)
    return _redis_instances[filename]


class RedisDB():
    def __init__(self, db_filename, namespace):
        redis_connection = _get_redis_instance(db_filename)
        self.redis_connection: Redis = redis_connection
        self.namespace = namespace

    def exists(self, key):
        result = self.redis_connection.exists(self._ns_key(key))
        logger.debug("EXISTS: {} - {}".format(self._ns_key(key), result))
        return result

    def hexists(self, key, name):
        result = self.redis_connection.hexists(name, self._ns_key(key))
        logger.debug("EXISTS: {} | {} - {}".format(name, self._ns_key(key), result))
        return result

    def keys(self):
        result = self.redis_connection.keys()
        logger.debug("KEYS: - {}".format(result))
        return result

    def get(self, key):
        result = self.redis_connection.get(self._ns_key(key))
        logger.debug("GET: {} - {}".format(self._ns_key(key), result))
        return result

    def hget(self, key, name):
        result = self.redis_connection.hget(name, self._ns_key(key))
        logger.debug("GET: {} | {} - {}".format(name, self._ns_key(key), result))
        return result

    def set(self, key, value):
        result = self.redis_connection.set(self._ns_key(key), value)
        logger.debug("SET: {} | {} - {}".format(self._ns_key(key), value, result))
        return result

    def hset(self, key, value, name):
        result = self.redis_connection.hset(name, self._ns_key(key), value)
        logger.debug("HSET: {} | {} | {} - {}".format(name, self._ns_key(key), value, result))
        return result

    def hgetall(self, name):
        result = self.redis_connection.hgetall(name)
        logger.debug("HGETALL: {} - {}".format(name, result))
        return result

    def delete(self, key):
        result = self.redis_connection.delete(self._ns_key(key))
        logger.debug("DEL: {} - {}".format(self._ns_key(key), result))
        return result

    def sadd(self, key, value):
        result = self.redis_connection.sadd(self._ns_key(key), value)
        logger.debug("SADD: {} | {} - {}".format(self._ns_key(key), value, result))
        return result

    def srem(self, key, value):
        result = self.redis_connection.srem(self._ns_key(key), value)
        logger.debug("SREM: {} | {} - {}".format(self._ns_key(key), value, result))
        return result

    def smembers(self, key):
        result = self.redis_connection.smembers(self._ns_key(key))
        logger.debug("SMEMBERS: {} - {}".format(key, result))
        return result

    def _ns_key(self, key):
        if str(key).startswith(self.namespace + ":"):
            return key
        return "{}:{}".format(self.namespace, key)

    def remove_namespace(self, key):
        if str(key).startswith(self.namespace + ":"):
            return key[len(self.namespace + ":"):]
        return key


def get_pure_db_key(key):
    return key.split(":")[-1]
