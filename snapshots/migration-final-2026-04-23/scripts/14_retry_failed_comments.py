from common import load_json, save_json, STATE_DIR, clickup_post, append_log
import time

errors = load_json(STATE_DIR / "comments_errors.json", [])
state = load_json(STATE_DIR / "comments_map.json", {})

retryable = [x for x in errors if x.get("reason") == "create_comment_failed"]

created = 0
failed = 0
remaining_errors = []

for row in retryable:
    item_id = str(row.get("item_id", "")).strip()
    payload = row.get("payload", {})
    raw_error = row.get("error", "")

    if not item_id or not payload.get("comment_text"):
        failed += 1
        remaining_errors.append(row)
        continue

    task_id = None
    marker = " /task/"
    if marker in raw_error and "/comment" in raw_error:
        task_id = raw_error.split(marker, 1)[1].split("/comment", 1)[0].strip()

    if not task_id:
        failed += 1
        remaining_errors.append(row)
        append_log("comments_retry_errors.log", f"{item_id} | missing_task_id_from_error")
        continue

    ok = False
    last_error = None

    for wait_seconds in (2, 5, 10):
        try:
            res = clickup_post(f"/task/{task_id}/comment", payload)
            key = f"retry:{item_id}:{task_id}"
            state[key] = str(res.get("id", key))
            created += 1
            ok = True
            break
        except Exception as e:
            last_error = str(e)
            time.sleep(wait_seconds)

    if not ok:
        failed += 1
        row["retry_error"] = last_error
        remaining_errors.append(row)
        append_log("comments_retry_errors.log", f"{item_id} | retry_failed | {last_error}")

save_json(STATE_DIR / "comments_map.json", state)
all_errors = [x for x in errors if x.get("reason") != "create_comment_failed"]
all_errors.extend(remaining_errors)
save_json(STATE_DIR / "comments_errors.json", all_errors)

print(f"retry finished | retried={len(retryable)} created={created} failed={failed}")
