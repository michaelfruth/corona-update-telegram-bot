from corona_labels import *


class TelegramBotMessage:
    def __init__(self):
        self._texts: list = []
        self._html: bool = False

    def add(self, text, newlines_before=0, newlines_after=0):
        if isinstance(text, TelegramBotMessage):
            if text._html:
                self._html = True
            text = str(text)
        return self.newline(newlines_before)._add(text, is_html=False).newline(newlines_after)

    def _add(self, text, is_html=True):
        if is_html:
            self._texts.append(text)
        else:
            self._texts.append(self.html_escape(text))
        return self

    def newline(self, count=1):
        self._texts.append("\n" * count)
        return self

    def tab(self, count=1):
        self._texts.append("\t" * count)
        return self

    def newline_tab(self):
        return self.newline().tab()

    def underline(self, text):
        self._html = True
        return self.add("<u>" + text + "</u>")

    def bold(self, text):
        self._html = True
        return self._add("<b>" + self.html_escape(text) + "</b>")

    def italic(self, text):
        self._html = True
        return self._add("<i>" + self.html_escape(text) + "</i>")

    def strikethrough(self, text):
        self._html = True
        return self._add("<s>" + self.html_escape(text) + "</s>")

    def code(self, text):
        self._html = True
        return self._add("<code>" + self.html_escape(text) + "</code>")

    def pre(self, text):
        self._html = True
        return self._add("<pre>" + self.html_escape(text) + "</pre>")

    def start_pre(self):
        self._html = True
        self._add("<pre>")
        return self

    def end_pre(self):
        self._html = True
        self._texts.append("</pre>")
        return self

    def html_escape(self, text):
        return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

    def __str__(self):
        return "".join(self._texts)


def short_city_info(data) -> TelegramBotMessage:
    return TelegramBotMessage() \
        .add("ID: ").bold(data[C_OBJECT_ID]).add(" - {} ({})".format(data[C_CITY_AREA], data[C_CITY_AREA_DESCRIPTION]))


def full_info(data) -> TelegramBotMessage:
    if not isinstance(data, list):
        data = [data]

    sorted_data = sorted(data, key=lambda x: x[C_CITY_AREA])

    message = TelegramBotMessage()

    states_info = full_states_info(sorted_data)
    message.add(states_info).newline(2)

    message.underline("Cities/Areas").newline()
    for data in sorted_data:
        message.add(full_city_info(data)).newline(2)

    landscape_quick_info = city_landscape_quick_info(sorted_data)
    message.add(landscape_quick_info)

    return message


def city_landscape_quick_info(datas) -> TelegramBotMessage:
    cities_and_cases7 = [("{} ({})".format(data[C_CITY_AREA], data[C_CITY_AREA_DESCRIPTION]),
                          "{:.2f}".format(data[C_CASES7_PER_100K])
                          ) for data in datas]

    longest_city_name = max([len(city_cases7[0]) for city_cases7 in cities_and_cases7])
    longest_cases7 = max([len(city_cases7[1]) for city_cases7 in cities_and_cases7])

    message = TelegramBotMessage()

    message.underline("Quick overview").add(" (use landscape mode):").newline()

    message.add("_" * (longest_city_name + longest_cases7 + 5)).newline()
    message.start_pre()

    for city, cases7 in cities_and_cases7:
        city = _fill_whitespace(city, longest_city_name)
        cases7 = _fill_whitespace(cases7, longest_cases7, left=True)

        message.add("|{} | {}|".format(city, cases7)).newline()

    message.add("-" * (longest_city_name + longest_cases7 + 5))
    message.end_pre()

    return message


def _fill_whitespace(value, length, left=False):
    if len(value) < length:
        if left:
            return (" " * (length - len(value))) + value
        return value + " " * (length - len(value))
    elif len(value) > length:
        raise ValueError("{} has more than {} characters.".format(value, length))
    return value


def full_city_info(data) -> TelegramBotMessage:
    message = TelegramBotMessage()

    message.bold(data[C_CITY_AREA]).add(" ({}) - (ID: {})".format(data[C_CITY_AREA_DESCRIPTION], data[C_OBJECT_ID])) \
        .newline_tab()
    message.add("Cases last 7 days per 100k: ").bold("{:.2f}".format(data[C_CASES7_PER_100K])).newline_tab()
    message.add("Cases: {}".format(data[C_CASES])).newline_tab()
    message.add("Last update: {}".format(data[C_LAST_UPDATE]))

    return message


def full_states_info(datas) -> TelegramBotMessage:
    states = set([(d[C_STATE], d[C_CASES7_BL_PER_100K]) for d in datas])

    message = TelegramBotMessage()

    message.underline("States").add(" - cases last 7 days per 100k:").newline().newline_tab()
    message.add("\n\t".join(["{}: {:.2f}".format(*state) for state in states]))

    return message
