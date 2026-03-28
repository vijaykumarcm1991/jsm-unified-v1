import requests
import os


def fetch_issues(source_type: str, jql: str, fields: list):
    """
    Fetch issues from Jira or JSM
    """

    if source_type == "JIRA":
        url = f"{os.getenv('JIRA_URL')}/rest/api/2/search"

        auth = (
            os.getenv("JIRA_USERNAME"),
            os.getenv("JIRA_PASSWORD")
        )

        headers = {
            "Content-Type": "application/json"
        }

    elif source_type == "JSM":
        url = f"{os.getenv('JSM_URL')}/rest/api/2/search"

        auth = None

        headers = {
            "Authorization": f"Bearer {os.getenv('JSM_PAT')}",
            "Content-Type": "application/json"
        }

    else:
        raise Exception("Invalid source type")

    payload = {
        "jql": jql,
        "fields": fields,
        "maxResults": 100
    }

    response = requests.post(url, json=payload, auth=auth, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Jira API error: {response.text}")

    data = response.json()

    return data.get("issues", [])