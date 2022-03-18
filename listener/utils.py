from common.msg_utils import validate_add_delete


def edit_watchlist(action, document, ticker, agg):
    """
    Takes a dict of a persons current watchlist and returns a dict with desired changes made.
    """
    existing_key = [x["market"] for x in document["watchList"] if x["market"] == ticker]

    if action == "add":
        if existing_key == []:
            document["watchList"].append({"market": ticker, "aggs": [agg]})
        else:
            for watch in document["watchList"]:
                if (watch["market"] == existing_key[0]) & (agg not in watch["aggs"]):
                    watch["aggs"].append(agg)

    elif action == "delete":

        if existing_key == []:
            pass
        else:
            for i in document["watchList"]:
                if i["market"] == existing_key[0]:
                    if agg in i["aggs"]:
                        i["aggs"].remove(agg)
                    if i["aggs"] == []:
                        document["watchList"].remove(i)
    return document


def add_delete(action=None, mongo=None, usr_id=None, usr_name=None, in_msg=None, **kwargs):
    """
    Allows a user to add/delete a watch to/from their watchlist
    """

    if validate_add_delete(in_msg):
        found_profile = [x for x in mongo["cusum"].watchList.find({"TGChatID": usr_id})]

        parts = in_msg.split(" ")
        ticker = parts[1]
        agg = parts[2]

        command = " ".join(parts[1:])

        if found_profile == []:
            if action == "add":
                mongo["cusum"].watchList.insert_one(
                    {
                        "TGUsername": usr_name,
                        "TGChatID": usr_id,
                        "watchList": [{"market": ticker, "aggs": []}],
                    }
                )
                return "You haven't got a watchlist yet. I've set one up and added {}".format(
                    command
                )

            elif action == "delete":
                return "You haven't got a watchlist yet. Set one up automatically by adding a watch via\n/new {ticker} {type}_{agg}_{filter_percentage}"
        else:
            entry = edit_watchlist(action, found_profile[0], ticker, agg)
            mongo["cusum"].watchList.replace_one({"TGChatID": usr_id}, entry)

            if action == "add":
                return "Added {}".format(command)
            elif action == "delete":
                return "Deleted {}".format(command)

    else:
        return "Sorry. '{}' is not valid. Schemata like 'BTC/USDT dollar_100000_1.5' would be valid.".format(
            in_msg
        )
