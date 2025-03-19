import os
from dotenv import load_dotenv


load_dotenv()

LASER_SERVICE = os.getenv("LASER_SERVICE", "http://10.0.2.201:7200")
DIAG_GROUP_ID = os.getenv("DIAG_GROUP_ID")
_TIMESTAMP_BY_ASSET = {}
