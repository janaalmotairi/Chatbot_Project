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


def ask_local_sql(question: str) -> str:
    model, tokenizer = _get_local_qwen()

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

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        output = model.generate(inputs.input_ids, max_new_tokens=140, do_sample=False)

    raw = tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

    sql = normalize_sql(raw)
    if not sql.lower().startswith("select"):
        return f"Invalid SQL generated.\nRaw: {raw.strip()[:200]}"

    try:
        cols, rows = execute_sql(sql)
    except Exception as e:
        return f"SQL execution error: {e}\nSQL was: {sql}"

    if not rows:
        return "No results found."

    return pretty_answer(question, cols, rows)
