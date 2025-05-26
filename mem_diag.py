#!/usr/bin/env python3

import time
import json
import sqlite3
from openai import OpenAI
from mem_database import insert_mem_document, insert_bulk_diagnostics 

# --- CONFIGURATION ---
# Set your project and assistant IDs
API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("OPENAI_PROJECT_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANS_ID")

# Initialize OpenAI Client
client = OpenAI(
	api_key=API_KEY,
	project=PROJECT_ID
)

# Database connection (reuse)
conn = sqlite3.connect("mem_diagnostics.db")
cur = conn.cursor()

# --- OPENAI ASSISTANT COMMUNICATION ---

def run_mem_diagnostic(content_text):
	"""
	Send content to MEM Assistant and retrieve structured diagnostic JSON.
	"""
	try:
		# Step 1: Create a thread
		thread = client.beta.threads.create()
		
		# Step 2: Add user prompt
		client.beta.threads.messages.create(
			thread_id=thread.id,
			role="user",
			content=content_text
		)
		
		# Step 3: Run the assistant
		run = client.beta.threads.runs.create(
			thread_id=thread.id,
			assistant_id=ASSISTANT_ID
		)
		
		# Step 4: Poll until completion
		while True:
			run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
			if run_status.status == "completed":
				break
			elif run_status.status in ["failed", "cancelled"]:
				raise Exception(f"Run failed: {run_status.status}")
			time.sleep(1)  # polite polling
			
		# Step 5: Retrieve output
		messages = client.beta.threads.messages.list(thread_id=thread.id)
		message = messages.data[0]
		content = message.content[0]
		
		if hasattr(content, "tool_calls"):
			# Structured schema call
			tool_call_result = content.tool_calls[0].function.arguments
			mem_diagnostic_data = json.loads(tool_call_result)
		else:
			# Plain JSON text fallback
			response_text = content.text.value
			mem_diagnostic_data = json.loads(response_text)
			
		return mem_diagnostic_data
	
	except Exception as e:
		print(f"Error running diagnostic: {e}")
		return None
	
	
# --- DATABASE SAVING ---
	
def save_mem_diagnostic(source, content_text, diagnostic_data):
	"""
	Save received diagnostic results into mem_documents and mem_diagnostics tables.
	"""
	
	# Insert document
	doc_id = insert_mem_document(source, content_text)
	
	# Extract diagnostics
	mem_core_items = diagnostic_data.get("mem_core", [])
	print(mem_core_items)
	
	diagnostics = []
	for item in mem_core_items:
		diag = {
			"pillar": item.get("pillar"),
			"subdomain": item.get("subdomain"),
			"question": item.get("question"),
			"indicator": "positive",  # <-- Still placeholder; real logic later if needed
			"response_type": item.get("type"),
			"response_value": str(item.get("response_value")),  # <-- Capture the actual 0–5 answer as a string
			"weight": 1.0  # Default for now; could refine later
		}
		diagnostics.append(diag)
		print(diag)
		
	# Save all diagnostics
	insert_bulk_diagnostics(doc_id, diagnostics)
	
	print(f"Saved diagnostics for document ID {doc_id}.")

	
# --- Main Example Usage ---
	
if __name__ == "__main__":
	SAMPLE_CONTENT = """
	Freedom is the ability to act without being bound by the illusions of consensus reality. True knowledge is felt, not certified.
	"""
	# Run Diagnostic
	diag_data = run_mem_diagnostic(SAMPLE_CONTENT)
	
	if diag_data:
		# Save Diagnostic
		save_mem_diagnostic("TestSource", SAMPLE_CONTENT, diag_data)
		
conn.close()
