# agent.py

import os
import json
from openai import OpenAI
import db
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY') or os.getenv('GROQ_API_KEY'),
    base_url="https://api.groq.com/openai/v1",
    timeout=30,
)

# --- Tool definitions: what the model is allowed to ask for ---

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Run a single read-only SELECT query on the analytics database and "
                "return the rows. Use this to answer any question about sales data. "
                "Schema: sales(id, product, category, region, amount DECIMAL, "
                "sold_at DATE). amount is the sale value in rupees; sold_at is the "
                "date of sale."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A MySQL SELECT statement"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sales_report",
            "description": "Get chart-ready total sales grouped by 'product', "
                        "'category', or 'region'. Use when the user wants a "
                        "report, breakdown, comparison, or chart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "enum": ["product", "category", "region"]}
                },
            },
        },
    },
]

# --- Map tool names to the real Python functions ---
available_functions = {
    "run_sql": db.run_sql,
    "sales_report": db.sales_report
}

SYSTEM_PROMPT = (
    "You are a data analyst. Answer questions about sales by writing a SELECT query "
    "and calling run_sql. Amounts are in Indian Rupees (₹). After getting rows, give "
    "a short, clear answer. Never invent numbers; only use what the query returns."
)

def run_agent(user_message, history=None, max_steps=6):
    messages = history or [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_message})
    collected = []                              # raw tool outputs (for charts later)

    for _ in range(max_steps):                  # capped loop = can't run forever
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools,
            temperature=0.1,                    # low = factual, stable SQL
        )
        msg = response.choices[0].message
        messages.append(msg)

        # No tool call -> the model is giving its final answer
        if not msg.tool_calls:
            return msg.content, collected

        # The model asked to run a tool
        for call in msg.tool_calls:
            fn = available_functions[call.function.name]
            args = json.loads(call.function.arguments)
            result = fn(**args)                 # YOUR code runs the tool
            collected.append({"tool": call.function.name, "args": args, "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str),
            })
        # loop again so the model can use the result

    return "Sorry, I couldn't finish that in time.", collected

""" **Concept learned (the agent loop):** look at the `for` loop. Each pass: call the
model → if it asked for a tool, run the tool and feed the result back → repeat.
When the model stops asking for tools and just answers, the loop ends. *That loop
is the agent.* You're not hardcoding questions — the model decides each step. """