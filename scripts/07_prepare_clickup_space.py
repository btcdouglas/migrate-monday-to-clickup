from common import clickup_get, save_json, CONFIG_DIR
teams = clickup_get("/team")
team_id = str(teams.get("teams", [{}])[0].get("id", "")) if teams.get("teams") else ""
space_id = ""
space_name = ""
if team_id:
    spaces = clickup_get(f"/team/{team_id}/space")
    if spaces.get("spaces"):
        space_id = str(spaces["spaces"][0]["id"])
        space_name = spaces["spaces"][0]["name"]
save_json(CONFIG_DIR / "clickup_target.json", {"team_id": team_id, "space_id": space_id, "space_name": space_name})
print({"team_id": team_id, "space_id": space_id, "space_name": space_name})
