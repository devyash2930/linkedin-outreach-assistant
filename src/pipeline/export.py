"""
Export Module

Exports data to CSV formats compatible with:
- Google Sheets
- Notion
- Airtable
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.config import get_data_dir, load_config
from db.repo import DatabaseRepo


def export_data(
    export_type: str = "companies",
    format: str = "csv",
    output_path: str = None
) -> Dict[str, Any]:
    """
    Export data to file.
    
    Args:
        export_type: Type of data to export (companies, contacts, sequences, summary)
        format: Output format (csv, notion, sheets)
        output_path: Optional custom output path
    
    Returns:
        Export result with path and count
    """
    db = DatabaseRepo()
    
    exporters = {
        "companies": export_companies,
        "contacts": export_contacts,
        "sequences": export_sequences,
        "summary": export_summary
    }
    
    if export_type not in exporters:
        raise ValueError(f"Unknown export type: {export_type}")
    
    return exporters[export_type](db, format, output_path)


def export_companies(
    db: DatabaseRepo, 
    format: str = "csv",
    output_path: str = None
) -> Dict[str, Any]:
    """Export companies data."""
    companies = db.get_all_companies(ranked=True)
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = get_data_dir("out/exports")
        output_path = output_dir / f"companies_export_{timestamp}.csv"
    else:
        output_path = Path(output_path)
    
    # Prepare columns based on format
    if format == "notion":
        columns = [
            "Name", "Domain", "Location", "Size", "Industry",
            "Score", "Hiring", "Activity", "Sources"
        ]
        rows = _format_companies_notion(companies)
    elif format == "sheets":
        columns = [
            "Company Name", "Website", "City", "State", "Size Band",
            "Industry", "Relevance Score", "Hiring Signal", "Recent Activity",
            "Keywords", "Sources", "Confidence"
        ]
        rows = _format_companies_sheets(companies)
    else:  # csv
        columns = [
            "company_id", "company_name", "domain", "hq_city", "hq_state",
            "size_band", "industry", "relevance_score", "hiring_signal",
            "recent_activity", "keywords", "sources", "confidence"
        ]
        rows = companies
    
    _write_csv(output_path, columns, rows, format)
    
    return {
        "path": str(output_path),
        "count": len(companies),
        "type": "companies",
        "format": format
    }


def export_contacts(
    db: DatabaseRepo,
    format: str = "csv",
    output_path: str = None
) -> Dict[str, Any]:
    """Export contacts data with company info and status."""
    contacts = db.get_all_contacts()
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = get_data_dir("out/exports")
        output_path = output_dir / f"contacts_export_{timestamp}.csv"
    else:
        output_path = Path(output_path)
    
    # Enrich contacts with company data
    enriched = []
    for contact in contacts:
        company = db.get_company(contact["company_id"])
        touchpoints = db.get_contact_touchpoints(contact["contact_id"])
        
        enriched.append({
            **contact,
            "company_name": company["company_name"] if company else "",
            "company_domain": company["domain"] if company else "",
            "touchpoint_count": len(touchpoints),
            "last_touchpoint": touchpoints[-1]["event_type"] if touchpoints else ""
        })
    
    if format == "notion":
        columns = [
            "Name", "Title", "Company", "Status", "Last Action", "Notes"
        ]
        rows = _format_contacts_notion(enriched)
    else:
        columns = [
            "contact_id", "first_name", "last_name", "title", "company_name",
            "company_domain", "linkedin_url", "email", "status",
            "touchpoint_count", "last_touchpoint", "notes", "created_at"
        ]
        rows = enriched
    
    _write_csv(output_path, columns, rows, format)
    
    return {
        "path": str(output_path),
        "count": len(contacts),
        "type": "contacts",
        "format": format
    }


def export_sequences(
    db: DatabaseRepo,
    format: str = "csv",
    output_path: str = None
) -> Dict[str, Any]:
    """Export outreach sequences and touchpoints."""
    # Get all touchpoints grouped by contact
    contacts = db.get_all_contacts()
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = get_data_dir("out/exports")
        output_path = output_dir / f"sequences_export_{timestamp}.csv"
    else:
        output_path = Path(output_path)
    
    rows = []
    for contact in contacts:
        company = db.get_company(contact["company_id"])
        touchpoints = db.get_contact_touchpoints(contact["contact_id"])
        
        for tp in touchpoints:
            rows.append({
                "contact_id": contact["contact_id"],
                "contact_name": f"{contact['first_name']} {contact['last_name']}",
                "company_name": company["company_name"] if company else "",
                "sequence_id": tp.get("sequence_id"),
                "step_number": tp.get("step_number"),
                "event_type": tp["event_type"],
                "event_date": tp["event_date"],
                "outcome": tp.get("outcome", ""),
                "notes": tp.get("notes", "")
            })
    
    columns = [
        "contact_id", "contact_name", "company_name", "sequence_id",
        "step_number", "event_type", "event_date", "outcome", "notes"
    ]
    
    _write_csv(output_path, columns, rows, format)
    
    return {
        "path": str(output_path),
        "count": len(rows),
        "type": "sequences",
        "format": format
    }


def export_summary(
    db: DatabaseRepo,
    format: str = "csv",
    output_path: str = None
) -> Dict[str, Any]:
    """Export summary statistics and conversion metrics."""
    stats = db.get_stats()
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = get_data_dir("out/exports")
        output_path = output_dir / f"summary_export_{timestamp}.csv"
    else:
        output_path = Path(output_path)
    
    # Calculate additional metrics
    reply_rate = (stats["replied"] / stats["sent"] * 100) if stats["sent"] > 0 else 0
    
    rows = [
        {"metric": "Total Companies", "value": stats["companies"]},
        {"metric": "Total Contacts", "value": stats["contacts"]},
        {"metric": "Messages Sent", "value": stats["sent"]},
        {"metric": "Replies Received", "value": stats["replied"]},
        {"metric": "Reply Rate", "value": f"{reply_rate:.1f}%"},
        {"metric": "Pending Follow-ups", "value": stats["pending_followups"]},
        {"metric": "Export Date", "value": datetime.now().strftime("%Y-%m-%d %H:%M")},
    ]
    
    columns = ["metric", "value"]
    
    _write_csv(output_path, columns, rows, format)
    
    return {
        "path": str(output_path),
        "count": len(rows),
        "type": "summary",
        "format": format
    }


def _write_csv(path: Path, columns: List[str], rows: List[Dict], format: str):
    """Write data to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _format_companies_notion(companies: List[Dict]) -> List[Dict]:
    """Format companies for Notion import."""
    return [
        {
            "Name": c.get("company_name", ""),
            "Domain": c.get("domain", ""),
            "Location": f"{c.get('hq_city', '')}, {c.get('hq_state', '')}",
            "Size": c.get("size_band", ""),
            "Industry": c.get("industry", ""),
            "Score": f"{c.get('relevance_score', 0):.2f}",
            "Hiring": c.get("hiring_signal", "unknown"),
            "Activity": c.get("recent_activity", ""),
            "Sources": c.get("sources", "")
        }
        for c in companies
    ]


def _format_companies_sheets(companies: List[Dict]) -> List[Dict]:
    """Format companies for Google Sheets."""
    return [
        {
            "Company Name": c.get("company_name", ""),
            "Website": c.get("domain", ""),
            "City": c.get("hq_city", ""),
            "State": c.get("hq_state", ""),
            "Size Band": c.get("size_band", ""),
            "Industry": c.get("industry", ""),
            "Relevance Score": c.get("relevance_score", 0),
            "Hiring Signal": c.get("hiring_signal", "unknown"),
            "Recent Activity": c.get("recent_activity", ""),
            "Keywords": c.get("keywords", ""),
            "Sources": c.get("sources", ""),
            "Confidence": c.get("confidence", 0.5)
        }
        for c in companies
    ]


def _format_contacts_notion(contacts: List[Dict]) -> List[Dict]:
    """Format contacts for Notion import."""
    return [
        {
            "Name": f"{c.get('first_name', '')} {c.get('last_name', '')}",
            "Title": c.get("title", ""),
            "Company": c.get("company_name", ""),
            "Status": c.get("status", "new"),
            "Last Action": c.get("last_touchpoint", ""),
            "Notes": c.get("notes", "")
        }
        for c in contacts
    ]
