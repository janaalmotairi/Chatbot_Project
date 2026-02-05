import pandas as pd
from sqlalchemy import create_engine
from transformers import pipeline


def load_and_prep_data(file_path: str):
    """
    Load the HR dataset and store it into a local SQLite database.

    Notes:
    - Table name: employees
    """
    df = pd.read_csv(file_path)

    # Build an employee profile field for context (optional utility).
    df["Employee_Profile"] = (
        "Age: " + df["Age"].astype(str) +
        ", Department: " + df["Department"].astype(str) +
        ", JobRole: " + df["JobRole"].astype(str) +
        ", MonthlyIncome: " + df["MonthlyIncome"].astype(str) +
        ", OverTime: " + df["OverTime"].astype(str) +
        ", Attrition: " + df["Attrition"].astype(str)
    )

    db_engine = create_engine("sqlite:///hr_database.db")
    df.to_sql("employees", db_engine, if_exists="replace", index=False)

    return df, db_engine
