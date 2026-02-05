"""
HR Assistant Chatbot (Streamlit)
"""

import os
import json
import torch
import streamlit as st
import re
from setup_models import load_groq_client
from sql_utils import normalize_sql, pretty_answer
from local_sql import ask_local_sql
from db import init_db, execute_sql


# Init DB
init_db()


# Cloud SQL cleaning helpers
def _clean_sql_cloud(sql: str) -> str:
    s = (sql or "").strip()
    s = s.replace("```sql", "").replace("```", "").strip()
    s = re.sub(r"^\s*sql\s*:\s*", "", s, flags=re.IGNORECASE).strip()

    # Keep only the SQL part (remove explanation line if present)
    # Stop at: first ';' OR a line that starts with '-- Explanation:'
    s = re.split(r";\s*|\n\s*--\s*Explanation\s*:", s, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    # Extract from first SELECT/WITH onward
    m = re.search(r"\b(with\b[\s\S]*?\bselect\b|select\b)[\s\S]*", s, flags=re.IGNORECASE)
    if m:
        s = m.group(0).strip()

    return s.strip()



def _fix_common_columns_cloud(sql: str) -> str:
    replacements = {
        "department_name": "Department",  
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


# Page config
st.set_page_config(page_title="HR Assistant Chatbot", page_icon="🤖", layout="centered")
st.title("🤖 HR Assistant Chatbot")


# Theme + sidebar styling
st.markdown(
    """
    <style>
    .stApp { background-color: #ffffff; }

    section[data-testid="stSidebar"] > div {
        background-color: #4b2c6f;
        padding-top: 1rem;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stCaption {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #ffffff !important;
        color: #2b2b2b !important;
        border-radius: 10px !important;
        border: none !important;
    }

    ul[role="listbox"] * { color: #2b2b2b !important; }

    section[data-testid="stSidebar"] .stButton button,
    section[data-testid="stSidebar"] .stDownloadButton button {
        background-color: #e56ba8 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] .stButton button:hover,
    section[data-testid="stSidebar"] .stDownloadButton button:hover {
        background-color: #d85697 !important;
    }

    .sidebar-footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        color: #f0d9ec;
        font-size: 12px;
        opacity: 0.85;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []


def _make_sql_prompt(question: str) -> str:
    return f"""
You are an expert data analyst specialized in SQLite.

Your task is to convert the user question into ONE valid, read-only SQL query
and add a very brief explanation.

====================
GENERAL RULES
====================
- Output ONLY:
  1) The SQL query
  2) One short explanation line starting with: -- Explanation:
- Do NOT use markdown or code fences.
- The query must be a SINGLE statement.
- Allowed: SELECT or WITH ... SELECT only.
- Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH.
- Use valid SQLite syntax only.
- Always use the table name: employees.
- Never invent columns or tables.

====================
TABLE SEMANTICS
====================
employees table represents company employees.

Key meanings:
- Attrition = 'Yes' → employee has left the company.
- Attrition = 'No'  → employee is still employed.
- OverTime = 'Yes' / 'No' indicates overtime work.
- MonthlyIncome represents salary.
- JobSatisfaction, EnvironmentSatisfaction, WorkLifeBalance are numeric scores.
- Age is employee age.
- Gender is employee gender.
- Department is department name.
- JobRole is job title.

There is NO departure date column.
There is NO hire date column.

====================
QUESTION INTERPRETATION
====================
- "How many", "count", "number", "كم عدد" → COUNT(*)
- "Average", "mean", "متوسط" → AVG(column)
- "Highest", "أعلى" → MAX(column)
- "Lowest", "أقل" → MIN(column)
- "Rate", "percentage" →
  AVG(CASE WHEN condition THEN 1.0 ELSE 0 END)
- "Per", "by", "لكل", "حسب" → GROUP BY
- Ordering requests → ORDER BY
- Listing rows → LIMIT 10 unless stated otherwise.

====================
LANGUAGE HANDLING
====================
Arabic mappings:
- "الذين تركوا العمل" → Attrition = 'Yes'
- "الموظفين الحاليين" → Attrition = 'No'
- "حسب القسم" → GROUP BY Department
- "حسب الوظيفة" → GROUP BY JobRole

====================
EXPLANATION RULE
====================
- Explanation must be ONE simple sentence.
- No technical jargon.
- No SQL keywords in explanation.
- Match the user's language (Arabic or English).

====================
FINAL INSTRUCTION
====================
Return:
- The SQL query
- Then one line:
  -- Explanation: <short explanation>


Question:
{question}

SQL:
""".strip()


# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    model_name = st.selectbox(
        "Select Model",
        ("Local Qwen (Offline)", "Cloud (Groq)"),
    )

    groq_key_input = ""
    if model_name == "Cloud (Groq)":
        groq_key_input = st.text_input("Groq API Key", type="password")

    # Download chat
    messages = st.session_state.get("messages", [])
    chat_text = ""
    for m in messages:
        role = "User" if m.get("role") == "user" else "Assistant"
        chat_text += f"{role}:\n{m.get('content','')}\n\n"

    st.download_button(
        label="⬇️ Download Chat",
        data=chat_text if chat_text else "No messages yet.",
        file_name="hr_chat_history.txt",
        mime="text/plain",
        disabled=(len(messages) == 0),
        key="download_chat_btn",
    )

    # Sidebar footer
    st.markdown('<div class="sidebar-footer">Developed by Jana</div>', unsafe_allow_html=True)


# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# Chat input
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
            if model_name == "Local Qwen (Offline)":
                response_text = ask_local_sql(prompt)
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
                response_text = pretty_answer(prompt, cols, rows)

            placeholder.empty()
            st.markdown(response_text if response_text else "No response.")

        except Exception as e:
            placeholder.empty()
            response_text = f"Runtime error: {e}"
            st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
