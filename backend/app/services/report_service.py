import os
import json
import csv
from datetime import datetime
import pytz
from openpyxl import Workbook
from utils.logger import logger


# 🔥 TIMEZONE
IST = pytz.timezone("Asia/Kolkata")


# 🔥 HELPER — FORMAT DATETIME (UTC → IST)
def format_datetime(value):
    """
    Normalize datetime formats to IST
    """

    if not value:
        return ""

    try:
        # Jira datetime (UTC format)
        if isinstance(value, str) and "T" in value:
            dt = datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
            dt = pytz.utc.localize(dt).astimezone(IST)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

        # Python datetime
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = pytz.utc.localize(value)

            value = value.astimezone(IST)
            return value.strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        pass

    return value


# 🔥 HELPER — NORMALIZE VALUE
def normalize_value(value):
    """
    Normalize Jira field values (dict, list, datetime)
    """

    if isinstance(value, dict):
        value = value.get("name") or value.get("value") or str(value)

    elif isinstance(value, list):
        value = ", ".join(
            str(v.get("name") if isinstance(v, dict) else v)
            for v in value
        )

    return format_datetime(value)


def generate_excel(report_name, issues, fields, source_type, export_type="xlsx"):
    """
    Generate report file in selected format (xlsx / csv / json)
    """

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
                writer.writerow(fields)

                for issue in issues:
                    row = []
                    issue_fields = issue.get("fields", {})

                    for field in fields:
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
                    value = issue_fields.get(field, "")
                    value = normalize_value(value)
                    row[field] = value

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
            ws.append(fields)

            for issue in issues:
                row = []
                issue_fields = issue.get("fields", {})

                for field in fields:
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