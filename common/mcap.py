""" Utilities to get archived cmc info from our own mongo database """

import os

from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")

endpoint = "https://api.telegram.org/bot{BOT_TOKEN}/{METHOD_NAME}"
postmsg_str = endpoint.format(BOT_TOKEN=BOT_TOKEN, METHOD_NAME="sendMessage")


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
