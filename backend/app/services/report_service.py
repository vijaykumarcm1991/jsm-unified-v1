import pandas as pd
from datetime import datetime
import os
import pytz

IST = pytz.timezone("Asia/Kolkata")


def format_datetime(value):
    try:
        # Example: 2026-03-27T16:30:39.000+0530
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

        # Convert to IST (safe even if already IST)
        dt = dt.astimezone(IST)

        return dt.strftime("%d-%m-%Y %H:%M:%S")

    except Exception:
        return value


def generate_excel(report_name: str, issues: list, fields: list):
    """
    Convert Jira issues → Excel file
    """

    rows = []

    for issue in issues:
        row = {
            "Key": issue.get("key")
        }

        issue_fields = issue.get("fields", {})

        for f in fields:
            value = issue_fields.get(f)

            # Handle nested objects (like priority)
            if isinstance(value, dict):
                value = value.get("name") or value.get("value")

            # ✅ Format datetime fields
            if isinstance(value, str) and "T" in value:
                value = format_datetime(value)

            row[f] = value

        rows.append(row)

    df = pd.DataFrame(rows)

    # File name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{report_name}_{timestamp}.xlsx"

    file_path = f"/reports/{file_name}"

    df.to_excel(file_path, index=False)

    return file_path