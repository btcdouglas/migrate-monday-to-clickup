from common import load_json, save_json, DATA_RAW, append_log, get_selected_board_ids
boards_cfg = get_selected_board_ids()
updates = []
assets = []
for board_id in boards_cfg:
    page = 1
    while True:
        p = DATA_RAW / f"monday_board_{board_id}_items_page_{page}.json"
        if not p.exists():
            break
        data = load_json(p, {})
        items = data.get("data", {}).get("boards", [{}])[0].get("items_page", {}).get("items", []) if page == 1 else data.get("data", {}).get("next_items_page", {}).get("items", [])
        for item in items:
            updates.append({
                "board_id": str(board_id),
                "item_id": item["id"],
                "comments": [{
                    "author": "migration-placeholder",
                    "created_at": item.get("updated_at"),
                    "text": "Export automático: updates reais devem ser implementados com query específica de updates conforme seu plano/API disponível."
                }]
            })
            assets.append({"board_id": str(board_id), "item_id": item["id"], "files": []})
        page += 1
save_json(DATA_RAW / "monday_updates.json", updates)
save_json(DATA_RAW / "monday_assets_manifest.json", assets)
append_log("export.log", "updates/assets placeholder export completed")
print("updates/assets manifests saved")
