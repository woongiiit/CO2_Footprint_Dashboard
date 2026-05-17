import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent

load_dotenv(APP_DIR / ".env")

DATA_DIR = Path(
    os.getenv("DATA_DIR", str(PROJECT_ROOT / "datas" / "generated_datas_202505_202604"))
).resolve()
PROMPT_PATH = Path(os.getenv("PROMPT_PATH", str(APP_DIR / ".prompt"))).resolve()

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
HF_API_TIMEOUT = int(os.getenv("HF_API_TIMEOUT", "60"))
