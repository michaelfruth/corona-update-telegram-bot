import corona
import telegram_bot
import user
import logging

logger = logging.getLogger(__name__)


def notify_users():
    user_ids = user.users()
    for user_id in user_ids:
        cities = user.all_cities(user_id)
        info = ""
        for city_data in cities:
            info += corona.full_info(city_data)
            info += "\n\n"

        logger.debug("Notifying user: {}".format(user_id))
        telegram_bot.send_message(user_id, info)


def notify_user(user_id, datas):
    update = "Your update:\n\n"
    for data in datas:
        update += corona.full_info(data)
        update += "\n\n"

    telegram_bot.send_message(user_id, update)
