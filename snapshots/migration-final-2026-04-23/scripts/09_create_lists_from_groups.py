import unicodedata
from common import load_json, save_json, DATA_NORM, STATE_DIR, clickup_post, clickup_get

lists_ = load_json(DATA_NORM / "lists.json", [])
folders_map = load_json(STATE_DIR / "folders_map.json", {})
state = load_json(STATE_DIR / "lists_map.json", {})

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

existing_lists_by_folder = {}

def get_existing_lists(folder_id):
    folder_id = str(folder_id)
    if folder_id in existing_lists_by_folder:
        return existing_lists_by_folder[folder_id]

    data = clickup_get(f"/folder/{folder_id}/list")
    lists_data = data.get("lists", [])
    mapped = {
        norm_name(x["name"]): str(x["id"])
        for x in lists_data
        if x.get("name") and x.get("id")
    }
    existing_lists_by_folder[folder_id] = mapped
    return mapped

for l in lists_:
    board_id = str(l["source_board_id"])
    group_id = str(l["source_group_id"])
    state_key = f"{board_id}:{group_id}"

    if state_key in state:
        continue

    folder_id = folders_map.get(board_id)
    if not folder_id:
        print(f"[SKIP] folder não encontrado para board {board_id}")
        continue

    list_name = clean_name(l.get("list_name"))
    if not list_name:
        print(f"[SKIP] list_name vazio para board {board_id} / group {group_id}")
        continue

    key = norm_name(list_name)
    existing_map = get_existing_lists(folder_id)

    if key in existing_map:
        state[state_key] = existing_map[key]
        print(f"[EXISTS] lista já existe: {list_name}")
        continue

    try:
        res = clickup_post(f"/folder/{folder_id}/list", {"name": list_name})
        list_id = str(res["id"])
        state[state_key] = list_id
        existing_map[key] = list_id
        print(f"[OK] lista criada: {list_name}")
    except RuntimeError as e:
        msg = str(e)
        if "List name taken" in msg:
            refreshed = clickup_get(f"/folder/{folder_id}/list")
            refreshed_map = {
                norm_name(x["name"]): str(x["id"])
                for x in refreshed.get("lists", [])
                if x.get("name") and x.get("id")
            }
            if key in refreshed_map:
                state[state_key] = refreshed_map[key]
                existing_lists_by_folder[str(folder_id)] = refreshed_map
                print(f"[EXISTS-API] lista já existia: {list_name}")
                continue
        raise

save_json(STATE_DIR / "lists_map.json", state)
print("lists processed")