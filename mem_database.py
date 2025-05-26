import sqlite3
from datetime import datetime

# Connect to the MEM diagnostics database
conn = sqlite3.connect("mem_diagnostics.db")
cur = conn.cursor()

def insert_mem_document(source, content):
    """
    Insert a new document (e.g., a post, speech, article) into the mem_documents table.
    Returns the document_id.
    """
    cur.execute("""
    INSERT INTO mem_documents (source, content)
    VALUES (?, ?)
    """, (source, content))
    conn.commit()
    return cur.lastrowid

def insert_mem_diagnostic(document_id, diag_entry):
    """
    Insert one diagnostic entry (single answered question) into mem_diagnostics.
    Assumes diag_entry is a dict with keys:
    - pillar
    - subdomain
    - question
    - indicator (positive/negative/neutral)
    - response_type (yesno/scale)
    - response_value (yes/no/1-5 scale)
    - weight
    """
    
    cur.execute("""
    INSERT INTO mem_diagnostics (document_id, pillar, subdomain, question, indicator, response_type, response_value, weight)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        diag_entry.get("pillar"),
        diag_entry.get("subdomain"),
        diag_entry.get("question"),
        diag_entry.get("indicator"),
        diag_entry.get("response_type"),
        str(diag_entry.get("response_value")),  # Always store as string for consistency
        diag_entry.get("weight", 1.0)  # Default weight if missing
    ))
    conn.commit()

def insert_bulk_diagnostics(document_id, diagnostics):
    """
    Insert multiple diagnostics at once.
    diagnostics = list of diagnostic dicts.
    """
    for diag in diagnostics:
        insert_mem_diagnostic(document_id, diag)

# Optional: Pillar Score Saving
def insert_pillar_score(document_id, pillar_name, score_value):
    """
    Insert pillar-level aggregate score (optional future use).
    """
    cur.execute("""
    INSERT INTO mem_pillar_scores (document_id, pillar, score)
    VALUES (?, ?, ?)
    """, (document_id, pillar_name, score_value))
    conn.commit()

# Utility (Optional) - Check if document already exists based on source and content
def document_exists(source, content):
    cur.execute("""
    SELECT id FROM mem_documents WHERE source = ? AND content = ?
    """, (source, content))
    return cur.fetchone() is not None

# Close DB connection when done (important later)
def close_connection():
    conn.close()
