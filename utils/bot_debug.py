""" a set of functions to relay debug messages to a specific person through telegram """

import os

import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_ADMIN = os.environ.get("BOT_ADMIN")

endpoint = "https://api.telegram.org/bot{BOT_TOKEN}/{METHOD_NAME}"
postmsg_str = endpoint.format(BOT_TOKEN=BOT_TOKEN, METHOD_NAME="sendMessage")


def send_notif(registry):
    for i in [x for x in list(registry.keys()) if x != -1]:
        resp = requests.post(postmsg_str, data={"chat_id": i, "text": registry[i]}).json()


def send_crash_report(e):
    resp = requests.post(
        postmsg_str,
        data={
            "chat_id": BOT_ADMIN,
            "text": "BOT CRASH: error message reads: {}".format(e),
        },
    ).json()


def send_live_report():
    resp = requests.post(
        postmsg_str,
        data={
            "chat_id": BOT_ADMIN,
            "text": "BOT LIVE: Back up and running.",
        },
    ).json()


if __name__ == "__main__":
    registry = {BOT_ADMIN: "test message"}
    send_notif(registry)
