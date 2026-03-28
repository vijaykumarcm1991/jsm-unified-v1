import requests
import os

def get_auth(source_type):
    if source_type == "JIRA":
        return (
            (os.getenv("JIRA_USERNAME"), os.getenv("JIRA_PASSWORD")),
            {"Content-Type": "application/json"}
        )
    else:
        return (
            None,
            {
                "Authorization": f"Bearer {os.getenv('JSM_PAT')}",
                "Content-Type": "application/json"
            }
        )

def get_base_url(source_type):
    if source_type == "JIRA":
        return os.getenv("JIRA_URL")
    else:
        return os.getenv("JSM_URL")

def get_projects(source_type):
    base_url = get_base_url(source_type)

    url = f"{base_url}/rest/api/2/project"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    return res.json()


def get_issue_types(source_type, project_key):
    base_url = get_base_url(source_type)

    url = f"{base_url}/rest/api/2/project/{project_key}"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    return [i["name"] for i in data.get("issueTypes", [])]


def get_statuses(source_type, project_key):
    base_url = get_base_url(source_type)

    url = f"{base_url}/rest/api/2/project/{project_key}/statuses"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    statuses = set()

    for item in data:
        for s in item.get("statuses", []):
            statuses.add(s["name"])

    return list(statuses)

def get_fields(source_type):
    base_url = get_base_url(source_type)

    url = f"{base_url}/rest/api/2/field"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    return [{"id": f["id"], "name": f["name"]} for f in data]