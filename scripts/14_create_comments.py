from common import load_json, save_json, DATA_NORM, STATE_DIR, clickup_post, append_log

items = load_json(DATA_NORM / "comments.json", [])
tasks_map = load_json(STATE_DIR / "tasks_map.json", {})
state = load_json(STATE_DIR / "comments_map.json", {})
errors = load_json(STATE_DIR / "comments_errors.json", [])

if not isinstance(errors, list):
    errors = []

total = sum(len(x.get("comments", [])) for x in items)
created = 0
skipped = 0
failed = 0

for idx_item, item in enumerate(items, 1):
    monday_item_id = str(item.get("item_id", ""))

    task_id = tasks_map.get(monday_item_id)
    if not task_id:
        failed += len(item.get("comments", []))
        errors.append({
            "item_id": monday_item_id,
            "reason": "task_not_found"
        })
        append_log("comments_import_errors.log", f"{monday_item_id} | task_not_found")
        continue

    for idx_comment, c in enumerate(item.get("comments", []), 1):
        key = f"{monday_item_id}:{c.get('created_at','')}:{idx_comment}"

        if key in state:
            skipped += 1
            continue

        author = c.get("author", "Unknown")
        created_at = c.get("created_at", "")
        text_body = c.get("text", "").strip()

        comment_text = (
            f"[Migrated from monday]\n"
            f"{author} - {created_at}\n\n"
            f"{text_body}"
        )

        payload = {
            "comment_text": comment_text
        }

        try:
            res = clickup_post(f"/task/{task_id}/comment", payload)
            state[key] = str(res.get("id", key))
            created += 1
        except Exception as e:
            failed += 1
            errors.append({
                "item_id": monday_item_id,
                "reason": "create_comment_failed",
                "payload": payload,
                "error": str(e)
            })
            append_log("comments_import_errors.log", f"{monday_item_id} | create_comment_failed | {str(e)}")

        if (created + skipped + failed) % 25 == 0:
            save_json(STATE_DIR / "comments_map.json", state)
            save_json(STATE_DIR / "comments_errors.json", errors)
            print(f"[{created+skipped+failed}/{total}] created={created} skipped={skipped} failed={failed}")

save_json(STATE_DIR / "comments_map.json", state)
save_json(STATE_DIR / "comments_errors.json", errors)
print(f"comments processed | total={total} created={created} skipped={skipped} failed={failed}")