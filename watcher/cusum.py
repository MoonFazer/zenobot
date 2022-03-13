"""
The CUSUM watcher!

This keeps track of the cryptos as ticks come in and counts up to people's thresholds ready
to ping notifications or trade events!

"""

import itertools
import time
from datetime import datetime

import numpy as np
import pandas as pd
from exchanges.ftx_rest import ftx
from loguru import logger
from utils.bot_debug import *
from utils.connection import get_connections
from utils.misc import *


class CUSUM(ftx):
    def __init__(self, interval=10):
        """
        First, inherit the functions from the ftx module.
        Then, grab the newest version of the watchlists from mongo.
        Instantiate a cache of crypto prices.
        Find the price to start from - (initial conditions).
        Record the most recent transactions so we can make an accurate comparison first time around
        Get some stats for these txs.
        Instantiate the counter df.

        """
        super().__init__()
        self.interval = interval
        self.update_mongo_watchlist()

        self.cache = {
            market_name: {"txs": pd.DataFrame(), "last_id": None, "last_time": None}
            for market_name in self.counter["market"].unique()
        }

        now = datetime.now().timestamp() * 1000

        init_pulls = {}
        for market in list(self.cache.keys()):
            init_pulls[market] = self.pull_txs(market, now, extra=1000000000)

        for market in list(self.cache.keys()):
            self.cache[market]["txs"] = init_pulls[market]

        self._update_cache_stats()
        self.counter["last_agg_price"] = self.counter["market"].apply(
            lambda x: self.cache[x]["txs"]["price"].iloc[-1]
        )
        self.counter["hit"] = False

    def fill_price(self, entry):
        if entry["last_agg_price"] == 0.0:
            return self.cache[entry["market"]]["last_price"]
        else:
            return entry["last_agg_price"]

    def get_active_range(self, entry):

        self.mongo = get_connections("mongo", "cusum")
        ranges_db = self.mongo["archive"].keyPriceLevels

        entry["market"] = entry["market"].split(f"/")[0]
        price_list = [x for x in ranges_db.find({"name": entry["market"]})][0]["levels"]
        price_list = [float(x) for x in price_list]
        low_bound = max([x for x in price_list if x < entry["last_agg_price"]])
        high_bound = min([x for x in price_list if x >= entry["last_agg_price"]])
        return (low_bound, high_bound)

    def update_cache(self):

        """
        This pulls recent tick for the desired markets and calculates a few stats about them
        WARNING:
            - It does NOT update last price etc. That should be done after the counting step
        """

        now = round(datetime.now().timestamp() * 1000)

        pulls = {}
        for market in list(self.cache.keys()):
            pulls[market] = self.pull_txs(market, now)

        # these are in separate loops to decrease the time it takes to get data from all
        # the desired markets. The above loop should be quick as possible!
        for market in list(self.cache.keys()):

            self.cache[market]["txs"] = (
                pulls[market]
                .loc[pulls[market]["time"] >= self.cache[market]["last_time"]]
                .loc[pulls[market]["id"] > self.cache[market]["last_id"]]
                .copy()
            )

            self.cache[market]["txs"]["cum_tick"] = [
                x + 1 for x in range(len(self.cache[market]["txs"]))
            ]
            self.cache[market]["txs"]["cum_volume"] = self.cache[market]["txs"]["size"].cumsum()
            self.cache[market]["txs"]["cum_dollar"] = self.cache[market]["txs"]["dollar"].cumsum()

    def _update_cache_stats(self):
        for market in list(self.cache.keys()):
            if len(self.cache[market]["txs"]) > 0:
                self.cache[market]["last_time"] = self.cache[market]["txs"]["time"].iloc[-1]
                self.cache[market]["last_id"] = self.cache[market]["txs"]["id"].iloc[-1]
                self.cache[market]["last_price"] = self.cache[market]["txs"]["price"].iloc[-1]

    def update_counts(self):

        self.counter["info"] = self.counter[["market", "agg_type", "agg_unit"]].to_dict("records")
        self.counter["count"] = self.counter["count"] + self.counter["info"].map(
            self._increment_count
        )

        self.counter["recent_index"] = self.counter["info"].map(self._index_quants)
        self.counter["info"] = self.counter.to_dict("records")

        self.counter = pd.DataFrame([self.trickle(record) for record in self.counter["info"]])

        return 0

    def _increment_count(self, record):
        if len(self.cache[record["market"]]["txs"]) > 0:
            return (
                self.cache[record["market"]]["txs"]["cum_" + record["agg_type"]].iloc[-1]
                / record["agg_unit"]
            )
        else:
            return 0.0

    def _index_quants(self, record):
        subj = self.cache[record["market"]]["txs"][["cum_" + record["agg_type"], "price"]]
        return {x["cum_" + record["agg_type"]]: x["price"] for x in subj.to_dict("records")}

    def pull_txs(self, market, now, extra=0):
        pull_not_succeeded = True

        while pull_not_succeeded:
            try:
                pull = [
                    x["info"]
                    for x in self.fetch_trades(
                        market,
                        since=now
                        - 1000 * 60 * 2
                        - self.interval
                        - extra,  # get the last 2 minutes of trades every interval
                        until=now,
                    )
                ]
                pull_not_succeeded = False
            except Exception as e:
                send_crash_report(e)
                time.sleep(0.5)

        if len(pull) > 0:
            pull = pd.DataFrame(pull)
        else:
            pull = pd.DataFrame(
                columns=[
                    "id",
                    "price",
                    "size",
                    "side",
                    "liquidation",
                    "time",
                    "dollar_amount",
                ]
            )

        for label in ["price", "size"]:
            pull[label] = pull[label].astype(float)

        pull["id"] = pull["id"].map(int)
        pull["time"] = pull["time"].map(
            lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f+00:00")
        )

        pull["dollar"] = pull["size"] * pull["price"]

        return pull.sort_values(["time", "id"])

    def trickle(self, record):
        """
        this function 'trickles' counts into cusum counts then decides if the cusum limit was hit, updating the record
        """
        record["hit"] = False
        if len(record["recent_index"]) > 0:

            multiples = int(
                round(record["count"] // 1)
            )  # this is the number of aggregation points we need to make

            if multiples > 0:
                rem = round(record["count"] - multiples, 7)
                pos = [
                    max(record["recent_index"].keys()) - (rem + x) * record["agg_unit"]
                    for x in range(multiples)
                ]
                idxs = []
                for idx in pos:
                    try:
                        idxs.append(
                            max([x for x in list(record["recent_index"].keys()) if x <= idx])
                        )
                    except ValueError as e:
                        print("ERROR ESCAPED!")
                        idxs.append(False)

                for idx in sorted(idxs):
                    if idx:
                        record["cusum_count"] += (
                            abs(record["recent_index"][idx] / record["last_agg_price"] - 1) * 100
                        )
                        record["last_agg_price"] = record["recent_index"][idx]
                    else:
                        record["cusum_count"] += (
                            abs(
                                self.cache[record["market"]]["last_price"]
                                / record["last_agg_price"]
                                - 1
                            )
                            * 100
                        )
                        record["last_agg_price"] = self.cache[record["market"]]["last_price"]

                record["count"] = rem

            if record["cusum_count"] > record["agg_perc"]:
                record["hit"] = True
                record["cusum_count"] = record["cusum_count"] - record["agg_perc"] * (
                    record["cusum_count"] // record["agg_perc"]
                )

        return record

    def log_output(self):
        cprint(
            "cyan",
            "\n\n####################     {}     ####################\n".format(
                datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")
            ),
        )
        print("Last cycle: ")
        print(
            pd.DataFrame(
                list(
                    {
                        "market": market_name,
                        "tick": len(self.cache[market_name]["txs"]),
                        "dollar": self.cache[market_name]["txs"]["dollar"].sum(),
                        "volume": self.cache[market_name]["txs"]["size"].sum(),
                        "last_time": self.cache[market_name]["last_time"],
                        "last_id": self.cache[market_name]["last_id"],
                    }
                    for market_name in self.cache
                )
            )
        )
        cprint("green", "\nCounters:")
        cprint(
            "green",
            self.counter[
                [
                    "market",
                    "agg_type",
                    "agg_unit",
                    "agg_perc",
                    "count",
                    "cusum_count",
                    "last_agg_price",
                    "hit",
                ]
            ],
        )

    def reg_keys(self, entries):
        big_set = set(itertools.chain(*entries))
        return {key: "" for key in big_set}

    def send_pings(self):
        active = self.counter[self.counter["hit"] == True][
            ["ids", "market", "agg_type", "agg_unit", "agg_perc", "last_agg_price"]
        ]

        if len(active) > 0:
            with open("logfile.txt", "a+") as f:
                f.write(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f") + "\n")
                f.write(active.to_string() + "\n\n")

        registry = self.reg_keys(active["ids"].to_list())

        active["get_range"] = active[["market", "last_agg_price"]].to_dict("records")
        active["range"] = active["get_range"].map(self.get_active_range)

        active["msg"] = (
            active["market"]
            + "\n"
            + active["agg_unit"].astype(str)
            + " "
            + active["agg_type"]
            + "\n"
            + active["agg_perc"].astype(str)
            + "% filter hit\n@ $"
            + active["last_agg_price"].astype(str)
            + "\n\nActive range:\n"
            + active["range"].astype(str)
        )

        for row in active[["ids", "msg"]].to_dict("records"):
            for id in row["ids"]:
                registry[id] = registry[id] + "\n\n" + row["msg"]

        send_notif(registry)

    def main_loop(self):
        failed = False
        try:
            self.update_cache()
            self.update_counts()
            self.send_pings()
            self._update_cache_stats()
            self.log_output()
            self.update_mongo_watchlist()

            if failed:
                send_live_report()
                failed = False

        except Exception as e:
            failed = True
            send_crash_report(e)

    def update_mongo_watchlist(self):

        self.mongo = get_connections("mongo", "cusum")

        pull = to_user_catalog([x for x in self.mongo["cusum"].watchList.find({})])
        if hasattr(self, "counter"):
            old = self.counter[
                ["market", "agg_perc", "agg_type", "agg_unit", "users", "ids"]
            ].to_dict("records")
            new = pull[["market", "agg_perc", "agg_type", "agg_unit", "users", "ids"]].to_dict(
                "records"
            )
            if old != new:
                print("schema changed!")

                self.counter = self.counter.merge(
                    pull,
                    how="right",
                    on=["market", "agg_perc", "agg_type", "agg_unit"],
                    suffixes=["_old", "_new"],
                )
                self.counter.fillna(0.0, inplace=True)
                self.counter["users"] = self.counter["users_new"]
                self.counter["count"] = self.counter["count_old"]
                self.counter["cusum_count"] = self.counter["cusum_count_old"]
                self.counter["last_agg_price"] = self.counter["last_agg_price_old"]
                self.counter["ids"] = self.counter["ids_new"]
                self.counter = self.counter[
                    [
                        "market",
                        "users",
                        "agg_perc",
                        "agg_type",
                        "agg_unit",
                        "count",
                        "cusum_count",
                        "last_agg_price",
                        "ids",
                    ]
                ]

                self.fix_cache(self.counter["market"].unique())
        else:
            self.counter = pull

    def fix_cache(self, cache_list):
        now = int(datetime.now().timestamp() * 1000)
        for entry in self.cache:
            if entry not in cache_list:
                del self.cache[entry]

        for entry in set(cache_list):
            if entry not in list(self.cache.keys()):
                print(entry)
                self.cache[entry] = {"txs": self.pull_txs(entry, now, extra=1000000000)}
                self.cache[entry]["last_id"] = self.cache[entry]["txs"]["id"].iloc[-1]
                self.cache[entry]["last_time"] = self.cache[entry]["txs"]["time"].iloc[-1]
                self.cache[entry]["last_price"] = self.cache[entry]["txs"]["price"].iloc[-1]

                self.counter["last_agg_price"] = np.where(
                    self.counter["market"] == entry,
                    self.cache[entry]["last_price"],
                    self.counter["last_agg_price"],
                )

        self.counter["last_agg_price"] = self.counter[["market", "last_agg_price"]].to_dict(
            "records"
        )
        self.counter["last_agg_price"] = self.counter["last_agg_price"].map(self.fill_price)

    def run(self):

        # at the start, we update the cache as we need only uncached transactions later from which to aggregate
        self.update_cache()
        self._update_cache_stats()
        time.sleep(self.interval)

        while 1:
            time.sleep(self.interval - time.time() % self.interval)
            self.main_loop()


@logger.catch
def main():

    watcher = CUSUM(
        interval=10,
    )

    watcher.run()


if __name__ == "__main__":
    main()
