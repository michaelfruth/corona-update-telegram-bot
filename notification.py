import corona
import telegram_bot
import user
import logging

logger = logging.getLogger(__name__)


def notify_users():
    user_ids = user.users()
    for user_id in user_ids:
        cities = user.all_cities(user_id)
        info = corona.full_info(cities)

        logger.debug("Notifying user: {}".format(user_id))
        telegram_bot.send_message(user_id, info)
