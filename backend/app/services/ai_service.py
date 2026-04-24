import csv
import json
import os
# import google.generativeai as genai  <-- If using Gemini
# from openai import OpenAI
from prompt_toolkit import prompt
from app.core.config import settings
from app.services.llm_service import llm

def extract_data_sample(file_path: str, max_rows: int = 5) -> str:
    """Extracts headers and a few rows to give the LLM context."""
    _, ext = os.path.splitext(file_path)

    try:
        if ext.lower() == "csv":
            return _extract_csv_sample(file_path, max_rows)
        elif ext.lower() == "json":
            return _extract_json_sample(file_path, max_rows)
        else:
            return "Unsupported file format."
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
def _extract_csv_sample(file_path:str, max_rows: int)-> str:

    sample_data = []
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        if not headers:
            return "No headers found in the CSV file."
        
        sample_data.append(headers)

        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            sample_data.append(row)

        return json.dumps(sample_data, indent=2)

def _extract_json_sample(file_path: str, max_rows: int) -> str:
    """Helper to safely read JSON files (handles arrays and objects)."""
    with open(file_path, mode='r', encoding='utf-8') as file:
        data = json.load(file)
        
        # If it's a list of objects (standard data export)
        if isinstance(data, list):
            return json.dumps(data[:max_rows], indent=2)
            
        # If it's a massive nested dictionary, just grab the first few keys
        elif isinstance(data, dict):
            sampled_dict = {k: data[k] for k in list(data.keys())[:max_rows]}
            return json.dumps(sampled_dict, indent=2)
            
        return "Unknown JSON structure."
    
def generate_dataset_insight(file_path: str) -> str:
    """Sends the data sample to the LLM for analysis."""
    # Get the shape of data
    data_context = extract_data_sample(file_path)
    
    prompt = f"""You are an expert data scientist. I am providing you with a schema and first {len(data_context.splitlines()) - 1 } rows of a dataset. 
    Please provide a breif, 3 sentence summary of what this dataset appears to contain and suggest one interesting metric I could calculate from it.
    
    Dataset Sample:
    {data_context}
     """
    if not settings.AI_API_KEY:
        return f"Mock AI Insight: This dataset has the following shape: {data_context[:100]}... Set AI_API_KEY to see real insights."   
    
    messages=[
                {
                    "role": "system",
                    "content": "You are a precise, technical data analysis assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]   
    
    response = llm.get_response(messages=messages)
    return response.content