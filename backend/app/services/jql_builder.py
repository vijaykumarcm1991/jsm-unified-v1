def build_jql(project=None, issue_type=None, status=None,
              start_date=None, end_date=None, range_days=None,
              date_template=None, date_field="created"):

    from datetime import datetime, timedelta

    conditions = []

    # 🔥 TEMPLATE OVERRIDE (OPTION A)
    if date_template:
        if date_template == "LAST_DAY":
            conditions.append(f'{date_field} >= startofday(-1) AND {date_field} < startofday()')

        elif date_template == "LAST_WEEK":
            conditions.append(f'{date_field} >= startofday(-7) AND {date_field} < startofday()')

        elif date_template == "LAST_MONTH":
            conditions.append(f'{date_field} >= startofmonth(-1) AND {date_field} < startofmonth()')

        # 🚨 IMPORTANT → skip other date filters
        start_date = None
        end_date = None
        range_days = None

    def build_condition(field, value, is_string=True):
        if not value:
            return None

        # If value is list → use IN
        if isinstance(value, list):
            if len(value) == 1:
                v = value[0]
                return f'{field} = "{v}"' if is_string else f"{field} = {v}"

            values = ",".join([f'"{v}"' if is_string else str(v) for v in value])
            return f"{field} IN ({values})"

        # Single value
        return f'{field} = "{value}"' if is_string else f"{field} = {value}"

    # ✅ Multi-select support
    project_condition = build_condition("project", project, is_string=False)
    if project_condition:
        conditions.append(project_condition)

    issue_condition = build_condition("issuetype", issue_type)
    if issue_condition:
        conditions.append(issue_condition)

    status_condition = build_condition("status", status)
    if status_condition:
        conditions.append(status_condition)

    # ✅ Date filters
    if range_days:
        conditions.append(f'{date_field} >= -{range_days}d')

    else:
        if start_date:
            conditions.append(f'{date_field} >= "{start_date}"')

        if end_date:
            next_day = (
                datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")

            conditions.append(f'{date_field} < "{next_day}"')

    if not conditions:
        return ""

    return " AND ".join(conditions)