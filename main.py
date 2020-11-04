import logging
import threading
import time

import schedule

logger = logging.getLogger(__name__)


def main():
    from argparse import ArgumentParser, ArgumentTypeError, ArgumentError

    def _check_positive(value):
        try:
            ivalue = int(value)
        except Exception:
            raise ArgumentTypeError("%s must be a number." % value)
        if ivalue <= 0:
            raise ArgumentTypeError("%s must be > 0." % value)
        return ivalue

    def _check_configuration_file(value):
        import json
        if not os.path.isfile(value):
            raise ArgumentError(value, "Is not a file or doesn't exist.")
        # TODO: Check JSON against schema.
        if value:
            with open(value, "r") as f:
                return json.load(f)

    parser = ArgumentParser()
    parser.add_argument("-config", "--c", type=_check_configuration_file,
                        help="A configuration file to use.")
    parser.add_argument("-corona_update_interval", "--cui", type=_check_positive, default=1,
                        help="The interval in hours how often the corona data should be updated. Default is every hour.")

    args = parser.parse_args()

    if args.c:
        import config
        config._config = args.c

    start(args.cui)


def start(corona_update_interval):
    import telegram_bot
    import corona
    import notification

    # Set up telegram, corona can use it.
    telegram_bot.init()

    corona._update_callback = notification.notify_users
    corona.check_update()

    th = threading.Thread(target=_schedule_jobs, args=(corona_update_interval, corona.check_update))
    th.start()

    # Infinite loop
    telegram_bot.poll()


def _schedule_jobs(corona_update_interval, corona_update_interval_function):
    schedule.every(corona_update_interval).hours.do(corona_update_interval_function)
    while 1:
        schedule.run_pending()
        time.sleep(60)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import os

    logging.basicConfig(
        # filename='HISTORYlistener.log',
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    main()
