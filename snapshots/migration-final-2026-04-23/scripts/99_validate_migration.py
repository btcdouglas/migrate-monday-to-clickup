from common import load_json, DATA_NORM, STATE_DIR, save_json
report = {
    "folders_expected": len(load_json(DATA_NORM / "folders.json", [])),
    "folders_created": len(load_json(STATE_DIR / "folders_map.json", {})),
    "lists_expected": len(load_json(DATA_NORM / "lists.json", [])),
    "lists_created": len(load_json(STATE_DIR / "lists_map.json", {})),
    "tasks_expected": len(load_json(DATA_NORM / "tasks.json", [])),
    "tasks_created": len(load_json(STATE_DIR / "tasks_map.json", {})),
    "subtasks_expected": len(load_json(DATA_NORM / "subtasks.json", [])),
    "subtasks_created": len(load_json(STATE_DIR / "subtasks_map.json", {})),
    "comments_expected_groups": len(load_json(DATA_NORM / "comments.json", [])),
    "attachments_expected_groups": len(load_json(DATA_NORM / "attachments_manifest.json", []))
}
save_json(STATE_DIR / "validation_report.json", report)
print(report)
