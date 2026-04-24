import re
import os
import duckdb
import json
from groq import Groq
from app.core.config import settings
from app.services.llm_service import llm
def _get_duckdb_table_expr(file_path: str) -> str:
    """Returns the correct DuckDB read function based on file type."""
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.csv':
        return f"read_csv_auto('{file_path}')"
    elif ext.lower() == '.json':
        return f"read_json_auto('{file_path}')"
    raise ValueError(f"Unsupported file format: {ext}")

def _extract_schema(file_path: str) -> str:
    """Uses DuckDB to grab the column names and data types."""
    table_expr = _get_duckdb_table_expr(file_path)
    
    # DuckDB's DESCRIBE command gives us the schema
    query = f"DESCRIBE SELECT * FROM {table_expr}"
    
    with duckdb.connect() as con:
        # Returns a list of tuples: [('column_name', 'VARCHAR', ...), ...]
        schema_data = con.execute(query).fetchall()
        
    # Format into a clean string for the LLM
    schema_str = "\n".join([f"- {row[0]} ({row[1]})" for row in schema_data])
    return schema_str


def _clean_json_string(raw_text: str) -> str:
    """Strips markdown code blocks from LLM output if present."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:] # Remove ```json
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:] # Remove generic ```
        
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3] # Remove ending ```
        
    return cleaned.strip()

def _generate_sql_queries(schema: str, table_expr: str) -> list[str]:
    """Uses native Tool Calling to guarantee a structured array of SQL queries."""
    prompt = f"""
    You are an expert data analyst. I have a dataset with this schema:
    {schema}
    
    Write 3 separate, valid DuckDB SQL queries to extract the most interesting insights.
    The table name you MUST query from is exactly: {table_expr}
    """
    
    # 1. Define the exact strict schema we want
    tools = [
        {
            "type": "function",
            "function": {
                "name": "execute_duckdb_queries",
                "description": "Executes a list of SQL queries against the DuckDB engine.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "An array of exactly 3 valid DuckDB SQL strings."
                        }
                    },
                    "required": ["queries"]
                }
            }
        }
    ]
    
    response = llm.get_response(
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        # 2. FORCE the model to use our specific tool. No chatting allowed.
        tool_choice={"type": "function", "function": {"name": "execute_duckdb_queries"}}
    )
    
    # 3. Extract the guaranteed JSON arguments from the tool call
    tool_call = response.tool_calls[0]
    arguments_json = tool_call.function.arguments
    
    print(f"\n--- GUARANTEED TOOL JSON ---\n{arguments_json}\n----------------------------\n")
    
    # 4. Parse it safely. It will never contain markdown now.
    data = json.loads(arguments_json)
    return data.get("queries", [])

def process_file_with_ai(file_path: str) -> str:
    """The main orchestrator function for the worker to call."""
    if not settings.AI_API_KEY:
        raise ValueError("AI API Key not configured.")

    table_expr = _get_duckdb_table_expr(file_path)
    schema = _extract_schema(file_path)
    
    # 1. Get our list of queries
    queries = _generate_sql_queries(schema, table_expr)
    
    all_results = []
    
    # 2. Execute them one by one
    with duckdb.connect() as con:
        for idx, query in enumerate(queries):
            try:
                results = con.execute(query).fetchall()
                columns = [desc[0] for desc in con.description]
                
                # Store the result for this specific query
                all_results.append({
                    "insight_number": idx + 1,
                    "columns": columns,
                    "data": results[:5] # Limit to 5 rows per query so we don't blow up the LLM context window
                })
            except Exception as e:
                print(f"[Warning] Query {idx + 1} failed to execute: {query}. Error: {e}")
                # If one query fails, we continue and just process the successful ones!
                continue
                
    if not all_results:
         raise ValueError("All generated SQL queries failed to execute.")

    # 3. Summarize the combined results
    summary_prompt = f"""
    I ran multiple SQL queries to find insights. 
    Here are the raw results:
    {json.dumps(all_results, indent=2)}
    
    Write a concise, 3-sentence executive summary of what these numbers mean.
    """
    
    summary_response = llm.get_response(
        messages=[{"role": "user", "content": summary_prompt}],
    )
    
    return summary_response.content