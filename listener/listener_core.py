"""
listener_core.py

This class allows regular functions that take in a msg and user id adn return a function
to be registered as a bot command in the updater

"""

import os

from dotenv import load_dotenv
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.updater import Updater
from telegram.update import Update
from utils.connection import get_connections


class CommandRegistry(Updater):
    def __init__(self) -> None:
        load_dotenv()
        self.BOT_TOKEN = os.environ.get("BOT_TOKEN")
        super().__init__(self.BOT_TOKEN, use_context=True)

    def register(self, call_slug, fn, **conns):
        """
        Registers a function with the updater

        takes:
            call_slug - the word we want our telegram users to use when calling the command
            fn - function we wish to register (returns text)

        returns:
            None
        """

        def new_command(update: Update, context: CallbackContext):

            kwargs = {
                "in_msg": update.message.text,
                "usr_id": update.effective_user.id,
                "first_name": update.effective_user.first_name,
            }

            for conn_name in conns:
                kwargs.update({conn_name: get_connections(conn_name, *conns[conn_name])})

            ret = fn(**kwargs)

            if isinstance(ret, list):
                for part in ret:
                    update.message.reply_text(part)
            else:
                update.message.reply_text(ret)

        self.dispatcher.add_handler(CommandHandler(call_slug, new_command))

        return None

    def bulk_register(self, commands):
        """unpacks a dict of connection requests and registers them all"""
        for entry in commands:
            self.register(entry, commands[entry]["fn"], **commands[entry]["conns"])

    def add_unknown_handlers(self):
        self.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
        self.dispatcher.add_handler(MessageHandler(Filters.command, unknown))
        self.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))


def unknown(update: Update, context: CallbackContext):
    """function to deal with unkown commands"""
    update.message.reply_text("Sorry '%s' is not a valid command" % update.message.text)


def unknown_text(update: Update, context: CallbackContext):
    """function to deal with unrecognised text"""
    update.message.reply_text("Sorry I can't recognise you, you said '%s'" % update.message.text)
