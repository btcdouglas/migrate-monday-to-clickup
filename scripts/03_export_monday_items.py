import sys
from common import monday_query, save_json, DATA_RAW, get_selected_board_ids

def export_board(board_id):
    cursor = None
    page_num = 1

    while True:
        if cursor is None:
            query = """
            query($board_id: ID!) {
              boards(ids: [$board_id]) {
                id
                name
                items_page(limit: 500) {
                  cursor
                  items {
                    id
                    name
                    group { id title }
                    created_at
                    updated_at
                    creator_id
                    column_values { id type text value }
                    subitems {
                      id
                      name
                      created_at
                      updated_at
                      column_values { id type text value }
                    }
                  }
                }
              }
            }
            """
            data = monday_query(query, {"board_id": str(board_id)})

            boards = data.get("data", {}).get("boards", [])
            if not boards:
                print(f"[SKIP] board {board_id} não retornou dados ou sem acesso")
                return

            page = boards[0].get("items_page")
            if not page:
                print(f"[SKIP] board {board_id} sem items_page")
                return

        else:
            query = """
            query($cursor: String!) {
              next_items_page(limit: 500, cursor: $cursor) {
                cursor
                items {
                  id
                  name
                  group { id title }
                  created_at
                  updated_at
                  creator_id
                  column_values { id type text value }
                  subitems {
                    id
                    name
                    created_at
                    updated_at
                    column_values { id type text value }
                  }
                }
              }
            }
            """
            data = monday_query(query, {"cursor": cursor})
            page = data.get("data", {}).get("next_items_page")

            if not page:
                print(f"[SKIP] paginação vazia no board {board_id}")
                return

        save_json(DATA_RAW / f"monday_board_{board_id}_items_page_{page_num}.json", data)

        cursor = page.get("cursor")
        if not cursor:
            break
        page_num += 1

    print(f"[OK] items exported for board {board_id}")

if len(sys.argv) > 1:
    export_board(sys.argv[1])
else:
    for board_id in get_selected_board_ids():
        export_board(board_id)