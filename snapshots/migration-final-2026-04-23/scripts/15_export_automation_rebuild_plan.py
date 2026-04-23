from common import load_json, save_json, DATA_RAW, DATA_NORM
raw = load_json(DATA_RAW / "monday_webhooks.json", [])
out = []
for chunk in raw:
    for b in chunk.get("data", {}).get("boards", []):
        for w in b.get("webhooks", []):
            out.append({
                "board_id": b.get("id"),
                "board_name": b.get("name"),
                "automation_source": "monday webhook",
                "trigger": w.get("event"),
                "config": w.get("config"),
                "target_clickup_pattern": "manual_or_middleware_rebuild",
                "rebuild_mode": "manual_or_middleware"
            })
save_json(DATA_NORM / "automations_inventory.json", out)
print("automation rebuild plan exported")
