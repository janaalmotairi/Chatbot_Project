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

def pretty_answer(question: str, cols, rows) -> str:
    """Format SQL results into a human-friendly answer (Arabic/English)."""
    question = question or ""
    is_ar = any("\u0600" <= ch <= "\u06FF" for ch in question)
    q = question.lower()

    if not rows:
        return "لا توجد نتائج." if is_ar else "No results found."

    # Single scalar result
    if len(cols) == 1 and len(rows) == 1:
        val = rows[0][0]

        if "how many" in q or "count" in q or "كم" in q or "عدد" in q:
            return (f"عدد الموظفين هو {val}." if is_ar else f"There are {val} employees.")

        if "average" in q or "avg" in q or "متوسط" in q:
            try:
                v = round(float(val), 2)
            except Exception:
                v = val
            return (f"متوسط القيمة هو {v}." if is_ar else f"The average value is {v}.")

        if "maximum" in q or "max" in q or "أعلى" in q:
            return (f"أعلى قيمة هي {val}." if is_ar else f"The maximum value is {val}.")

        if "minimum" in q or "min" in q or "أقل" in q:
            return (f"أقل قيمة هي {val}." if is_ar else f"The minimum value is {val}.")

        return str(val)

        # Tabular results (show up to 10 rows) - friendly format
    shown = rows[:10]
    if is_ar:
        lines = [f"- {', '.join(str(x) for x in r)}" for r in shown]
        header = "النتائج:\n"
        return header + "\n".join(lines)
    else:
        lines = [f"- {', '.join(str(x) for x in r)}" for r in shown]
        header = "Results:\n"
        return header + "\n".join(lines)


def fix_common_columns(sql: str) -> str:
    replacements = {
    "department_name": "Department",
    "dept_name": "Department",
    "dept": "Department",
    "department": "Department",

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


def normalize_sql(raw: str) -> str:
    sql = clean_sql(raw)
    sql = fix_common_columns(sql)
    sql = fix_department_values(sql)
    return sql
