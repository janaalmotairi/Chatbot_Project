"""
local_sql.py

Text-to-SQL using local Qwen model.
"""

import re
import torch
from setup_models import load_local_qwen
from db import execute_sql
from sql_utils import normalize_sql, pretty_answer


_MODEL = None
_TOKENIZER = None


def _get_local_qwen():
    global _MODEL, _TOKENIZER
    if _MODEL is None or _TOKENIZER is None:
        _MODEL, _TOKENIZER = load_local_qwen()
    return _MODEL, _TOKENIZER


def _clean_sql(sql: str) -> str:
    s = (sql or "").strip()
    s = s.replace("```sql", "").replace("```", "").strip()
    s = re.sub(r"^\s*sql\s*:\s*", "", s, flags=re.IGNORECASE).strip()

    m = re.search(r"(select\b.*)", s, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return s.strip()

    return m.group(1).split(";")[0].strip()


def _fix_common_columns(sql: str) -> str:
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
    for k, v in replacements.items():
        out = re.sub(rf"\b{k}\b", v, out, flags=re.IGNORECASE)
    return out



def ask_local_sql(question: str) -> str:
    model, tokenizer = _get_local_qwen()

    prompt = f"""
You are a SQL generator.
Rules:
- Output ONLY a valid SQLite SELECT query.
- Table name: employees
- No explanations.

Question:
{question}

SQL:
""".strip()

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        output = model.generate(inputs.input_ids, max_new_tokens=140, do_sample=False)

    raw = tokenizer.decode(
        output[0][inputs.input_ids.shape[-1]:],
        skip_special_tokens=True
    )

    sql = normalize_sql(raw)


    if not sql.lower().startswith("select"):
        return "تعذر إنشاء استعلام SQL صالح." if any("\u0600" <= ch <= "\u06FF" for ch in question) else "Failed to generate valid SQL."

    cols, rows = execute_sql(sql)
    return pretty_answer(question, cols, rows)
