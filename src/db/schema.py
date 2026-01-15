"""
SQLite Database Schema for Outreach Tracking.

Tables:
- companies: Discovered and normalized company data
- contacts: Manually added contacts from LinkedIn
- title_priorities: Job titles and priority order
- touchpoints: Outreach events (sent, seen, replied, etc.)
- sequences: Multi-step outreach sequences
- do_not_contact: Suppression list
"""

import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA_SQL = """
-- Companies table: stores normalized company data
CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    domain TEXT UNIQUE,
    hq_city TEXT,
    hq_state TEXT,
    size_band TEXT,
    industry TEXT,
    keywords TEXT,  -- comma-separated
    sources TEXT,   -- comma-separated (multi-source attribution)
    confidence REAL DEFAULT 0.5,
    hiring_signal TEXT DEFAULT 'unknown',  -- yes/no/unknown
    recent_activity TEXT,
    tech_stack_hint TEXT,
    relevance_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table: manually added after LinkedIn selection
CREATE TABLE IF NOT EXISTS contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    linkedin_url TEXT,
    email TEXT,
    notes TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'new',  -- new/contacted/replied/converted/dnc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Title priorities: guides contact selection on LinkedIn
CREATE TABLE IF NOT EXISTS title_priorities (
    priority_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_pattern TEXT NOT NULL,
    priority_rank INTEGER NOT NULL,
    notes TEXT
);

-- Sequences: multi-step outreach campaigns
CREATE TABLE IF NOT EXISTS sequences (
    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sequence steps: individual steps in a sequence
CREATE TABLE IF NOT EXISTS sequence_steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,  -- invite/follow-up/breakup
    days_after_previous INTEGER DEFAULT 0,
    template_name TEXT,
    notes TEXT,
    FOREIGN KEY (sequence_id) REFERENCES sequences(sequence_id)
);

-- Touchpoints: outreach events tracking
CREATE TABLE IF NOT EXISTS touchpoints (
    touchpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    sequence_id INTEGER,
    step_number INTEGER,
    event_type TEXT NOT NULL,  -- sent/seen/replied/follow_up
    event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    planned_date DATE,
    outcome TEXT,
    notes TEXT,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (sequence_id) REFERENCES sequences(sequence_id)
);

-- Do Not Contact: suppression list
CREATE TABLE IF NOT EXISTS do_not_contact (
    dnc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    company_id INTEGER,
    domain TEXT,
    email TEXT,
    reason TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Message drafts: stored drafts for review
CREATE TABLE IF NOT EXISTS message_drafts (
    draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    contact_id INTEGER,
    angle TEXT,  -- peer/curiosity/usecase/local
    invite_note TEXT,
    inmail_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_hq_city ON companies(hq_city);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_touchpoints_contact ON touchpoints(contact_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_event_type ON touchpoints(event_type);

-- Insert default title priorities
INSERT OR IGNORE INTO title_priorities (title_pattern, priority_rank, notes) VALUES
    ('CEO', 1, 'Chief Executive Officer'),
    ('CTO', 2, 'Chief Technology Officer'),
    ('Founder', 3, 'Founder/Co-Founder'),
    ('Co-Founder', 3, 'Co-Founder'),
    ('VP of Engineering', 4, 'VP Engineering'),
    ('VP Engineering', 4, 'VP Engineering'),
    ('Head of Engineering', 5, 'Engineering Head'),
    ('Director of Engineering', 6, 'Engineering Director'),
    ('Engineering Manager', 7, 'Eng Manager');

-- Insert default sequence
INSERT OR IGNORE INTO sequences (sequence_id, sequence_name, description) VALUES
    (1, 'Standard Cold Outreach', 'Default 3-step sequence: invite, follow-up, breakup');

INSERT OR IGNORE INTO sequence_steps (sequence_id, step_number, step_type, days_after_previous, template_name) VALUES
    (1, 1, 'invite', 0, 'initial_invite'),
    (1, 2, 'follow_up', 7, 'first_followup'),
    (1, 3, 'breakup', 14, 'breakup_message');
"""


def init_database(db_path: Path) -> sqlite3.Connection:
    """
    Initialize the database with schema.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        Database connection
    """
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Execute schema
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    
    return conn


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a database connection."""
    if db_path is None:
        from utils.config import get_db_path
        db_path = get_db_path()
    
    if not db_path.exists():
        return init_database(db_path)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
