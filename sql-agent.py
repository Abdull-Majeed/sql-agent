import os
import asyncio
import aiomysql
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()

GENAI_MODEL = os.getenv("GENAI_MODEL", "models/gemini-2.5-flash")
db_pool = None


async def setup_mysql_connection():
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            db=os.getenv("MYSQL_DATABASE", "test"),
            charset="utf8mb4",
            autocommit=True,
        )
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                if (await cursor.fetchone())[0] == 1:
                    print("✅ Connected to MySQL")
                    return True
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        return False

SAFE_SQL = ("SELECT", "SHOW", "DESCRIBE", "DESC")


async def execute_sql(query: str):
    global db_pool
    if not query.upper().startswith(SAFE_SQL):
        return "Only SELECT, SHOW, DESCRIBE are allowed."

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                rows = await cursor.fetchall()

        if not rows:
            return "No rows found."

        headers = list(rows[0].keys())
        out = " | ".join(headers) + "\n" + "-" * (len(headers) * 15) + "\n"
        for r in rows[:20]:
            out += " | ".join(str(r[h]) for h in headers) + "\n"
        if len(rows) > 20:
            out += f"\n... and {len(rows) - 20} more rows\n"
        out += f"\nTotal rows: {len(rows)}"
        return out
    except Exception as e:
        return f"SQL Error: {e}"

gen_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

async def list_models():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: gen_client.models.list())

async def gemini_chat(prompt: str, retries=3, delay=2):
    loop = asyncio.get_running_loop()
    for attempt in range(retries):
        def blocking_call():
            try:
                resp = gen_client.models.generate_content(
                    model=GENAI_MODEL,
                    contents=prompt
                )
                return resp.text
            except Exception as e:
                return f"Geminii API error: {e}"

        result = await loop.run_in_executor(None, blocking_call)
        if not result.startswith("❌"):
            return result
        if attempt < retries - 1:
            print("Model busy or API error, retrying...")
            time.sleep(delay)
    return result

async def generate_sql_from_nl(question: str):
    # Get actual tables in DB
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = [row[0] for row in await cursor.fetchall()]

    table_list = ", ".join(tables)

    prompt = f"""
  You are a MySQL assistant. Generate a SAFE SQL query using only the tables in this database: {table_list}.
- Only use SELECT, SHOW, DESCRIBE statements.
- Never modify data (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
- Return ONLY the SQL query. Do NOT include explanations or placeholders.
- And in tables, use only name, id and etc from the database.
- Make sure the SQL uses real table names from this database.

User question:
{question}
"""

    response = await gemini_chat(prompt)

    # Search for first line starting with valid SQL keyword
    sql_lines = [line.strip("` ").strip() for line in response.split("\n")]
    sql = next((line for line in sql_lines if line.upper().startswith(("SELECT","SHOW","DESCRIBE","DESC"))), None)

    if not sql:
        return "SELECT 'Error: Could not generate SQL';"

    # Sanitize
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
    if any(w in sql.upper() for w in forbidden):
        return "SELECT 'Error: Forbidden SQL keyword detected';"

    return sql

async def main():
    if not os.getenv("GOOGLE_API_KEY"):
        print("Missing GOOGLE_API_KEY")
        return

    print("Connecting to MySQL…")
    if not await setup_mysql_connection():
        return
    try:
        while True:
            q = input("Ask a question or 'quit': ").strip()
            if q.lower() in ("quit"):
                break

            print("Generating SQL query…")
            sql = await generate_sql_from_nl(q)
            print(f"\nSQL Generated: {sql}\n")
            result = await execute_sql(sql)
            print("Result: ", result)

    finally:
        global db_pool
        if db_pool:
            db_pool.close()
            await db_pool.wait_closed()
            print("MySQL connection closed")

if __name__ == "__main__":
    asyncio.run(main())
