"""
Pipeline module - orchestrates normalization and deduplication.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from utils.config import get_data_dir
from .normalize import normalize_companies
from .dedupe import dedupe_companies, calculate_dedup_stats


def process_companies(companies: List[Dict]) -> Dict[str, Any]:
    """
    Full processing pipeline: normalize -> dedupe -> save.
    
    Args:
        companies: Raw company data from discovery
    
    Returns:
        Processing results and statistics
    """
    print("   Normalizing company data...")
    normalized = normalize_companies(companies)
    
    print("   Deduplicating records...")
    deduped = dedupe_companies(normalized)
    
    stats = calculate_dedup_stats(normalized, deduped)
    print(f"   Removed {stats['duplicates_removed']} duplicates ({stats['reduction_pct']}%)")
    
    # Save to companies.csv
    output_path = save_companies_csv(deduped)
    
    # Also save to database
    save_companies_to_db(deduped)
    
    return {
        "companies": deduped,
        "stats": stats,
        "output_path": str(output_path)
    }


def save_companies_csv(companies: List[Dict], filename: str = "companies.csv") -> Path:
    """
    Save companies to CSV file.
    
    Args:
        companies: List of company dictionaries
        filename: Output filename
    
    Returns:
        Path to saved file
    """
    output_dir = get_data_dir("out")
    output_path = output_dir / filename
    
    if not companies:
        return output_path
    
    # Define column order
    columns = [
        "company_id", "company_name", "domain", "hq_city", "hq_state",
        "size_band", "industry", "keywords", "sources", "confidence",
        "hiring_signal", "recent_activity", "tech_stack_hint"
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for idx, company in enumerate(companies, 1):
            company["company_id"] = idx
            writer.writerow(company)
    
    return output_path


def save_companies_to_db(companies: List[Dict]):
    """Save companies to SQLite database."""
    from db.repo import DatabaseRepo
    
    db = DatabaseRepo()
    
    for company in companies:
        try:
            db.upsert_company(company)
        except Exception as e:
            print(f"   Warning: Could not save {company.get('company_name')}: {e}")


def load_discovery_results() -> List[Dict]:
    """Load most recent discovery results."""
    raw_dir = get_data_dir("raw/discovery")
    
    # Find most recent discovery file
    files = sorted(raw_dir.glob("discovery_*.json"), reverse=True)
    
    if not files:
        return []
    
    with open(files[0]) as f:
        data = json.load(f)
    
    return data.get("companies", [])
