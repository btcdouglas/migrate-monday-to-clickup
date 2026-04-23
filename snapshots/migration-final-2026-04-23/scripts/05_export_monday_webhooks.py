from common import monday_query, save_json, DATA_RAW, get_selected_board_ids

boards_cfg = get_selected_board_ids()
query = """
query($board_id: [ID!]) {
  boards(ids: $board_id) {
    id
    name
    webhooks {
      id
      board_id
      event
      config
    }
  }
}
"""
out = []
for board_id in boards_cfg:
    data = monday_query(query, {"board_id": [str(board_id)]})
    out.append(data)

save_json(DATA_RAW / "monday_webhooks.json", out)
print("webhooks exported")