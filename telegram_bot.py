import logging

from telegram.error import Unauthorized
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

import corona
import user
from config import get_config

logger = logging.getLogger(__name__)

_updater: Updater


def _invalid(update, context):
    reply_text = "Sorry, I don't understand.\n"
    reply_text += "Try /help to see the list of available commands."

    update.message.reply_text(reply_text)


def _help(update, context):
    reply_text = "You can subscribe to cities or areas for which you will get notifications about the current corona incidence value and more."
    reply_text += "\n"
    reply_text += "You will get updates as soon as they are available. Mostly, the data is updated during the night. It's likely that you will receive messages while you are sleeping ;-). if you are a light sleeper, you may mute the bot."

    reply_text += "\n\n\n"
    reply_text += "List of available commands:\n\n"

    reply_text += "/search <name>\n"
    reply_text += "Searches for the given city or area.\n"
    reply_text += "Example: /search München"
    reply_text += "\n\n"

    reply_text += "/sub <ID>\n"
    reply_text += "Subscribes to the given city or area using the specified ID.\n"
    reply_text += "Example: /sub 224"
    reply_text += "\n\n"

    reply_text += "/info\n"
    reply_text += "Sends you information about the incidence value of the last 7 days per 100.000 inhabitants and other corona values/statistics for your subscribed cities and areas."
    reply_text += "Example: /info"
    reply_text += "\n\n"

    reply_text += "/remove <ID>\n"
    reply_text += "Removes a city or an area from the subscriptions by using the corresponding ID.\n"
    reply_text += "Example: /remove 224"
    reply_text += "\n\n"

    reply_text += "/delete\n"
    reply_text += "Deletes all subscriptions.\n"
    reply_text += "Example: /delete"
    reply_text += "\n\n"

    reply_text += "/help\n"
    reply_text += "Prints this text.\n"
    reply_text += "Example: /help"
    reply_text += "\n\n"

    reply_text += "/start\n"
    reply_text += "Prints this text.\n"
    reply_text += "Example: /start"
    reply_text += "\n\n"

    reply_text += "\n"
    reply_text += "How to use this bot:\n"
    reply_text += "1. Search for a city or an area: /search <name>\n"
    reply_text += "2. Subscribe to a city or an area: /sub <ID>\n"
    reply_text += "3. You can manually retrieve all information (current corona incidence value and more) by using /info. Otherwise, you will get a message automatically as soon as the data has been uupdated."

    update.message.reply_text(reply_text)


def _start(update, context):
    update.message.reply_text(
        "Hi! I'm Corona Inzidenz Updater. I will send you messages about the current incidence value for cities/areas you are interested in.")
    _help(update, context)


def _search(update, context):
    if len(context.args) == 0:
        update.message.reply_text("Please enter a name of a city or an area to search for. E.g.: /search München")
        return

    search_city = " ".join(context.args)

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
    if len(context.args) == 0:
        update.message.reply_text(
            "Please enter a ID of a subscribed city or an area to unsubscribe for. E.g.: /remove 224")
        return

    reply_text = ""

    chat_id = update.message.chat_id
    for city_key in context.args:
        if not user.remove_city(city_key, chat_id):
            reply_text += "ID '{}' doesn't exist. Use the ID given by /info. E.g.: /remove 234\n".format(city_key)
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
    if len(context.args) == 0:
        update.message.reply_text("Please enter a ID of a city or an area to subscribe for. E.g.: /sub 224")
        return

    reply_text = ""

    chat_id = update.message.chat_id
    for city_key in context.args:
        if not user.add_city(city_key, chat_id):
            reply_text += "ID '{}' doesn't exists. Use the ID given by /search. E.g.: /sub 224\n".format(city_key)
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
        try:
            _updater.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        except Unauthorized as e:
            print("{}: {}".format(chat_id, str(e)))
    else:
        raise NotImplementedError("Initialize this module first!")


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
    dp.add_handler(MessageHandler(Filters.text & ~Filters.update.edited_message, _invalid))


def poll():
    _updater.start_polling()
    _updater.idle()
