""" Utilities to get archived cmc info from our own mongo database """

import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

endpoint = "https://api.telegram.org/bot{BOT_TOKEN}/{METHOD_NAME}"
postmsg_str = endpoint.format(BOT_TOKEN=BOT_TOKEN, METHOD_NAME="sendMessage")


class FormattedCap:
    def __init__(self, label, total_market, val, source="cap") -> None:

        if source == "cap":
            self.cap = val
            self.cap_str = str(round(val / 1e9, 2)) + "B"

        elif source == "dominance":
            self.cap = val * total_market / 100
            self.cap_str = str(round(val * total_market / 1e11, 2)) + "B"

        self.perc_str = str(round((self.cap / total_market * 100), 2)) + "%"

        self.rep_str = label + " " + self.cap_str + " " + self.perc_str


def get_cmc_stats(mongo=None):

    """A function to grab the latest stats from our mongo collection"""

    wanted = [
        "btc_dominance",
        "eth_dominance",
        "quote",
    ]

    quote_wanted = [
        "altcoin_market_cap",
        "altcoin_volume_24h",
        "defi_market_cap",
        "stablecoin_market_cap",
        "total_market_cap",
        "total_volume_24h",
    ]

    last = mongo["archive"].marketCap.find_one(
        {"$query": {}, "$orderby": {"last_updated": -1}}, projection=wanted
    )

    inner = last.pop("quote")["USD"]
    last.pop("_id")

    for label in quote_wanted:
        last[label] = inner[label]

    return last


def make_graph(stats):

    total_cap = stats["total_market_cap"]

    btc = FormattedCap("BTC", total_cap, stats["btc_dominance"], source="dominance")
    eth = FormattedCap("ETH", total_cap, stats["eth_dominance"], source="dominance")
    defi = FormattedCap("DEFI", total_cap, stats["defi_market_cap"])
    stable = FormattedCap("STBL", total_cap, stats["stablecoin_market_cap"])
    alt = FormattedCap("ALT", total_cap, stats["altcoin_market_cap"] - eth.cap - stable.cap)

    plt.pie(
        np.array([btc.cap, eth.cap, alt.cap, stable.cap]),
        labels=[
            btc.rep_str,
            eth.rep_str,
            alt.rep_str,
            stable.rep_str,
        ],
        colors=["orange", "blue", "purple", "green"],
    )

    fname = "chart_{}.png".format(datetime.strftime(datetime.now(), "%Y%m%d%H%M%S"))
    fname = os.path.join("imgs", fname)

    plt.savefig(fname)
    make_room("imgs")
    return fname


def make_room(folder, limit=5):
    """clears old images out of the img folder"""
    fnames = os.listdir(folder)
    if len(fnames) > limit:
        for fname in sorted(fnames)[:-limit]:
            os.remove(os.path.join(folder, fname))


if __name__ == "__main__":
    stats = get_cmc_stats()
    make_graph(stats)
