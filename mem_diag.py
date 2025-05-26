import os, time
import json
import sqlite3
from openai import OpenAI
from mem_database import insert_mem_document, insert_bulk_diagnostics

# --- CONFIGURATION ---

# Set your project and assistant IDs
API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("OPENAI_PROJECT_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID") 

DB_PATH = "mem_diagnostics.db"

# Initialize OpenAI Client
client = OpenAI(
    api_key=API_KEY,
    project=PROJECT_ID
)

# --- VALIDATOR HELPER ---
def validate_mem_diagnostic_structure(diagnostic_data):
    if not isinstance(diagnostic_data, dict):
        print("Validation Error: Top-level structure is not a dictionary.")
        print(json.dumps(diagnostic_data, indent=2, ensure_ascii=False))
        return False
    if "mem_core" not in diagnostic_data:
        print("Validation Error: 'mem_core' key missing in diagnostic data.")
        print(json.dumps(diagnostic_data, indent=2, ensure_ascii=False))
        return False
    if not isinstance(diagnostic_data["mem_core"], list):
        print("Validation Error: 'mem_core' value is not a list.")
        print(json.dumps(diagnostic_data, indent=2, ensure_ascii=False))
        return False
    return True

# --- SAVE TO DATABASE ---
def save_mem_diagnostic(source, content_text, diagnostic_data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    doc_id = insert_mem_document(source, content_text)

    mem_core_items = diagnostic_data["mem_core"]
    print(json.dumps(diagnostic_data, indent=2, ensure_ascii=False))
    

    diagnostics = []
    for item in mem_core_items:
        diag = {
            "pillar": item.get("pillar"),
            "subdomain": item.get("subdomain"),
            "question": item.get("question"),
            "indicator": "positive",  # Placeholder for now
            "response_type": item.get("type"),
            "response_value": str(item.get("response_value")),
            "weight": 1.0
        }
        diagnostics.append(diag)

    insert_bulk_diagnostics(doc_id, diagnostics)

    conn.commit()
    conn.close()
    print(f"Saved diagnostics for document ID {doc_id}.")

# --- ASSISTANT CALLER ---
def run_mem_diagnostic(content_text):
    """
    Send content to MEM Assistant and retrieve structured diagnostic JSON.
    """
    try:
        # Create a thread
        thread = client.beta.threads.create()
        
        # Add user prompt
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content_text
        )
        
        # Run Assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        
        # Poll until completion
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                raise Exception(f"Run failed: {run_status.status}")
            time.sleep(1)
        
        # Retrieve output
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        message = messages.data[0]
        content = message.content[0]
        
        if hasattr(content, "tool_calls"):
            tool_call_result = content.tool_calls[0].function.arguments
            mem_diagnostic_data = json.loads(tool_call_result)
        else:
            response_text = content.text.value
            mem_diagnostic_data = json.loads(response_text)
        
        return mem_diagnostic_data

    except Exception as e:
        print(f"Error running diagnostic: {e}")
        return None

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    SAMPLE_CONTENT = """
    True understanding arises from inner resonance rather than external validation. What we know must be felt, not proven.
    """
    
    diag_data = run_mem_diagnostic(SAMPLE_CONTENT)
    
    if diag_data:
        if validate_mem_diagnostic_structure(diag_data):
            save_mem_diagnostic("TestSource", SAMPLE_CONTENT, diag_data)
        else:
            print("Output structure invalid, not saving.")
    else:
        print("No diagnostic data received.")

        
