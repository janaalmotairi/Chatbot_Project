from db import execute_sql
from sql_utils import normalize_sql, pretty_answer

def ask_cloud_sql(client, question: str) -> str:
    prompt = f"""
You are a SQL generator.
Rules:
- Output ONLY a valid SQLite SELECT query.
- Table name: employees
- No explanations.
- Use ONLY these exact column names:
  Age, Attrition, Department, JobRole, MonthlyIncome, OverTime, EducationField, JobSatisfaction, WorkLifeBalance
- Department values are EXACTLY:
  'Human Resources', 'Research & Development', 'Sales'
Question:
{question}
SQL:
""".strip()

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Return SQL only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=200,
    )

    raw = completion.choices[0].message.content
    sql = normalize_sql(raw)

    if not sql.lower().startswith("select"):
        return f"Invalid SQL generated.\nRaw: {str(raw).strip()[:200]}"

    try:
        cols, rows = execute_sql(sql)
    except Exception as e:
        return f"SQL execution error: {e}\nSQL was: {sql}"

    if not rows:
        return "No results found."

    return pretty_answer(question, cols, rows)
