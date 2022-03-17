"""
Set of utilities to

Turn data objects into neatly formatted telegram message packets
--or--
Validate entries from users

"""
import re


def build_watchlist_str(entry):
    """takes a watchlist entry and returns a neatly formatted string"""
    strn = ""
    for record in entry["watchList"]:
        strn = strn + "\n\n" + record["market"]
        for agg in record["aggs"]:
            strn = strn + "\n\t" + str(agg)
    return strn


def dict_to_msg(dict_):
    """takes a top-level dict and returns a neat string"""
    str_ = ""
    for entry in sorted(list(dict_.keys())):
        str_ = str_ + "\n" + entry + " : " + str(dict_[entry])
    return str_


def validate_add_delete(message_text):

    """ """

    if re.match(
        r"^(\/add\s|\/delete\s)[A-Za-z]{1,}\/[A-Za-z]{1,}\s(tick|volume|dollar)\_([0-9]+)(\.[0-9]+)?\_([0-9]+)(\.[0-9]+)?$",
        message_text,
    ):
        return True
    else:
        return False
