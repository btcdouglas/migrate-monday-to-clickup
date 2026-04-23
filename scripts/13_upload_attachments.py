from pathlib import Path
from common import load_json, DATA_NORM, STATE_DIR, clickup_post, append_log
manifest = load_json(DATA_NORM / "attachments_manifest.json", [])
tasks_map = load_json(STATE_DIR / "tasks_map.json", {})
for row in manifest:
    task_id = tasks_map.get(row.get("item_id"))
    if not task_id:
        continue
    for f in row.get("files", []):
        p = Path(f.get("local_path", ""))
        if not p.exists():
            append_log("import.log", f"attachment missing item={row.get('item_id')} path={p}")
            continue
        with open(p, "rb") as fh:
            clickup_post(f"/task/{task_id}/attachment", files={"attachment": fh})
print("attachments processed")
