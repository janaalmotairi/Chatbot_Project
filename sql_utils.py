import re

def clean_sql(sql: str) -> str:
    s = (sql or "").strip()
    s = s.replace("```sql", "").replace("```", "").strip()
    s = re.sub(r"^\s*sql\s*:\s*", "", s, flags=re.IGNORECASE).strip()

    m = re.search(r"(select\b.*)", s, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return s.strip()

    s = m.group(1).strip()
    s = s.split(";")[0].strip()
    return s


def fix_common_columns(sql: str) -> str:
    replacements = {
        "monthly_income": "MonthlyIncome",
        "monthlyincome": "MonthlyIncome",
        "salary": "MonthlyIncome",
        "income": "MonthlyIncome",
        "job_satisfaction": "JobSatisfaction",
        "work_life_balance": "WorkLifeBalance",
        "education_field": "EducationField",
        "job_role": "JobRole",
        "overtime": "OverTime",
    }
    out = sql
    for wrong, right in replacements.items():
        out = re.sub(rf"\b{wrong}\b", right, out, flags=re.IGNORECASE)
    return out


def fix_department_values(sql: str) -> str:
    dept_map = {
        "research and development": "Research & Development",
        "research & development": "Research & Development",
        "research &development": "Research & Development",
        "r&d": "Research & Development",
        "r & d": "Research & Development",
        "human resource": "Human Resources",
        "human resources": "Human Resources",
        "sales": "Sales",
    }

    def repl(m):
        val = m.group(1).strip()
        key = re.sub(r"\s+", " ", val.lower())
        fixed = dept_map.get(key, val)
        return f"Department = '{fixed}'"

    return re.sub(r"Department\s*=\s*'([^']+)'", repl, sql, flags=re.IGNORECASE)


def pretty_answer(question: str, cols, rows) -> str:
    q = (question or "").lower()

    if len(cols) == 1 and len(rows) == 1:
        val = rows[0][0]

        if ("how many" in q or "count" in q or "كم" in q or "عدد" in q):
            if "attrition" in q and "yes" in q:
                return f"There are {val} employees with Attrition = 'Yes'."
            if "attrition" in q and "no" in q:
                return f"There are {val} employees with Attrition = 'No'."
            if "overtime" in q:
                return f"There are {val} employees who work overtime."
            if "research" in q:
                return f"There are {val} employees in Research & Development."
            if "sales" in q:
                return f"There are {val} employees in Sales."
            if "human" in q and "resource" in q:
                return f"There are {val} employees in Human Resources."
            return f"There are {val} employees."

        if "average" in q or "avg" in q or "متوسط" in q:
            return f"The average is {val}."

        if "maximum" in q or "max" in q or "أعلى" in q:
            return f"The maximum is {val}."

        if "minimum" in q or "min" in q or "أقل" in q:
            return f"The minimum is {val}."

        return str(val)

    lines = [", ".join(cols)] + [", ".join(str(x) for x in r) for r in rows[:10]]
    table = "\n".join(lines)
    return f"Here are the results:\n```text\n{table}\n```"


def normalize_sql(raw: str) -> str:
    sql = clean_sql(raw)
    sql = fix_common_columns(sql)
    sql = fix_department_values(sql)
    return sql
