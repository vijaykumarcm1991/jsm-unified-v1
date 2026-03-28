import requests
import os
from utils.logger import logger

def fetch_issues(source_type: str, jql: str, fields: list, cancel_event=None):
    """
    Fetch ALL issues from Jira/JSM using pagination
    Supports cancellation via threading.Event
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
    total = None  # will be set after first response

    logger.info(f"[{source_type.upper()}] 🔍 Starting paginated fetch")

    while True:

        # 🔴 CANCEL CHECK (TOP PRIORITY)
        if cancel_event and cancel_event.is_set():
            logger.info(f"[{source_type.upper()}] 🛑 Cancel detected — stopping fetch loop")
            break

        payload = {
            "jql": jql,
            "fields": fields,
            "startAt": start_at,
            "maxResults": max_results
        }

        try:
            response = requests.post(
                url,
                json=payload,
                auth=auth,
                headers=headers,
                timeout=30
            )

        except Exception as e:
            logger.error(f"[{source_type.upper()}] ❌ Request failed: {str(e)}")
            raise Exception("Jira connection failed")

        # 🔴 HANDLE BAD RESPONSE
        if response.status_code != 200:
            logger.error(f"[{source_type.upper()}] ❌ API error: {response.status_code} - {response.text}")
            raise Exception("Jira API error")

        data = response.json()

        issues = data.get("issues", [])
        total = data.get("total", 0)

        all_issues.extend(issues)

        logger.info(f"[{source_type.upper()}] 📦 Fetched {len(all_issues)} / {total} issues")

        # 🔴 STOP CONDITION
        if len(all_issues) >= total:
            logger.info(f"[{source_type.upper()}] ✅ Fetch complete")
            break

        start_at += max_results

    logger.info(f"[{source_type.upper()}] 📊 Final fetched count: {len(all_issues)}")

    return all_issues