"""
HR Assistant Chatbot (Streamlit)
"""

import os
import json
import torch
import streamlit as st
import re
from setup_models import load_groq_client

# Local pipeline (cleaning + column fixes + pretty answers)
from local_sql import ask_local_sql

# DB
from db import init_db, execute_sql


# ---------------------------------------------------------------------
# Init DB once
# ---------------------------------------------------------------------
init_db()


# ---------------------------------------------------------------------
# Cloud helpers (clean SQL + fix columns + format result)
# ---------------------------------------------------------------------
def _clean_sql_cloud(sql: str) -> str:
    s = (sql or "").strip()
    s = s.replace("```sql", "").replace("```", "").strip()
    s = re.sub(r"^\s*sql\s*:\s*", "", s, flags=re.IGNORECASE).strip()

    m = re.search(r"(select\b.*)", s, flags=re.IGNORECASE | re.DOTALL)
    if m:
        s = m.group(1).strip()

    return s.split(";")[0].strip()


def _fix_common_columns_cloud(sql: str) -> str:
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


def _format_result(cols, rows) -> str:
    if not rows:
        return "No results found."

    if len(cols) == 1 and len(rows) == 1:
        return str(rows[0][0])

    return "\n".join(
        [", ".join(cols)] +
        [", ".join(str(x) for x in r) for r in rows[:10]]
    )


# ---------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------
st.set_page_config(page_title="HR Assistant Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 HR Assistant Chatbot")


# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


def _make_sql_prompt(question: str) -> str:
    return f"""
You are a data analyst. Convert the user question into a SQL query only.
Rules:
- Output ONLY SQL, no explanation.
- Use table name: employees
- Use valid SQLite syntax.

Question:
{question}

SQL:
""".strip()


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    model_name = st.selectbox(
        "Select Model",
        ("Local Qwen (Offline)", "Cloud (Groq)"),
    )

    groq_key_input = ""
    if model_name == "Cloud (Groq)":
        groq_key_input = st.text_input("Groq API Key", type="password")


# ---------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# ---------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------
prompt = st.chat_input("Ask a question (English / Arabic)...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response_text = ""

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ Processing...")

        try:
            # ==========================================================
            # LOCAL MODE
            # ==========================================================
            if model_name == "Local Qwen (Offline)":
                response_text = ask_local_sql(prompt)

            # ==========================================================
            # CLOUD MODE (FIXED)
            # ==========================================================
            else:
                if not groq_key_input:
                    raise ValueError("Please enter your Groq API Key in the sidebar.")

                client = load_groq_client(groq_key_input)

                sql_prompt = _make_sql_prompt(prompt)

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You generate SQL queries only."},
                        {"role": "user", "content": sql_prompt},
                    ],
                    temperature=0,
                )

                sql_query = completion.choices[0].message.content
                sql_query = _clean_sql_cloud(sql_query)
                sql_query = _fix_common_columns_cloud(sql_query)

                cols, rows = execute_sql(sql_query)
                response_text = _format_result(cols, rows)

            placeholder.empty()
            st.markdown(response_text if response_text else "No response.")

        except Exception as e:
            placeholder.empty()
            response_text = f"Runtime error: {e}"
            st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
