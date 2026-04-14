import os
import json
import csv
from datetime import datetime
import pytz
from openpyxl import Workbook
from utils.logger import logger


# 🔥 TIMEZONE
IST = pytz.timezone("Asia/Kolkata")


def format_datetime(value):
    """
    Normalize datetime formats (handles IST + timezone correctly)
    """

    if not value:
        return ""

    try:
        # 🔥 STRING DATETIME (ISO with timezone)
        if isinstance(value, str) and "T" in value:

            # Example: 2026-04-14T14:31:00.000+0530
            dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

            # Already in IST → just format
            return dt.strftime("%Y-%m-%d %H:%M:%S")

        # 🔥 Python datetime
        if isinstance(value, datetime):

            if value.tzinfo is None:
                # Assume already IST if no timezone
                value = IST.localize(value)

            return value.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        pass

    return value

def extract_adf_text(adf):
    """
    Extract plain text from Atlassian Document Format (ADF)
    """
    try:
        texts = []

        def recurse(content):
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
                elif "content" in item:
                    recurse(item["content"])

        if "content" in adf:
            recurse(adf["content"])

        return " ".join(texts)

    except Exception:
        return str(adf)

# 🔥 HELPER — NORMALIZE VALUE
def normalize_value(value):
    """
    Normalize Jira field values (dict, list, datetime)
    """

    # 🔥 HANDLE DICT VALUES
    if isinstance(value, dict):

        # ✅ Assignee / User fields
        if "displayName" in value:
            value = value.get("displayName")

        # ✅ Common fields
        elif "name" in value:
            value = value.get("name")

        elif "value" in value:
            value = value.get("value")

        # ✅ ADF (rich text)
        elif value.get("type") == "doc":
            value = extract_adf_text(value)

        else:
            value = str(value)

    # 🔥 HANDLE LIST
    elif isinstance(value, list):
        value = ", ".join(
            normalize_value(v) for v in value
        )

    return format_datetime(value)

def generate_excel(report_name, issues, fields, source_type, export_type="xlsx", field_names_map=None):
    """
    Generate report file in selected format (xlsx / csv / json)
    """

    if field_names_map is None:
        field_names_map = {}

    timestamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    safe_name = report_name.replace(" ", "_")

    logger.info(f"[EXPORT] 🔧 Generating file type: {export_type}")

    # =========================
    # 🔥 CSV EXPORT
    # =========================
    if export_type == "csv":

        file_path = f"/reports/{safe_name}_{timestamp}.csv"

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header
                headers = [
                    field_names_map.get(field, field)
                    for field in fields
                ]
                writer.writerow(headers)

                for issue in issues:
                    row = []
                    issue_fields = issue.get("fields", {})

                    for field in fields:
                        # 🔥 HANDLE ROOT LEVEL FIELDS (INCLUDING issuekey)
                        if field in ["key", "issuekey"]:
                            value = issue.get("key")

                        elif field in ["id", "self"]:
                            value = issue.get(field)

                        else:
                            value = issue_fields.get(field, "")

                        value = normalize_value(value)
                        row.append(str(value) if value is not None else "")

                    writer.writerow(row)

            logger.info(f"[EXPORT] ✅ CSV created: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"[EXPORT] ❌ CSV failed: {str(e)}")
            raise

    # =========================
    # 🔥 JSON EXPORT
    # =========================
    elif export_type == "json":

        file_path = f"/reports/{safe_name}_{timestamp}.json"

        try:
            data = []

            for issue in issues:
                issue_fields = issue.get("fields", {})
                row = {}

                for field in fields:
                    # 🔥 HANDLE ROOT LEVEL FIELDS (INCLUDING issuekey)
                    if field in ["key", "issuekey"]:
                        value = issue.get("key")

                    elif field in ["id", "self"]:
                        value = issue.get(field)

                    else:
                        value = issue_fields.get(field, "")

                    value = normalize_value(value)
                    display_name = field_names_map.get(field, field)
                    row[display_name] = value

                data.append(row)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"[EXPORT] ✅ JSON created: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"[EXPORT] ❌ JSON failed: {str(e)}")
            raise

    # =========================
    # 🔥 XLSX EXPORT (DEFAULT)
    # =========================
    else:

        file_path = f"/reports/{safe_name}_{timestamp}.xlsx"

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Report"

            # Header
            headers = [
                field_names_map.get(field, field)
                for field in fields
            ]

            ws.append(headers)

            for issue in issues:
                row = []
                issue_fields = issue.get("fields", {})

                for field in fields:
                    # 🔥 HANDLE ROOT LEVEL FIELDS (INCLUDING issuekey)
                    if field in ["key", "issuekey"]:
                        value = issue.get("key")

                    elif field in ["id", "self"]:
                        value = issue.get(field)

                    else:
                        value = issue_fields.get(field, "")

                    value = normalize_value(value)
                    row.append(value if value is not None else "")

                ws.append(row)

            wb.save(file_path)

            logger.info(f"[EXPORT] ✅ Excel created: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"[EXPORT] ❌ Excel failed: {str(e)}")
            raise