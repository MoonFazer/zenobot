import itertools

import pandas as pd
import polars as pl
import pyarrow
from common.connection import get_connections


def get_active_range(market, last_agg_price):

    """left as pandas due to insignificant speed increase"""

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


def to_user_catalog(records, use_polars=False):
    """takes a dict and returns polars/pandas df"""

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
                    }
                )
    new = (
        pl.DataFrame(rows)
        .groupby(
            [
                "market",
                "agg_type",
                "agg_unit",
                "agg_perc",
            ],
        )
        .agg([pl.col("TGUsername").list(), pl.col("TGChatID").list()])
    )
    new.with_column(pl.lit(0.0).alias("count"))
    new.with_column(pl.lit(0.0).alias("cusum_count"))
    new.with_column(pl.lit(0.0).alias("last_agg_price"))

    if use_polars:
        return new
    else:
        return new.to_pandas()
