import re
from typing import Optional
from .llm import chat_completion

# Một vài intent rule-based đơn giản; có thể mở rộng dần
RULES = [
    (re.compile(r"(doanh thu|revenue|sales)", re.I), "QUERY_REVENUE"),
    (re.compile(r"(khách hàng|customer|client)", re.I), "QUERY_CUSTOMER"),
    (re.compile(r"(đơn hàng|order)", re.I), "QUERY_ORDER"),
    (re.compile(r"(khoản vay|loan|outstanding|balance)", re.I), "QUERY_LOAN"),
]

INTENT_SYSTEM = """You are an intent classifier for Text2SQL system.
Return one UPPER_SNAKE_CASE intent label that best matches the user query.
If unclear, return GENERIC_QUERY."""
INTENT_LIST = "Possible intents: QUERY_REVENUE, QUERY_CUSTOMER, QUERY_ORDER, QUERY_LOAN, GENERIC_QUERY."

def detect_intent(user_query: str) -> str:
    for pat, intent in RULES:
        if pat.search(user_query):
            return intent
    # Fallback LLM
    msg = [
        {"role": "system", "content": INTENT_SYSTEM},
        {"role": "user", "content": f"{INTENT_LIST}\n\nUser query: {user_query}\nIntent:"},
    ]
    out = chat_completion(msg).strip()
    # vệ sinh output
    out = re.sub(r"[^A-Z_]", "", out)
    return out or "GENERIC_QUERY"
