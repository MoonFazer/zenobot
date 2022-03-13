""" a collection of miscellaneous utilities """

from colorama import Fore, Style
from pandas import DataFrame

colours = {
    "red": Fore.RED,
    "cyan": Fore.CYAN,
    "magenta": Fore.MAGENTA,
    "yellow": Fore.YELLOW,
    "green": Fore.LIGHTGREEN_EX,
    "default": Fore.RESET,
}


def cprint(colour, *obj):
    if colour in list(colours.keys()):
        print(colours[colour] + " ".join([str(i) for i in obj]) + Style.RESET_ALL)
    else:
        print(colours["default"] + " ".join([str(i) for i in obj]) + Style.RESET_ALL)


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
        DataFrame(rows)
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
