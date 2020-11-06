import json
import logging
from difflib import SequenceMatcher

import requests

from redis_storage import RedisDB, get_pure_db_key

logger = logging.getLogger(__name__)

CORONA_API_URL = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID,BL,county,GEN,BEZ,last_update,cases7_per_100k,cases_per_100k,cases7_bl_per_100k,cases&returnGeometry=false&outSR=4326&f=json"
CORONA_UPDATE_API_URL = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID,last_update&returnGeometry=false&outSR=4326&f=json"

C_OBJECT_ID = "OBJECTID"
C_STATE = "BL"
C_COUNTY = "COUNTY"
C_CITY_AREA = "GEN"
C_CITY_AREA_DESCRIPTION = "BEZ"
C_LAST_UPDATE = "last_update"
C_CASES_PER_100K = "cases_per_100k"
C_CASES7_PER_100K = "cases7_per_100k"
C_CASES7_BL_PER_100K = "cases7_bl_per_100k"
C_CASES = "cases"

_DATABSE_FILE = "corona.db"
_redis_last_update = RedisDB(_DATABSE_FILE, "last_updated")
_redis_corona = RedisDB(_DATABSE_FILE, "corona")
_redis_corona_city_search = RedisDB(_DATABSE_FILE, "corona_city_search")

_update_callback = None


def check_update():
    respone = requests.get(CORONA_UPDATE_API_URL)
    data = json.loads(respone.text)

    if "features" in data:
        features = data["features"]
        for feature in features:
            if 'attributes' in feature:
                attributes = feature['attributes']

                stored_last_update = _redis_last_update.get(attributes[C_OBJECT_ID])
                if stored_last_update is None or str(stored_last_update) < attributes[C_LAST_UPDATE]:
                    logger.info("Found old data. Updating all data...")
                    _update_data()
                    break


def _update_data():
    respone = requests.get(CORONA_API_URL)
    data = json.loads(respone.text)

    if "features" in data:
        features = data["features"]
        for feature in features:
            if 'attributes' in feature:
                attributes = feature['attributes']
                object_id = attributes[C_OBJECT_ID]

                stored_last_update = _redis_last_update.get(object_id)
                if stored_last_update is None or str(stored_last_update) < attributes[C_LAST_UPDATE]:
                    logger.info("Update/Insert Data. ObjectId: {}".format(attributes[C_OBJECT_ID]))

                    # Update last updated
                    _redis_last_update.set(object_id, attributes[C_LAST_UPDATE])

                    # Store corona data
                    _redis_corona.set(object_id, json.dumps(attributes))

                    # Store corona data - hashed by first character of the city name
                    city_first_char = attributes[C_CITY_AREA][0].upper()
                    _redis_corona_city_search.sadd(city_first_char, object_id)
                else:
                    logger.info("Data up-to-date. ObjectId {}".format(attributes[C_OBJECT_ID]))

    if _update_callback is not None:
        _update_callback()


def find_city(name):
    if not name or not isinstance(name, str) or len(name) <= 0:
        raise ValueError("Invalid input for name: {}".format(name))

    name_upper = name.upper()

    potential_object_ids = _redis_corona_city_search.smembers(name_upper[0])

    matching_cities = []
    for object_id in potential_object_ids:
        corona_data = _redis_corona.get(object_id)

        if corona_data is None:
            continue

        corona_data = json.loads(corona_data)
        city_upper = corona_data[C_CITY_AREA].upper()

        if name_upper in city_upper or SequenceMatcher(None, name_upper, city_upper).ratio() >= 0.8:
            matching_cities.append(corona_data)

    return matching_cities


def get_data(object_id):
    corona_data = _redis_corona.get(object_id)
    if corona_data is None:
        return None

    return json.loads(corona_data)


def exists(object_id):
    return True if _redis_corona.exists(object_id) >= 1 else False


def short_city_info(data):
    return "ID: <b>{}</b> - {} ({})".format(data[C_OBJECT_ID], data[C_CITY_AREA], data[C_CITY_AREA_DESCRIPTION])


def full_info(data):
    if not isinstance(data, list):
        data = [data]

    sorted_data = sorted(data, key=lambda x: x[C_CITY_AREA])

    states_info = full_states_info(sorted_data)

    cities_info = "\n\n".join([full_city_info(d) for d in sorted_data])
    cities_info = "<u>Cities/Areas</u>:\n" + cities_info

    landscape_quick_info = city_landscape_quick_info(data)

    info = "{}\n\n{}\n\n{}".format(states_info, cities_info, landscape_quick_info)

    return info


def city_landscape_quick_info(datas):
    cities_and_cases7 = [("{} ({})".format(data[C_CITY_AREA], data[C_CITY_AREA_DESCRIPTION]),
                          "{:.2f}".format(data[C_CASES7_PER_100K])
                          ) for data in datas]

    longest_city_name = max([len(city_cases7[0]) for city_cases7 in cities_and_cases7])
    longest_cases7 = max([len(city_cases7[1]) for city_cases7 in cities_and_cases7])

    info = "_" * (longest_city_name + longest_cases7 + 5)
    info += "\n"
    for city, cases7 in cities_and_cases7:
        city = _fill_whitespace(city, longest_city_name)
        cases7 = _fill_whitespace(cases7, longest_cases7, left=True)
        info += "|{} | {}|".format(city, cases7)
        info += "\n"
    info += "-" * (longest_city_name + longest_cases7 + 5)

    info = "<u>Quick overview</u> (use landscape mode):\n<pre>{}</pre>".format(info)
    return info


def _fill_whitespace(value, length, left=False):
    if len(value) < length:
        if left:
            return (" " * (length - len(value))) + value
        return value + " " * (length - len(value))
    elif len(value) > length:
        raise ValueError("{} has more than {} characters.".format(value, length))
    return value


def full_city_info(data):
    info = "<b>{}</b> ({}) - (ID: {})".format(data[C_CITY_AREA], data[C_CITY_AREA_DESCRIPTION], data[C_OBJECT_ID])
    info += "\n"
    info += "\tCases last 7 days per 100k: <b>{:.2f}</b>".format(data[C_CASES7_PER_100K])
    info += "\n"
    info += "\tCases: {}".format(data[C_CASES])
    info += "\n"
    info += "\tLast update: {}".format(data[C_LAST_UPDATE])

    return info


def full_states_info(datas):
    states = set([(d[C_STATE], d[C_CASES7_BL_PER_100K]) for d in datas])

    info = "<u>States</u> - cases last 7 days per 100k:"
    info += "\n"
    info += "\n\t".join(["{}: {:.2f}".format(*state) for state in states])

    return info
