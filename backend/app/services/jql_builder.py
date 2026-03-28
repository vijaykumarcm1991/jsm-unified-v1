def build_jql(project=None, issue_type=None, status=None,
              start_date=None, end_date=None, range_days=None):

    from datetime import datetime, timedelta

    conditions = []

    if project:
        conditions.append(f'project = "{project}"')

    if issue_type:
        conditions.append(f'issuetype = "{issue_type}"')

    if status:
        conditions.append(f'status = "{status}"')

    # ✅ Date filters
    if range_days:
        conditions.append(f'created >= -{range_days}d')

    else:
        if start_date:
            conditions.append(f'created >= "{start_date}"')

        if end_date:
            next_day = (
                datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")

            conditions.append(f'created < "{next_day}"')

    if not conditions:
        return ""

    return " AND ".join(conditions)