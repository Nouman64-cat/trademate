import os
from dotenv import load_dotenv

load_dotenv()

# ── General Config ────────────────────────────────────────────────────────────
BASE_URL = "https://tipp.gov.pk"
DATA_DIR = os.getenv("DATA_DIR", "data")

# ── Scraping Parameters ───────────────────────────────────────────────────────
TIMEOUT = 25
MAX_RETRIES = 6
DELAY_MIN = 0.3
DELAY_MAX = 0.9
MAX_WORKERS = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://tipp.gov.pk/index.php?r=tradeInfo/index",
}

# ── Proxy List ────────────────────────────────────────────────────────────────
PROXY_LIST = [
    "31.58.29.91:6057:fmnakanp:d0gt52m0eosu",
    "45.39.13.51:5488:fmnakanp:d0gt52m0eosu",
    "154.30.1.72:5388:fmnakanp:d0gt52m0eosu",
    "103.47.53.104:8402:fmnakanp:d0gt52m0eosu",
    "45.43.64.157:6415:fmnakanp:d0gt52m0eosu",
    "45.67.0.18:6454:fmnakanp:d0gt52m0eosu",
    "206.206.64.125:6086:fmnakanp:d0gt52m0eosu",
    "92.112.137.206:6149:fmnakanp:d0gt52m0eosu",
    "104.252.44.39:5969:fmnakanp:d0gt52m0eosu",
    "31.59.18.181:6762:fmnakanp:d0gt52m0eosu",
    "45.39.17.163:5586:fmnakanp:d0gt52m0eosu",
    "194.116.250.78:6536:fmnakanp:d0gt52m0eosu",
    "104.253.90.157:5577:fmnakanp:d0gt52m0eosu",
    "184.174.27.17:6240:fmnakanp:d0gt52m0eosu",
    "50.114.8.147:7132:fmnakanp:d0gt52m0eosu",
    "152.232.16.4:8555:fmnakanp:d0gt52m0eosu",
    "173.211.68.165:6447:fmnakanp:d0gt52m0eosu",
    "67.227.112.155:6195:fmnakanp:d0gt52m0eosu",
    "82.26.222.233:8045:fmnakanp:d0gt52m0eosu",
    "107.175.208.245:6186:fmnakanp:d0gt52m0eosu",
    "172.121.159.95:5255:fmnakanp:d0gt52m0eosu",
    "193.239.176.126:5532:fmnakanp:d0gt52m0eosu",
    "104.222.187.80:6204:fmnakanp:d0gt52m0eosu",
    "107.175.56.208:6481:fmnakanp:d0gt52m0eosu",
    "185.15.178.211:5895:fmnakanp:d0gt52m0eosu",
    "82.22.253.245:8103:fmnakanp:d0gt52m0eosu",
    "104.143.244.78:6026:fmnakanp:d0gt52m0eosu",
    "45.249.59.232:6208:fmnakanp:d0gt52m0eosu",
    "46.203.202.35:5981:fmnakanp:d0gt52m0eosu",
    "82.22.235.175:6981:fmnakanp:d0gt52m0eosu",
    "104.143.226.135:5738:fmnakanp:d0gt52m0eosu",
    "184.174.44.162:6588:fmnakanp:d0gt52m0eosu",
    "108.165.227.252:5493:fmnakanp:d0gt52m0eosu",
    "23.109.232.99:6019:fmnakanp:d0gt52m0eosu",
    "104.253.180.44:6457:fmnakanp:d0gt52m0eosu",
    "191.101.41.77:6149:fmnakanp:d0gt52m0eosu",
    "191.101.181.234:6987:fmnakanp:d0gt52m0eosu",
    "94.177.49.246:6262:fmnakanp:d0gt52m0eosu",
    "206.83.131.230:5606:fmnakanp:d0gt52m0eosu",
    "136.0.103.151:5852:fmnakanp:d0gt52m0eosu",
]

# ── AWS S3 Config ─────────────────────────────────────────────────────────────
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID_MANUAL")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY_MANUAL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
