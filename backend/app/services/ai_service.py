import csv
import json
import os
# import google.generativeai as genai  <-- If using Gemini
# from openai import OpenAI
from prompt_toolkit import prompt
from app.core.config import settings
from app.services.llm_service import llm
import structlog

log = structlog.get_logger()

def extract_data_sample(file_path: str, max_rows: int = 5) -> str:
    """Extracts headers and a few rows to give the LLM context."""
    log.info("extracting_data_sample", file_path=file_path, max_rows=max_rows)
    try:
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() == "csv":
            result = _extract_csv_sample(file_path, max_rows)
        elif ext.lower() == "json":
            result = _extract_json_sample(file_path, max_rows)
        else:
            log.warning("unsupported_file_format", file_path=file_path, extension=ext)
            return "Unsupported file format."
        
        log.debug("data_sample_extracted_successfully", file_path=file_path)
        return result
    except Exception as e:
        log.error("extract_data_sample_failed", file_path=file_path, error=str(e))
        return f"Error reading file: {str(e)}"
    
def _extract_csv_sample(file_path:str, max_rows: int)-> str:
    log.debug("extracting_csv_sample", file_path=file_path, max_rows=max_rows)
    try:
        sample_data = []
        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            headers = next(reader)
            if not headers:
                log.warning("no_headers_found_in_csv", file_path=file_path)
                return "No headers found in the CSV file."
            
            sample_data.append(headers)

            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                sample_data.append(row)

            log.debug("csv_sample_extraction_completed", file_path=file_path, rows_extracted=len(sample_data)-1)
            return json.dumps(sample_data, indent=2)
    except Exception as e:
        log.error("_extract_csv_sample_failed", file_path=file_path, error=str(e))
        raise

def _extract_json_sample(file_path: str, max_rows: int) -> str:
    """Helper to safely read JSON files (handles arrays and objects)."""
    log.debug("extracting_json_sample", file_path=file_path, max_rows=max_rows)
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            
            # If it's a list of objects (standard data export)
            if isinstance(data, list):
                result = json.dumps(data[:max_rows], indent=2)
                log.debug("json_sample_extraction_completed", file_path=file_path, type="array", items=len(data[:max_rows]))
                return result
                
            # If it's a massive nested dictionary, just grab the first few keys
            elif isinstance(data, dict):
                sampled_dict = {k: data[k] for k in list(data.keys())[:max_rows]}
                log.debug("json_sample_extraction_completed", file_path=file_path, type="object", keys=len(sampled_dict))
                return json.dumps(sampled_dict, indent=2)
                
            log.warning("unknown_json_structure", file_path=file_path)
            return "Unknown JSON structure."
    except Exception as e:
        log.error("_extract_json_sample_failed", file_path=file_path, error=str(e))
        raise
    
def generate_dataset_insight(file_path: str) -> str:
    """Sends the data sample to the LLM for analysis."""
    log.info("generating_dataset_insight", file_path=file_path)
    try:
        # Get the shape of data
        data_context = extract_data_sample(file_path)
        
        prompt = f"""You are an expert data scientist. I am providing you with a schema and first {len(data_context.splitlines()) - 1 } rows of a dataset. 
        Please provide a breif, 3 sentence summary of what this dataset appears to contain and suggest one interesting metric I could calculate from it.
        
        Dataset Sample:
        {data_context}
         """
        if not settings.AI_API_KEY:
            log.warning("ai_api_key_not_configured")
            return f"Mock AI Insight: This dataset has the following shape: {data_context[:100]}... Set AI_API_KEY to see real insights."   
        
        log.debug("calling_llm_for_insight", file_path=file_path)
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
        log.info("dataset_insight_generated_successfully", file_path=file_path)
        return response.content
    except Exception as e:
        log.error("generate_dataset_insight_failed", file_path=file_path, error=str(e))
        raise