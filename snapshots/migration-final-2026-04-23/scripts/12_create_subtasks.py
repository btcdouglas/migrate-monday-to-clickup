from common import load_json, save_json, DATA_NORM, STATE_DIR, clickup_post, clickup_get, append_log

subtasks = load_json(DATA_NORM / "subtasks.json", [])
tasks_map = load_json(STATE_DIR / "tasks_map.json", {})
state = load_json(STATE_DIR / "subtasks_map.json", {})
errors = load_json(STATE_DIR / "subtasks_errors.json", [])

if not isinstance(errors, list):
    errors = []

parent_list_cache = {}

def get_parent_list_id(parent_clickup_id):
    parent_clickup_id = str(parent_clickup_id)
    if parent_clickup_id in parent_list_cache:
        return parent_list_cache[parent_clickup_id]

    data = clickup_get(f"/task/{parent_clickup_id}")
    list_info = data.get("list", {}) if isinstance(data, dict) else {}
    list_id = str(list_info.get("id", "")).strip()

    if not list_id:
        raise RuntimeError(f"list_id não encontrado para parent task {parent_clickup_id}")

    parent_list_cache[parent_clickup_id] = list_id
    return list_id

total = len(subtasks)
created = 0
skipped = 0
failed = 0

for idx, item in enumerate(subtasks, 1):
    src = item.get("source", {})
    task = item.get("task", {})

    subitem_id = str(src.get("subitem_id", "")).strip()
    parent_monday_item_id = str(src.get("parent_item_id", "")).strip()

    if not subitem_id:
        failed += 1
        errors.append({
            "reason": "missing_subitem_id",
            "item": item
        })
        append_log("subtasks_import_errors.log", f"missing_subitem_id | {item}")
        continue

    if subitem_id in state:
        skipped += 1
        if idx % 25 == 0 or idx == total:
            print(f"[{idx}/{total}] skipped={skipped} created={created} failed={failed}")
        continue

    parent_clickup_id = tasks_map.get(parent_monday_item_id)

    if not parent_clickup_id:
        failed += 1
        errors.append({
            "subitem_id": subitem_id,
            "reason": "parent_task_not_found",
            "parent_monday_item_id": parent_monday_item_id
        })
        append_log("subtasks_import_errors.log", f"{subitem_id} | parent_task_not_found | {parent_monday_item_id}")
        continue

    try:
        parent_list_id = get_parent_list_id(parent_clickup_id)
    except Exception as e:
        failed += 1
        errors.append({
            "subitem_id": subitem_id,
            "reason": "parent_list_lookup_failed",
            "parent_clickup_id": parent_clickup_id,
            "error": str(e)
        })
        append_log("subtasks_import_errors.log", f"{subitem_id} | parent_list_lookup_failed | {str(e)}")
        continue

    payload = {
        "name": task.get("name", f"Subtask {subitem_id}"),
        "description": task.get("description_md", ""),
        "parent": parent_clickup_id
    }

    try:
        res = clickup_post(f"/list/{parent_list_id}/task", payload)
        state[subitem_id] = str(res.get("id", subitem_id))
        created += 1
    except Exception as e:
        failed += 1
        errors.append({
            "subitem_id": subitem_id,
            "reason": "create_subtask_failed",
            "parent_clickup_id": parent_clickup_id,
            "parent_list_id": parent_list_id,
            "payload": payload,
            "error": str(e)
        })
        append_log("subtasks_import_errors.log", f"{subitem_id} | create_subtask_failed | {str(e)}")

    if idx % 25 == 0:
        save_json(STATE_DIR / "subtasks_map.json", state)
        save_json(STATE_DIR / "subtasks_errors.json", errors)
        print(f"[{idx}/{total}] skipped={skipped} created={created} failed={failed}")

save_json(STATE_DIR / "subtasks_map.json", state)
save_json(STATE_DIR / "subtasks_errors.json", errors)
print(f"subtasks processed | total={total} created={created} skipped={skipped} failed={failed}")
