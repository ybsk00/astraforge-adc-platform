import os
import httpx
from pathlib import Path

def get_env():
    env = {}
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key.strip()] = value.strip().strip('"').strip("'")
    return env

def apply_sql():
    env = get_env()
    url = env.get("SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return

    sql_path = Path("supabase/schema_v2_supplement.sql")
    if not sql_path.exists():
        print(f"Error: {sql_path} not found")
        return

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Supabase SQL API endpoint
    # Note: Supabase doesn't have a public SQL execution endpoint for service role key via REST easily
    # but we can use the admin API if available or just try to use the CLI again with correct flags.
    # Actually, the best way is to use the CLI correctly.
    
    print("Attempting to execute SQL via Supabase CLI with correct flags...")
    # Based on Supabase CLI docs, 'db query' reads from stdin if no query is provided.
    # We will use subprocess to pipe the SQL.
    import subprocess
    
    try:
        process = subprocess.Popen(
            ["npx", "supabase", "db", "query"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        stdout, stderr = process.communicate(input=sql)
        
        if process.returncode == 0:
            print("SQL executed successfully!")
            print(stdout)
        else:
            print(f"Error executing SQL (Exit code {process.returncode}):")
            print(stderr)
            print(stdout)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    apply_sql()
