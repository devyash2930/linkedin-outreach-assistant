"""
Database Repository - Data access layer for outreach tracking.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .schema import get_connection, init_database


class DatabaseRepo:
    """Repository for database operations."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize repository with database connection."""
        if db_path is None:
            from utils.config import get_db_path
            db_path = get_db_path()
        
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists and is initialized."""
        if not self.db_path.exists():
            init_database(self.db_path)
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        return get_connection(self.db_path)
    
    # ─────────────────────────────────────────────────────────────
    # Company Operations
    # ─────────────────────────────────────────────────────────────
    
    def add_company(self, company_data: Dict[str, Any]) -> int:
        """Add a new company to the database."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO companies (
                company_name, domain, hq_city, hq_state, size_band,
                industry, keywords, sources, confidence, hiring_signal,
                recent_activity, tech_stack_hint, relevance_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_data.get('company_name'),
            company_data.get('domain'),
            company_data.get('hq_city'),
            company_data.get('hq_state'),
            company_data.get('size_band'),
            company_data.get('industry'),
            company_data.get('keywords'),
            company_data.get('sources'),
            company_data.get('confidence', 0.5),
            company_data.get('hiring_signal', 'unknown'),
            company_data.get('recent_activity'),
            company_data.get('tech_stack_hint'),
            company_data.get('relevance_score', 0.0)
        ))
        
        conn.commit()
        company_id = cursor.lastrowid
        conn.close()
        return company_id
    
    def get_company(self, company_id: int) -> Optional[Dict]:
        """Get company by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE company_id = ?", (company_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_company_by_domain(self, domain: str) -> Optional[Dict]:
        """Get company by domain."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_companies(self, ranked: bool = False, limit: int = None) -> List[Dict]:
        """Get all companies, optionally ranked."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM companies"
        if ranked:
            query += " ORDER BY relevance_score DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_company_score(self, company_id: int, score: float):
        """Update company relevance score."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE companies SET relevance_score = ?, updated_at = ? WHERE company_id = ?",
            (score, datetime.now(), company_id)
        )
        conn.commit()
        conn.close()
    
    def upsert_company(self, company_data: Dict[str, Any]) -> int:
        """Insert or update company by domain."""
        existing = self.get_company_by_domain(company_data.get('domain'))
        if existing:
            # Update existing
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE companies SET
                    company_name = COALESCE(?, company_name),
                    hq_city = COALESCE(?, hq_city),
                    hq_state = COALESCE(?, hq_state),
                    size_band = COALESCE(?, size_band),
                    industry = COALESCE(?, industry),
                    keywords = COALESCE(?, keywords),
                    sources = ?,
                    confidence = ?,
                    updated_at = ?
                WHERE domain = ?
            """, (
                company_data.get('company_name'),
                company_data.get('hq_city'),
                company_data.get('hq_state'),
                company_data.get('size_band'),
                company_data.get('industry'),
                company_data.get('keywords'),
                company_data.get('sources'),
                company_data.get('confidence', existing['confidence']),
                datetime.now(),
                company_data.get('domain')
            ))
            conn.commit()
            conn.close()
            return existing['company_id']
        else:
            return self.add_company(company_data)
    
    # ─────────────────────────────────────────────────────────────
    # Contact Operations
    # ─────────────────────────────────────────────────────────────
    
    def add_contact(self, contact_data: Dict[str, Any]) -> int:
        """Add a new contact."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO contacts (
                company_id, first_name, last_name, title,
                linkedin_url, email, notes, priority, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contact_data.get('company_id'),
            contact_data.get('first_name'),
            contact_data.get('last_name'),
            contact_data.get('title'),
            contact_data.get('linkedin_url'),
            contact_data.get('email'),
            contact_data.get('notes'),
            contact_data.get('priority', 5),
            contact_data.get('status', 'new')
        ))
        
        conn.commit()
        contact_id = cursor.lastrowid
        conn.close()
        return contact_id
    
    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get contact by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE contact_id = ?", (contact_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_contact_status(self, contact_id: int, status: str):
        """Update contact status."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE contacts SET status = ?, updated_at = ? WHERE contact_id = ?",
            (status, datetime.now(), contact_id)
        )
        conn.commit()
        conn.close()
    
    def get_all_contacts(
        self, 
        company_id: int = None, 
        status: str = None
    ) -> List[Dict]:
        """Get all contacts with optional filters."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []
        
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_to_dnc(
        self, 
        contact_id: int = None, 
        company_id: int = None,
        domain: str = None,
        email: str = None,
        reason: str = ""
    ) -> int:
        """Add to do-not-contact list."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO do_not_contact (contact_id, company_id, domain, email, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (contact_id, company_id, domain, email, reason))
        
        # Update contact status if contact_id provided
        if contact_id:
            cursor.execute(
                "UPDATE contacts SET status = 'dnc' WHERE contact_id = ?",
                (contact_id,)
            )
        
        conn.commit()
        dnc_id = cursor.lastrowid
        conn.close()
        return dnc_id
    
    # ─────────────────────────────────────────────────────────────
    # Draft Operations
    # ─────────────────────────────────────────────────────────────
    
    def save_draft(
        self,
        company_id: int,
        contact_id: int = None,
        angle: str = None,
        invite_note: str = None,
        inmail_message: str = None
    ) -> int:
        """Save a message draft."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO message_drafts (
                company_id, contact_id, angle, invite_note, inmail_message
            ) VALUES (?, ?, ?, ?, ?)
        """, (company_id, contact_id, angle, invite_note, inmail_message))
        
        conn.commit()
        draft_id = cursor.lastrowid
        conn.close()
        return draft_id
    
    def get_drafts(
        self, 
        company_id: int = None, 
        contact_id: int = None
    ) -> List[Dict]:
        """Get message drafts."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM message_drafts WHERE 1=1"
        params = []
        
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)
        
        if contact_id:
            query += " AND contact_id = ?"
            params.append(contact_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def is_on_dnc_list(self, contact_id: int = None, domain: str = None) -> bool:
        """Check if contact/domain is on do-not-contact list."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if contact_id:
            cursor.execute("SELECT 1 FROM do_not_contact WHERE contact_id = ?", (contact_id,))
        elif domain:
            cursor.execute("SELECT 1 FROM do_not_contact WHERE domain = ?", (domain,))
        else:
            return False
        
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    # ─────────────────────────────────────────────────────────────
    # Touchpoint Operations
    # ─────────────────────────────────────────────────────────────
    
    def log_touchpoint(
        self, 
        contact_id: int, 
        event_type: str,
        sequence_id: int = None,
        step_number: int = None,
        outcome: str = None,
        notes: str = None
    ) -> int:
        """Log an outreach touchpoint."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO touchpoints (
                contact_id, sequence_id, step_number, event_type, outcome, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (contact_id, sequence_id, step_number, event_type, outcome, notes))
        
        conn.commit()
        touchpoint_id = cursor.lastrowid
        
        # Update contact status based on event
        status_map = {
            'sent': 'contacted',
            'replied': 'replied',
            'converted': 'converted'
        }
        if event_type in status_map:
            self.update_contact_status(contact_id, status_map[event_type])
        
        conn.close()
        return touchpoint_id
    
    def get_contact_touchpoints(self, contact_id: int) -> List[Dict]:
        """Get all touchpoints for a contact."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM touchpoints WHERE contact_id = ? ORDER BY event_date",
            (contact_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_pending_followups(self) -> List[Dict]:
        """Get contacts needing follow-up."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Find contacts with sent but no reply after 7 days
        cursor.execute("""
            SELECT c.*, t.event_date as last_sent
            FROM contacts c
            JOIN touchpoints t ON c.contact_id = t.contact_id
            WHERE t.event_type = 'sent'
            AND c.status = 'contacted'
            AND NOT EXISTS (
                SELECT 1 FROM touchpoints t2 
                WHERE t2.contact_id = c.contact_id 
                AND t2.event_type IN ('replied', 'follow_up')
                AND t2.event_date > t.event_date
            )
            AND date(t.event_date, '+7 days') <= date('now')
        """)
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ─────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, int]:
        """Get outreach statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        stats['companies'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts")
        stats['contacts'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM touchpoints WHERE event_type = 'sent'")
        stats['sent'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM touchpoints WHERE event_type = 'replied'")
        stats['replied'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT c.contact_id)
            FROM contacts c
            JOIN touchpoints t ON c.contact_id = t.contact_id
            WHERE t.event_type = 'sent'
            AND c.status = 'contacted'
            AND NOT EXISTS (
                SELECT 1 FROM touchpoints t2 
                WHERE t2.contact_id = c.contact_id 
                AND t2.event_type IN ('replied', 'follow_up')
            )
        """)
        stats['pending_followups'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
