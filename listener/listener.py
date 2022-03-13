"""
This script adds all command functions to a command registry and begins polling chats

In order to register a new command, append it to the bot.bulk_register call while being sure
to specify which function the command should look for and which connections it will need.

For each connection, specify its optional arguments if need be.

"""

from listener.functions import *
from listener.listener_core import CommandRegistry

mongo_config = {"mongo": ["cusum"]}


def main():

    bot = CommandRegistry()

    bot.bulk_register(
        {
            "start": {"fn": start, "conns": {}},
            "help": {"fn": help, "conns": {}},
            "description": {"fn": description, "conns": {}},
            "future": {"fn": future, "conns": {}},
            "watchlist": {"fn": watchlist, "conns": mongo_config},
            "stats": {"fn": stats, "conns": mongo_config},
            # since add is an internal command it needs a different alias for the fn definition
            "add": {"fn": add_watch, "conns": mongo_config},
            "delete": {"fn": delete_watch, "conns": mongo_config},
        }
    )

    bot.add_unknown_handlers()
    bot.start_polling()


if __name__ == "__main__":
    main()
