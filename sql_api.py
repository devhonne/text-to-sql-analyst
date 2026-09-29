"""
Step 4: a tiny API so a web page can ask questions of the database.

Setup:
    pip install fastapi uvicorn

Run:
    uvicorn sql_api:app --reload --port 8001

Then open sql_index.html in your browser.
Reuses the exact same generate_sql / is_safe / run_query logic as ask.py.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

from ask import generate_sql, is_safe, run_query, SCHEMA

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
print("Ready. Schema loaded:\n" + SCHEMA)


class Question(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: Question):
    sql = generate_sql(_client, payload.question)
    safe, reason = is_safe(sql)

    if not safe:
        return {
            "sql": sql,
            "blocked": True,
            "reason": reason,
            "columns": [],
            "rows": [],
        }

    try:
        cols, rows = run_query(sql)
    except Exception as e:
        return {
            "sql": sql,
            "blocked": False,
            "error": str(e),
            "columns": [],
            "rows": [],
        }

    return {
        "sql": sql,
        "blocked": False,
        "columns": cols,
        "rows": rows,
    }
