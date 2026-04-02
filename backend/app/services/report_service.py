import pandas as pd
from datetime import datetime
import os
import pytz
from services.metadata_service import get_fields

IST = pytz.timezone("Asia/Kolkata")


def format_datetime(value):
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

        dt = dt.astimezone(IST)

        # ✅ REMOVE TIMEZONE FOR EXCEL
        dt = dt.replace(tzinfo=None)

        return dt

    except Exception:
        return value


def generate_excel(report_name: str, issues: list, fields: list, source_type: str):
    """
    Convert Jira issues → Excel file
    """

    rows = []

    # ✅ FETCH FIELD METADATA
    field_meta = get_fields(source_type)  # default (we will improve later)

    # ✅ CREATE MAPPING
    field_map = {f["id"]: f["name"] for f in field_meta}

    for issue in issues:
        row = {
            "Issue Key": issue.get("key")
        }

        issue_fields = issue.get("fields", {})

        for f in fields:
            value = issue_fields.get(f)

            # Handle nested objects (like priority)
            if isinstance(value, dict):
                value = value.get("name") or value.get("value")

            # ✅ Format datetime fields
            if isinstance(value, str) and "T" in value:
                parsed = format_datetime(value)
                value = parsed

            column_name = field_map.get(f, f)  # fallback if not found
            row[column_name] = value

        rows.append(row)

    df = pd.DataFrame(rows)

    # File name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{report_name}_{timestamp}.xlsx"

    file_path = f"/reports/{file_name}"

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

        workbook = writer.book
        worksheet = writer.sheets["Report"]

        date_format = workbook.add_format({"num_format": "dd-mm-yyyy hh:mm:ss"})

        # Apply format to datetime columns
        for idx, col in enumerate(df.columns):
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                worksheet.set_column(idx, idx, 20, date_format)
        
        for idx, col in enumerate(df.columns):
            try:
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2

                worksheet.set_column(idx, idx, max_len)

            except Exception:
                worksheet.set_column(idx, idx, 20)

    return file_path