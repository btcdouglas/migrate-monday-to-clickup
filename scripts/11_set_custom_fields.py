from common import load_json, DATA_NORM, STATE_DIR, CONFIG_DIR, clickup_post, append_log
items = load_json(DATA_NORM / "tasks.json", [])
tasks_map = load_json(STATE_DIR / "tasks_map.json", {})
field_map = load_json(CONFIG_DIR / "field_mapping.json", {})
for item in items:
    task_id = tasks_map.get(item["source"]["item_id"])
    if not task_id:
        continue
    for raw in item["task"].get("custom_fields_raw", []):
        fm = field_map.get(raw.get("id")) or field_map.get(raw.get("title"))
        if not fm:
            continue
        payload = {"value": raw.get("text") or raw.get("value")}
        try:
            clickup_post(f"/task/{task_id}/field/{fm['clickup_field_id']}", payload)
        except Exception as e:
            append_log("import.log", f"custom field failed task={task_id} field={fm['clickup_field_id']} err={e}")
print("custom fields processed")
