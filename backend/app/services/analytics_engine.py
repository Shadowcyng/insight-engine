import re
import os
import duckdb
import json
from groq import Groq
from app.core.config import settings
from app.services.llm_service import llm
import structlog
from typing import List,  Dict, Any

log = structlog.get_logger()

def _get_duckdb_table_expr(file_path: str) -> str:
    """Returns the correct DuckDB read function based on file type."""
    log.debug("getting_duckdb_table_expression", file_path=file_path)
    try:
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.csv':
            result = f"read_csv_auto('{file_path}')"
            log.debug("duckdb_expression_created", file_path=file_path, type="csv")
            return result
        elif ext.lower() == '.json':
            result = f"read_json_auto('{file_path}')"
            log.debug("duckdb_expression_created", file_path=file_path, type="json")
            return result
        else:
            log.error("unsupported_file_format_for_duckdb", file_path=file_path, extension=ext)
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        log.error("_get_duckdb_table_expr_failed", file_path=file_path, error=str(e))
        raise

def _extract_schema(file_path: str) -> str:
    """Uses DuckDB to grab the column names and data types."""
    log.info("extracting_schema_from_file", file_path=file_path)
    try:
        table_expr = _get_duckdb_table_expr(file_path)
        
        # DuckDB's DESCRIBE command gives us the schema
        query = f"DESCRIBE SELECT * FROM {table_expr}"
        log.debug("executing_describe_query", file_path=file_path)
        
        with duckdb.connect() as con:
            # Returns a list of tuples: [('column_name', 'VARCHAR', ...), ...]
            schema_data = con.execute(query).fetchall()
        
        log.debug("schema_extracted_successfully", file_path=file_path, column_count=len(schema_data))
        # Format into a clean string for the LLM
        schema_str = "\n".join([f"- {row[0]} ({row[1]})" for row in schema_data])
        return schema_str
    except Exception as e:
        log.error("_extract_schema_failed", file_path=file_path, error=str(e))
        raise


def _clean_json_string(raw_text: str) -> str:
    """Strips markdown code blocks from LLM output if present."""
    log.debug("cleaning_json_string_from_llm_output")
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:] # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:] # Remove generic ```
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3] # Remove ending ```
            
        result = cleaned.strip()
        log.debug("json_string_cleaned_successfully")
        return result
    except Exception as e:
        log.error("_clean_json_string_failed", error=str(e))
        raise

def _generate_sql_queries(schema: str, table_expr: str) -> list[str]:
    """Uses native Tool Calling to guarantee a structured array of SQL queries."""
    log.info("generating_sql_queries_with_llm")
    try:
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
        
        log.debug("calling_llm_with_tool_choice")
        response = llm.get_response(
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            # 2. FORCE the model to use our specific tool. No chatting allowed.
            tool_choice={"type": "function", "function": {"name": "execute_duckdb_queries"}}
        )
        
        # 3. Extract the guaranteed JSON arguments from the tool call
        tool_call = response.tool_calls[0]
        arguments_json = tool_call.function.arguments
        
        log.debug("sql_queries_generated_by_llm", query_count=3)
        
        # 4. Parse it safely. It will never contain markdown now.
        data = json.loads(arguments_json)
        queries = data.get("queries", [])
        log.info("sql_queries_extracted_successfully", query_count=len(queries))
        return queries
    except Exception as e:
        log.error("_generate_sql_queries_failed", error=str(e))
        raise

def process_file_with_ai(file_path: str) -> str:
    """The main orchestrator function for the worker to call."""
    log.info("process_file_with_ai_started", file_path=file_path)
    try:
        if not settings.AI_API_KEY:
            log.error("ai_api_key_not_configured")
            raise ValueError("AI API Key not configured.")

        table_expr = _get_duckdb_table_expr(file_path)
        schema = _extract_schema(file_path)
        
        # 1. Get our list of queries
        queries = _generate_sql_queries(schema, table_expr)
        log.debug("sql_queries_generation_completed", query_count=len(queries))
        
        all_results = []
        
        # 2. Execute them one by one
        log.info("executing_sql_queries", query_count=len(queries))
        with duckdb.connect() as con:
            for idx, query in enumerate(queries):
                try:
                    log.debug("executing_sql_query", query_index=idx+1, query=query[:100])
                    results = con.execute(query).fetchall()
                    columns = [desc[0] for desc in con.description]
                    
                    # Store the result for this specific query
                    all_results.append({
                        "insight_number": idx + 1,
                        "columns": columns,
                        "data": results[:5] # Limit to 5 rows per query so we don't blow up the LLM context window
                    })
                    log.debug("sql_query_executed_successfully", query_index=idx+1, result_count=len(results))
                except Exception as e:
                    log.warning("sql_query_execution_failed", query_index=idx+1, error=str(e))
                    # If one query fails, we continue and just process the successful ones!
                    continue
        
        if not all_results:
            log.error("all_sql_queries_failed")
            raise ValueError("All generated SQL queries failed to execute.")

        log.debug("all_queries_executed_successfully", successful_count=len(all_results))

        # 3. Summarize the combined results
        summary_prompt = f"""
        I ran multiple SQL queries to find insights. 
        Here are the raw results:
        {json.dumps(all_results, indent=2)}
        
        Write a concise, 3-sentence executive summary of what these numbers mean.
        """
        
        log.info("generating_summary_from_results")
        summary_response = llm.get_response(
            messages=[{"role": "user", "content": summary_prompt}],
        )
        
        log.info("process_file_with_ai_completed_successfully", file_path=file_path)
        return summary_response.content
    except Exception as e:
        log.error("process_file_with_ai_failed", file_path=file_path, error=str(e))
        raise

def execute_duckdb_queries(queries: List[str], file_path: str) -> List[Dict[str, Any]]:
    """
    Executes analytical queries directly against a CSV file path.
    """
    results = []
    # Minor comment: DuckDB allows querying the file path directly using 'read_csv_auto'
    try:
        with duckdb.connect(database=':memory:') as con:
            # We create a view named 'df' so the LLM doesn't have to deal with long paths
            con.execute(f"CREATE VIEW df AS SELECT * FROM read_csv_auto('{file_path}')")
            
            for query in queries:
                log.info("executing_duckdb_query", query=query)
                # fetchdf() gets a pandas-like dataframe, to_dict converts it to JSON
                df = con.execute(query).fetchdf()
                results.append(df.to_dict(orient="records"))
                
        return results
    except Exception as e:
        log.error("duckdb_execution_failed", error=str(e))
        return [{"error": str(e)}]