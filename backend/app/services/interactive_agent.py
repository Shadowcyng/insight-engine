# app/services/interactive_agent.py
import json
import structlog
from app.services.llm_service import llm
from app.services.analytics_engine import execute_duckdb_queries

log = structlog.get_logger()

class InteractiveAgent:
    """
    Consolidated Orchestrator: Handles the conversation and tool-calling loop.
    """
    def __init__(self, upload_id: int, file_path: str, websocket):
        self.upload_id = upload_id
        self.file_path = file_path
        self.websocket = websocket

    async def run(self, question: str):
        # 1. Define tools (DuckDB focus)
        tools = [{
            "type": "function",
            "function": {
                "name": "execute_duckdb_queries",
                "description": "Query the CSV data using SQL. Table name is 'df'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": { "type": "array", "items": {"type": "string"} }
                    },
                    "required": ["queries"]
                }
            }
        }]

        messages = [
            {"role": "system", "content": (
            "You are a data expert. CRITICAL: Before answering any data questions, "
            "you MUST run 'DESCRIBE df' to see the actual column names. "
            "Do not guess column names. Use the 'execute_duckdb_queries' tool "
            "to get the schema first, then run your analysis."
            )},
            {"role": "user", "content": f"Context: {self.file_path}. Question: {question}"}
        ]

        # --- STEP 1: Initial Thought ---
        await self.websocket.send_json({"type": "log", "message": "🤖 AI is planning the analysis..."})
        response = llm.get_response(messages=messages, tools=tools)

        # --- STEP 2: The Tool Loop ---
        if response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                args = json.loads(tool_call.function.arguments)
                
                await self.websocket.send_json({"type": "log", "message": f"📊 Running DuckDB: {args['queries'][0]}..."})
                
                # Use the function from analytics_engine.py
                results = execute_duckdb_queries(args['queries'], self.file_path)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "execute_duckdb_queries",
                    "content": json.dumps(results)
                })

            # --- STEP 3: Final Synthesis ---
            await self.websocket.send_json({"type": "log", "message": "✍️ Finalizing insight..."})
            final_response = llm.get_response(messages=messages)
            content = final_response.content
        else:
            content = response.content

        # --- STEP 4: Send Final Answer ---
        await self.websocket.send_json({
            "type": "query_result",
            "upload_id": self.upload_id,
            "answer": content
        })