from common import (
    load_json,
    save_json,
    DATA_RAW,
    DATA_NORM,
    find_status_text,
    find_date_text,
    get_selected_board_ids,
)

boards_schema = load_json(DATA_RAW / "monday_boards.json", {})
status_map = load_json("config/status_mapping.json", {})

folders = []
lists_ = []
tasks = []
subtasks = []

board_lookup = {}
for b in boards_schema.get("data", {}).get("boards", []):
    board_lookup[str(b["id"])] = b

boards_cfg = get_selected_board_ids()

for board_id in boards_cfg:
    b = board_lookup.get(str(board_id))
    if not b:
        continue

    folders.append({
        "source_board_id": str(board_id),
        "folder_name": b["name"]
    })

    for g in b.get("groups", []):
        lists_.append({
            "source_board_id": str(board_id),
            "source_group_id": g["id"],
            "list_name": g["title"]
        })

    page = 1
    while True:
        p = DATA_RAW / f"monday_board_{board_id}_items_page_{page}.json"
        if not p.exists():
            break

        data = load_json(p, {})

        if page == 1:
            items = data.get("data", {}).get("boards", [{}])[0].get("items_page", {}).get("items", [])
        else:
            items = data.get("data", {}).get("next_items_page", {}).get("items", [])

        for item in items:
            status = status_map.get(find_status_text(item.get("column_values", [])), None)

            description_md = f"""### Metadata de migração
- source_platform: monday
- monday_board_id: {board_id}
- monday_group_id: {item.get('group', {}).get('id')}
- monday_item_id: {item['id']}
"""

            tasks.append({
                "source": {
                    "board_id": str(board_id),
                    "group_id": item.get("group", {}).get("id"),
                    "item_id": item["id"]
                },
                "task": {
                    "name": item["name"],
                    "description_md": description_md,
                    "status": status,
                    "start_date_text": find_date_text(item.get("column_values", [])),
                    "due_date_text": find_date_text(item.get("column_values", [])),
                    "custom_fields_raw": item.get("column_values", [])
                }
            })

            for sub in item.get("subitems", []):
                subtasks.append({
                    "source": {
                        "board_id": str(board_id),
                        "parent_item_id": item["id"],
                        "subitem_id": sub["id"]
                    },
                    "task": {
                        "name": sub["name"],
                        "description_md": f"Subitem origin: {sub['id']}"
                    }
                })

        page += 1

comments = load_json(DATA_RAW / "monday_updates.json", [])
attachments = load_json(DATA_RAW / "monday_assets_manifest.json", [])

save_json(DATA_NORM / "folders.json", folders)
save_json(DATA_NORM / "lists.json", lists_)
save_json(DATA_NORM / "tasks.json", tasks)
save_json(DATA_NORM / "subtasks.json", subtasks)
save_json(DATA_NORM / "comments.json", comments)
save_json(DATA_NORM / "attachments_manifest.json", attachments)
save_json(DATA_NORM / "automations_inventory.json", load_json(DATA_RAW / "monday_webhooks.json", []))

print("normalized")