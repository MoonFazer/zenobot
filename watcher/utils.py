import itertools

import pandas as pd
from common.connection import get_connections


def get_active_range(market, last_agg_price):

    """finds the active range of a crypto with pre-established support-resistance levels"""

    mongo = get_connections("mongo", "cusum")
    ranges_db = mongo["archive"].keyPriceLevels

    market = market.split(f"/")[0]
    price_list = [x for x in ranges_db.find({"name": market})][0]["levels"]
    price_list = [float(x) for x in price_list]
    low_bound = max([x for x in price_list if x < last_agg_price])
    high_bound = min([x for x in price_list if x >= last_agg_price])
    return (low_bound, high_bound)


def reg_keys(entries):
    """creates a dict of empty strings by unpacking a counter dictionary"""
    big_set = set(itertools.chain(*entries))
    return {key: "" for key in big_set}


def to_user_catalog(records):

    rows = []
    for record in records:
        for entry in record["watchList"]:
            for agg in entry["aggs"]:
                agg_type, agg_unit, agg_perc = agg.split("_")
                rows.append(
                    {
                        "TGUsername": record["TGUsername"],
                        "TGChatID": record["TGChatID"],
                        "market": entry["market"],
                        "agg_type": agg_type,
                        "agg_unit": float(agg_unit),
                        "agg_perc": float(agg_perc),
                        "count": 0.0,
                        "cusum_count": 0.0,
                        "last_agg_price": None,
                    }
                )
    return (
        pd.DataFrame(rows)
        .groupby(
            [
                "market",
                "agg_type",
                "agg_unit",
                "agg_perc",
            ],
            as_index=False,
        )
        .agg(
            users=("TGUsername", lambda x: list(set(x))),
            ids=("TGChatID", lambda x: list(set(x))),
            count=("count", lambda x: 0.0),
            cusum_count=("cusum_count", lambda x: 0.0),
            last_agg_price=("last_agg_price", lambda x: None),
        )
    )


if __name__ == "__main__":
    active = pd.DataFrame(
        [
            {"market": "BTC/USDT", "last_agg_price": 41500.00},
            {"market": "ETH/USDT", "last_agg_price": 2150.00},
        ]
    )
    active["get_range"] = active[["market", "last_agg_price"]].to_dict("records")
    active["range"] = active["get_range"].map(lambda x: get_active_range(**x))

    print(active)
