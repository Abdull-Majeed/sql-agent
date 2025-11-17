# MySQL Agent

A **MySQL Agent** powered by **Google Gemini**.  
It converts **natural language questions** into **safe SQL queries** and executes them on your database

---

## Features

- ✅ Natural Language → SQL using Gemini (text generation API)
- ✅ Safe SQL filtering: Only `SELECT`, `SHOW`, `DESCRIBE` queries allowed
- ✅ Auto-sanitizes dangerous SQL commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`)
- ✅ Interactive command-line interface
- ✅ Works asynchronously for faster MySQL queries

---

## Requirements

- Python 3.11+
- MySQL database
- Google Gemini API key
- Python packages:

```bash
pip install aiomysql python-dotenv google-genai```


Setup

1. Clone the repository
```bash
git clone https://github.com/Abdull-Majeed/sql-agent.git
cd sql-agent```


2. Create a .env file in the project root

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
GOOGLE_API_KEY=your_google_gemini_api_key```


3. Activate your virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows 
```

4. Install dependencies

```bash
pip install -r requirements.txt```


5. Run the agent

```bash
python sql-agent.py```