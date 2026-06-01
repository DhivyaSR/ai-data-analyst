#db.py

import os
import mysql.connector
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

def get_connection():
    """Establish a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
def run_sql(query: str):
    """Run a READ-ONLY SQL query and return the rows.

    SAFETY: we only allow SELECT. The LLM writes the SQL, and we must never let a
    generated query delete or change data. This check is the guardrail.
    """
    clean = query.strip().lower()
    if not clean.startswith("select"):
        return {"error": "Only SELECT queries are allowed."}
    # Block multiple statements (e.g. "select ...; drop table ...")
    if ";" in query.strip().rstrip(";"):
        return {"error": "Only a single statement is allowed."}

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query)
        rows = cur.fetchall()
        # money/dates come back as Decimal/date -> make them plain for JSON later
        for r in rows:
            for k, v in r.items():
                r[k] = float(v) if hasattr(v, "is_signed") else (str(v) if not isinstance(v, (int, float, str)) else v)
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close(); conn.close()

def sales_report(group_by: str = "product"):
    """Return total sales grouped by 'product', 'category', or 'region'.
    Output is chart-ready structured data."""
    allowed = {"product", "category", "region"}
    if group_by not in allowed:
        return {"error": f"group_by must be one of {allowed}"}
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        f"SELECT {group_by} AS label, SUM(amount) AS total "
        f"FROM sales GROUP BY {group_by} ORDER BY total DESC"
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    for r in rows:
        r["total"] = float(r["total"])
    # the "type" marker tells the frontend "this is chartable"
    return {"type": "sales_report", "group_by": group_by, "rows": rows}