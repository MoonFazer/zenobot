import os

from dotenv import load_dotenv
from pymongo import MongoClient


class Mongo(MongoClient):
    """
    Really, the purpose of this class is just to hide the conn string because it is quite ugly
    """

    def __init__(self, db_name="cusum") -> None:

        load_dotenv()
        ATLAS_USER = os.environ.get("ATLAS_USER")
        ATLAS_PASSWD = os.environ.get("ATLAS_PASSWD")

        super().__init__(
            "mongodb+srv://"
            + ATLAS_USER
            + ":"
            + ATLAS_PASSWD
            + "@moonfazer.p0pd0.mongodb.net/"
            + db_name
            + "?retryWrites=true&w=majority"
        )
