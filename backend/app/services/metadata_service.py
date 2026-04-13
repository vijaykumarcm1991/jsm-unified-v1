from sys import api_version

import requests
import os
from requests.auth import HTTPBasicAuth

def get_auth(source_type):
    if source_type == "JIRA":
        return (
            (os.getenv("JIRA_USERNAME"), os.getenv("JIRA_PASSWORD")),
            {"Content-Type": "application/json"}
        )
    else:     
        return (
            HTTPBasicAuth(
                os.getenv("JSM_EMAIL"),
                os.getenv("JSM_API_TOKEN")
            ),
            {
                "Accept": "application/json"
            }
        )

def get_base_url(source_type):
    if source_type == "JIRA":
        return os.getenv("JIRA_URL")
    else:
        return os.getenv("JSM_URL")

def get_projects(source_type):
    base_url = get_base_url(source_type)

    api_version = "3" if source_type == "JSM" else "2"
    url = f"{base_url}/rest/api/{api_version}/project"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    return res.json()


def get_issue_types(source_type):
    base_url = get_base_url(source_type)

    api_version = "3" if source_type == "JSM" else "2"
    url = f"{base_url}/rest/api/{api_version}/issuetype"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    return [i["name"] for i in data]

def get_statuses(source_type):
    base_url = get_base_url(source_type)

    api_version = "3" if source_type == "JSM" else "2"
    url = f"{base_url}/rest/api/{api_version}/status"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    return [s["name"] for s in data]

def get_fields(source_type):
    base_url = get_base_url(source_type)

    api_version = "3" if source_type == "JSM" else "2"
    url = f"{base_url}/rest/api/{api_version}/field"

    auth, headers = get_auth(source_type)

    res = requests.get(url, auth=auth, headers=headers)

    data = res.json()

    return [{"id": f["id"], "name": f["name"]} for f in data]