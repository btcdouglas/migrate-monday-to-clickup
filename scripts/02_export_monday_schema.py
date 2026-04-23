from common import monday_query, save_json, DATA_RAW

all_boards = []
page = 1

while True:
    query = """
    query($page: Int!) {
      boards(limit: 100, page: $page) {
        id
        name
        description
        board_kind
        columns { id title type }
        groups { id title }
      }
    }
    """
    data = monday_query(query, {"page": page})
    boards = data.get("data", {}).get("boards", [])
    if not boards:
        break
    all_boards.extend(boards)
    if len(boards) < 100:
        break
    page += 1

save_json(DATA_RAW / "monday_boards.json", {"data": {"boards": all_boards}})
print(f"saved schema for {len(all_boards)} boards")