import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import corona
import user
from config import get_config

logger = logging.getLogger(__name__)

_updater: Updater


def _help(update, context):
    reply_text = "How to use this bot:\n\n"

    reply_text += "Add a city or an area:\n"
    reply_text += "1. Search for a city or an area: /search <city or area> (e.g.: /search Berlin)\n"
    reply_text += "2. Subscribe to a city or an area: /sub <ID of city/area> (e.g.: /sub 233)\n"
    reply_text += "The ID is given by /search\n\n"

    reply_text += "You can list your subscribed areas/cities through /info\n\n"

    reply_text += "You get notified automatically about the corona information of your added cities/areas as soon as the data has been updated."
    update.message.reply_text(reply_text)


def _start(update, context):
    update.message.reply_text("Hi! Corona Inzidenz Updater.")
    _help(update, context)


def _search(update, context):
    search_city = " ".join(context.args)
    if len(search_city) == 0:
        update.message.reply_text("Please enter a name of a city or an area to search for. E.g.: /search Berlin")
        return

    found_cities = corona.find_city(search_city)
    if len(found_cities) == 0:
        update.message.reply_text("No cities or areas found for '{}'".format(found_cities))
        return

    found_cities.sort(key=lambda d: d[corona.C_CITY_AREA])

    cities_formatted = "\n".join([corona.short_city_info(data) for data in found_cities])

    reply_text = "Cities and areas found:\n" \
                 "\n" \
                 "{}\n" \
                 "\n" \
                 "Please use '/sub &lt;ID&gt;' to subscribe to a city or an area.".format(cities_formatted)

    update.message.reply_html(reply_text)


def remove(update, context):
    reply_text = ""

    chat_id = update.message.chat_id
    for city_key in context.args:
        if not user.remove_city(city_key, chat_id):
            reply_text += "ID '{}' doesn't exists. Use the ID given by /info. E.g.: /remove 234\n".format(city_key)
        else:
            reply_text += "ID '{}' successfully removed.\n".format(city_key)

    update.message.reply_text(reply_text)


def _delete(update, context):
    chat_id = update.message.chat_id

    if user.delete(chat_id):
        reply_text = "Deleted all of your data. You will no longer receive notifications.\n"
        reply_text += "You can turn the bot back on by sending /start.\n\n"
        reply_text += "Stay safe! Bye bye."

        update.message.reply_text(reply_text)
    else:
        update.message.reply_text("You didn't subscribe to any cities/areas. There is no data to delete.")


def _add(update, context):
    reply_text = ""

    chat_id = update.message.chat_id
    for city_key in context.args:
        if not user.add_city(city_key, chat_id):
            reply_text += "ID '{}' doesn't exists. Use the ID given by /search. E.g.: /sub 234\n".format(city_key)
        else:
            reply_text += "ID '{}' successfully added.\n".format(city_key)

    update.message.reply_text(reply_text)


def _info(update, context):
    chat_id = update.message.chat_id
    cities = user.all_cities(chat_id)

    if len(cities) == 0:
        reply_html = "No cities or areas are added yet."
    else:
        reply_html = corona.full_info(cities)

    update.message.reply_html(reply_html)


def send_message(chat_id, message):
    if _updater:
        _updater.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)


def init():
    global _updater
    _updater = Updater(get_config()["telegramToken"], use_context=True)

    dp = _updater.dispatcher
    dp.add_handler(CommandHandler("start", _start, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("delete", _delete, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("help", _help, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("search", _search, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("info", _info, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("sub", _add, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler("remove", remove, filters=~Filters.update.edited_message))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.update.edited_message, _help))


def poll():
    _updater.start_polling()
    _updater.idle()
