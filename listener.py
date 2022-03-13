""" This script adds all command functions to a command registry and begins polling chats """


import yaml

from listener_core import CommandRegistry

with open("paragraphs.yaml", "r") as stream:
    try:
        long_texts = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        print(e)


def start(*args, **kwargs):
    return long_texts["start"].format(**kwargs)


def help(*args, **kwargs):
    return long_texts["help"]


def description(*args, **kwargs):
    return [long_texts["description_0"], long_texts["description_1"]]


def main():

    bot = CommandRegistry()

    commands = {"start": start, "help": help, "description": description}

    for entry in commands:
        bot.register(entry, commands[entry])

    bot.add_unknown_handlers()
    bot.start_polling()


if __name__ == "__main__":
    main()
