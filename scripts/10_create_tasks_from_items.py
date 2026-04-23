from common import load_json, save_json, DATA_NORM, STATE_DIR, clickup_post, append_log

items = load_json(DATA_NORM / "tasks.json", [])
lists_map = load_json(STATE_DIR / "lists_map.json", {})
state = load_json(STATE_DIR / "tasks_map.json", {})
errors = load_json(STATE_DIR / "tasks_errors.json", [])

total = len(items)
created = 0
skipped = 0
failed = 0

for idx, item in enumerate(items, 1):
    src = item["source"]
    monday_item_id = str(src["item_id"])

    if monday_item_id in state:
        skipped += 1
        if idx % 50 == 0 or idx == total:
            print(f"[{idx}/{total}] skipped={skipped} created={created} failed={failed}")
        continue

    list_key = f"{src['board_id']}:{src['group_id']}"
    list_id = lists_map.get(list_key)
    if not list_id:
        failed += 1
        errors.append({
            "item_id": monday_item_id,
            "reason": "list_id_not_found",
            "list_key": list_key
        })
        append_log("tasks_import_errors.log", f"{monday_item_id} | list_id_not_found | {list_key}")
        continue

    task = item["task"]
    payload = {
        "name": task["name"],
        "markdown_content": task.get("description_md", "")
    }

    if task.get("status"):
        payload["status"] = task["status"]

    try:
        res = clickup_post(f"/list/{list_id}/task", payload)
    except Exception as e:
        msg = str(e)

        if '"status"' in msg.lower() or "status" in msg.lower():
            payload_fallback = {
                "name": task["name"],
                "markdown_content": task.get("description_md", "")
            }
            try:
                res = clickup_post(f"/list/{list_id}/task", payload_fallback)
            except Exception as e2:
                failed += 1
                errors.append({
                    "item_id": monday_item_id,
                    "reason": "create_task_failed_after_status_fallback",
                    "list_id": list_id,
                    "payload": payload,
                    "error": str(e2)
                })
                append_log("tasks_import_errors.log", f"{monday_item_id} | create_task_failed_after_status_fallback | {str(e2)}")
                continue
        else:
            failed += 1
            errors.append({
                "item_id": monday_item_id,
                "reason": "create_task_failed",
                "list_id": list_id,
                "payload": payload,
                "error": msg
            })
            append_log("tasks_import_errors.log", f"{monday_item_id} | create_task_failed | {msg}")
            continue

    state[monday_item_id] = str(res.get("id"))
    created += 1

    if idx % 25 == 0:
        save_json(STATE_DIR / "tasks_map.json", state)
        save_json(STATE_DIR / "tasks_errors.json", errors)
        print(f"[{idx}/{total}] skipped={skipped} created={created} failed={failed}")

save_json(STATE_DIR / "tasks_map.json", state)
save_json(STATE_DIR / "tasks_errors.json", errors)
print(f"tasks processed | total={total} created={created} skipped={skipped} failed={failed}")