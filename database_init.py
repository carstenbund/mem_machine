#!/usr/bin/env python3

import sqlite3

# Connect to (or create) the MEM diagnostics database
conn = sqlite3.connect("mem_diagnostics.db")
cur = conn.cursor()

# Create table for storing evaluated statements/posts
cur.execute("""
CREATE TABLE IF NOT EXISTS mem_documents (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	source TEXT,
	content TEXT,
	analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create table for storing pillar-level scores
cur.execute("""
CREATE TABLE IF NOT EXISTS mem_pillar_scores (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	document_id INTEGER,
	pillar TEXT,
	score REAL,
	FOREIGN KEY(document_id) REFERENCES mem_documents(id)
)
""")

# Create table for storing question-level diagnostics
cur.execute("""
CREATE TABLE IF NOT EXISTS mem_diagnostics (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	document_id INTEGER,
	pillar TEXT,
	subdomain TEXT,
	question TEXT,
	indicator TEXT,
	response_type TEXT,
	response_value TEXT,
	weight REAL,
	FOREIGN KEY(document_id) REFERENCES mem_documents(id)
)
""")

# Create table for storing application-level modules (e.g. commercial influence)
cur.execute("""
CREATE TABLE IF NOT EXISTS mem_applications (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	document_id INTEGER,
	application_name TEXT,
	score REAL,
	classification TEXT,
	flags TEXT,
	FOREIGN KEY(document_id) REFERENCES mem_documents(id)
)
""")

# Create table for storing application question details
cur.execute("""
CREATE TABLE IF NOT EXISTS mem_application_diagnostics (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	application_id INTEGER,
	question TEXT,
	indicator TEXT,
	response_type TEXT,
	response_value TEXT,
	weight REAL,
	linked_pillars TEXT,
	variant_of TEXT,
	FOREIGN KEY(application_id) REFERENCES mem_applications(id)
)
""")

conn.commit()
conn.close()
