import requests
import os
from utils.logger import logger

def fetch_issues(source_type: str, jql: str, fields: list):
    """
    Fetch ALL issues from Jira/JSM using pagination
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

    all_issues = []
    start_at = 0
    max_results = 100

    while True:
        payload = {
            "jql": jql,
            "fields": fields,
            "startAt": start_at,
            "maxResults": max_results
        }

        try:
            response = requests.post(url, json=payload, auth=auth, headers=headers, timeout=30)

        except Exception as e:
            logger.error(f"Jira request failed: {str(e)}")
            raise Exception("Jira connection failed")

        data = response.json()

        issues = data.get("issues", [])
        total = data.get("total", 0)

        all_issues.extend(issues)

        logger.info(f"[{source_type.upper()}] Fetched {len(all_issues)} / {total} issues")

        # Stop condition
        if len(all_issues) >= total:
            break

        start_at += max_results

    return all_issues