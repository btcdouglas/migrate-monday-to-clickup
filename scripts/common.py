import os, json, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_NORM = BASE_DIR / "data" / "normalized"
LOG_DIR = BASE_DIR / "data" / "logs"
STATE_DIR = BASE_DIR / "state"
DOWNLOADS_DIR = BASE_DIR / "downloads" / "assets"
CONFIG_DIR = BASE_DIR / "config"
for p in [DATA_RAW, DATA_NORM, LOG_DIR, STATE_DIR, DOWNLOADS_DIR, CONFIG_DIR]:
    p.mkdir(parents=True, exist_ok=True)

MONDAY_URL = "https://api.monday.com/v2"
CLICKUP_URL = "https://api.clickup.com/api/v2"
MONDAY_TOKEN = os.getenv("MONDAY_TOKEN", "")
CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN", "")

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default if default is not None else {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def append_log(name, message):
    with open(LOG_DIR / name, "a", encoding="utf-8") as f:
        f.write(message.rstrip() + "\n")

def monday_query(query, variables=None, retries=3, timeout=120):
    headers = {"Authorization": MONDAY_TOKEN, "Content-Type": "application/json"}
    payload = {"query": query, "variables": variables or {}}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(MONDAY_URL, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            if data.get("errors"):
                raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
            return data
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise last

def clickup_get(path, params=None, retries=3, timeout=60):
    headers = {"Authorization": CLICKUP_TOKEN}
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(f"{CLICKUP_URL}{path}", headers=headers, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    raise last

def clickup_post(path, payload):
    r = requests.post(
        f"{CLICKUP_URL}{path}",
        headers={
            "Authorization": CLICKUP_TOKEN,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=120
    )
    if not r.ok:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"ClickUp POST failed {r.status_code} {path} payload={payload} response={detail}")
    return r.json()

def find_status_text(column_values):
    for c in column_values:
        if c.get("type") == "status" and c.get("text"):
            return c.get("text")
    return None

def find_date_text(column_values, column_id_hint=None):
    for c in column_values:
        if c.get("type") == "date":
            if column_id_hint is None or c.get("id") == column_id_hint:
                return c.get("text")
    return None

def get_selected_board_ids():
    cfg = load_json(CONFIG_DIR / "monday_boards.json", {"boards": []})
    selected = cfg.get("boards", [])
    if selected:
        return [str(x) for x in selected]

    schema = load_json(DATA_RAW / "monday_boards.json", {})
    boards = schema.get("data", {}).get("boards", [])
    return [str(b["id"]) for b in boards]
