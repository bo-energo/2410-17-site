import os
from dotenv import load_dotenv


load_dotenv()

LASER_SERVICE = os.getenv("LASER_SERVICE")
