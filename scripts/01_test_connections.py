from common import monday_query, clickup_get

me = monday_query("query { me { id name email } }")
print(me)
teams = clickup_get("/team")
print(teams)
