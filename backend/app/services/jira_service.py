import time
import requests
import os
from utils.logger import logger
from requests.auth import HTTPBasicAuth


def fetch_issues(source_type: str, jql: str, fields: list, cancel_event=None, progress_callback=None):

    if "order by" not in jql.lower():
        jql += " ORDER BY created ASC"

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
        url = f"{os.getenv('JSM_URL')}/rest/api/3/search/jql"

        auth = HTTPBasicAuth(
            os.getenv("JSM_EMAIL"),
            os.getenv("JSM_API_TOKEN")
        )

        headers = {
            "Accept": "application/json"
        }

    else:
        raise Exception("Invalid source type")

    all_issues = []
    next_page_token = None
    max_results = 100
    total = None

    logger.info(f"[{source_type.upper()}] 🔍 Starting paginated fetch")

    while True:

        if cancel_event and cancel_event.is_set():
            logger.info(f"[{source_type.upper()}] 🛑 Cancel detected — stopping fetch loop")
            break

        # 🔥 JSM → TOKEN BASED PAGINATION
        if source_type == "JSM":
            params = {
                "jql": jql,
                "maxResults": max_results
            }

            if fields:
                params["fields"] = ",".join(fields)

            if next_page_token:
                params["nextPageToken"] = next_page_token

        else:
            payload = {
                "jql": jql,
                "fields": fields,
                "startAt": len(all_issues),
                "maxResults": max_results
            }

        logger.info(f"[{source_type.upper()}] JQL → {jql}")

        try:
            if source_type == "JSM":
                response = requests.get(
                    url,
                    params=params,
                    auth=auth,
                    headers=headers,
                    timeout=30
                )
            else:
                response = requests.post(
                    url,
                    json=payload,
                    auth=auth,
                    headers=headers,
                    timeout=30
                )

            logger.info(f"[{source_type.upper()}] RAW RESPONSE → {response.text[:300]}")

        except Exception as e:
            logger.error(f"[{source_type.upper()}] ❌ Request failed: {str(e)}")
            raise Exception("Jira connection failed")

        if source_type == "JSM" and response.status_code == 429:
            logger.warning("[JSM] ⚠️ Rate limited, retrying...")
            time.sleep(2)
            continue

        if response.status_code != 200:
            logger.error(f"[{source_type.upper()}] ❌ API error: {response.status_code} - {response.text}")
            raise Exception("Jira API error")

        data = response.json()

        issues = data.get("issues", [])
        total = data.get("total")

        # ✅ ADD THIS
        field_names_map = data.get("names", {})

        logger.info(f"[{source_type.upper()}] DEBUG → batch={len(issues)}, total={total}")

        all_issues.extend(issues)

        current = len(all_issues)
        logger.info(f"[{source_type.upper()}] 📦 Fetched {current} issues")

        if progress_callback:
            if source_type == "JSM":
                progress_callback(current, None)
            else:
                progress_callback(current, total)

        # 🔥 JSM → TOKEN BASED STOP
        if source_type == "JSM":
            next_page_token = data.get("nextPageToken")

            if not next_page_token:
                logger.info("[JSM] ✅ No more pages, stopping")
                break

        else:
            if total is not None and len(all_issues) >= total:
                logger.info("[JIRA] ✅ Reached total, stopping")
                break

    logger.info(f"[{source_type.upper()}] 📊 Final fetched count: {len(all_issues)}")

    return all_issues, field_names_map