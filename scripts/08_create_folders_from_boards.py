import unicodedata
from common import load_json, save_json, DATA_NORM, STATE_DIR, CONFIG_DIR, clickup_post, clickup_get

folders = load_json(DATA_NORM / "folders.json", [])
state = load_json(STATE_DIR / "folders_map.json", {})
target = load_json(CONFIG_DIR / "clickup_target.json", {})

space_id = str(target.get("space_id", "")).strip()

if not space_id:
    raise RuntimeError("space_id ausente em config/clickup_target.json")

def clean_name(value):
    if value is None:
        return ""
    name = str(value).strip()
    name = " ".join(name.split())
    return name[:200]

def norm_name(value):
    s = clean_name(value)
    s = unicodedata.normalize("NFKC", s)
    return s.casefold()

existing = clickup_get(f"/space/{space_id}/folder")
existing_folders = existing.get("folders", [])
existing_by_norm = {
    norm_name(f["name"]): str(f["id"])
    for f in existing_folders
    if f.get("name") and f.get("id")
}

for f in folders:
    bid = str(f["source_board_id"])
    if bid in state:
        continue

    folder_name = clean_name(f.get("folder_name"))
    if not folder_name:
        print(f"[SKIP] board {bid} com folder_name vazio")
        continue

    key = norm_name(folder_name)

    if key in existing_by_norm:
        state[bid] = existing_by_norm[key]
        print(f"[EXISTS] folder já existe: {folder_name}")
        continue

    try:
        res = clickup_post(f"/space/{space_id}/folder", {"name": folder_name})
        folder_id = str(res["id"])
        state[bid] = folder_id
        existing_by_norm[key] = folder_id
        print(f"[OK] folder criado: {folder_name}")
    except RuntimeError as e:
        msg = str(e)
        if "Folder name taken" in msg:
            refreshed = clickup_get(f"/space/{space_id}/folder")
            refreshed_map = {
                norm_name(x["name"]): str(x["id"])
                for x in refreshed.get("folders", [])
                if x.get("name") and x.get("id")
            }
            if key in refreshed_map:
                state[bid] = refreshed_map[key]
                existing_by_norm[key] = refreshed_map[key]
                print(f"[EXISTS-API] folder já existia: {folder_name}")
                continue
        raise

save_json(STATE_DIR / "folders_map.json", state)
print("folders processed")