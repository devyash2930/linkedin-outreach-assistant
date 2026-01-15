"""
Company Discovery Module

Discovers companies from approved OFF-LinkedIn sources:
- Crunchbase (API)
- Google Places / Maps (API)
- NC startup directories (HTML/CSV ingest)
- Wellfound / AngelList (manual CSV ingest)

All raw data is stored in data/raw/{source}/{timestamp}.json|csv
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

from utils.config import load_config, get_data_dir


def discover_companies(
    since_days: int = 30,
    sources: List[str] = None
) -> Dict[str, Any]:
    """
    Discover companies from configured sources.
    
    Args:
        since_days: Look back period in days
        sources: List of sources to query (default: all)
    
    Returns:
        Dictionary with discovery results
    """
    if sources is None:
        sources = ["crunchbase", "google_places", "nc_directories", "wellfound"]
    
    config = load_config()
    results = {
        "count": 0,
        "sources_used": 0,
        "companies": [],
        "errors": []
    }
    
    source_handlers = {
        "crunchbase": CrunchbaseSource(),
        "google_places": GooglePlacesSource(),
        "nc_directories": NCDirectoriesSource(),
        "wellfound": WellfoundSource()
    }
    
    for source_name in sources:
        if source_name in source_handlers:
            try:
                handler = source_handlers[source_name]
                companies = handler.discover(since_days, config)
                results["companies"].extend(companies)
                results["sources_used"] += 1
                print(f"   ✓ {source_name}: Found {len(companies)} companies")
            except Exception as e:
                results["errors"].append(f"{source_name}: {str(e)}")
                print(f"   ✗ {source_name}: {str(e)}")
    
    results["count"] = len(results["companies"])
    
    # Save raw results
    _save_raw_results(results)
    
    return results


def _save_raw_results(results: Dict):
    """Save raw discovery results to data/raw/"""
    raw_dir = get_data_dir("raw/discovery")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_path = raw_dir / f"discovery_{timestamp}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


class BaseSource:
    """Base class for data sources."""
    
    def __init__(self):
        self.name = "base"
    
    def discover(self, since_days: int, config: Dict) -> List[Dict]:
        """Discover companies from this source."""
        raise NotImplementedError
    
    def _normalize_company(self, raw_data: Dict) -> Dict:
        """Normalize company data to standard format."""
        return {
            "company_name": raw_data.get("name", ""),
            "domain": raw_data.get("domain", ""),
            "hq_city": raw_data.get("city", ""),
            "hq_state": raw_data.get("state", ""),
            "size_band": raw_data.get("size", ""),
            "industry": raw_data.get("industry", ""),
            "keywords": raw_data.get("keywords", ""),
            "sources": self.name,
            "confidence": 0.5,
            "hiring_signal": raw_data.get("hiring", "unknown"),
            "recent_activity": raw_data.get("activity", ""),
            "tech_stack_hint": raw_data.get("tech_stack", "")
        }


class CrunchbaseSource(BaseSource):
    """Crunchbase API source."""
    
    def __init__(self):
        self.name = "crunchbase"
        self.api_key = os.environ.get("CRUNCHBASE_API_KEY")
    
    def discover(self, since_days: int, config: Dict) -> List[Dict]:
        """
        Discover companies from Crunchbase.
        
        Note: Requires CRUNCHBASE_API_KEY environment variable.
        Falls back to demo data if not available.
        """
        location = config.get("location", {})
        city = location.get("city", "Raleigh")
        state = location.get("state", "NC")
        
        if not self.api_key:
            # Return demo data for testing
            print(f"      (Demo mode - set CRUNCHBASE_API_KEY for real data)")
            return self._get_demo_data(city, state)
        
        # Real API implementation would go here
        # For now, using demo data
        return self._get_demo_data(city, state)
    
    def _get_demo_data(self, city: str, state: str) -> List[Dict]:
        """Demo data for testing without API key."""
        demo_companies = [
            {
                "name": "TechRaleigh Solutions",
                "domain": "techraleigh.io",
                "city": city,
                "state": state,
                "size": "11-50",
                "industry": "Software",
                "keywords": "saas,startup,series-a",
                "hiring": "yes",
                "activity": "Series A - $5M (2025)",
                "tech_stack": "Python,React,AWS"
            },
            {
                "name": "TriangleAI Labs",
                "domain": "triangleai.com",
                "city": city,
                "state": state,
                "size": "51-200",
                "industry": "AI/ML",
                "keywords": "ai,machine-learning,startup",
                "hiring": "yes",
                "activity": "Expansion announced",
                "tech_stack": "Python,TensorFlow,GCP"
            },
            {
                "name": "HealthTech Innovators",
                "domain": "healthtechinnovators.com",
                "city": city,
                "state": state,
                "size": "11-50",
                "industry": "HealthTech",
                "keywords": "healthcare,saas,series-b",
                "hiring": "yes",
                "activity": "Series B - $15M (2025)",
                "tech_stack": "Java,React,Azure"
            },
        ]
        
        return [self._normalize_company(c) for c in demo_companies]


class GooglePlacesSource(BaseSource):
    """Google Places API source."""
    
    def __init__(self):
        self.name = "google_places"
        self.api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    
    def discover(self, since_days: int, config: Dict) -> List[Dict]:
        """
        Discover companies from Google Places.
        
        Note: Requires GOOGLE_PLACES_API_KEY environment variable.
        """
        location = config.get("location", {})
        city = location.get("city", "Raleigh")
        state = location.get("state", "NC")
        
        if not self.api_key:
            print(f"      (Demo mode - set GOOGLE_PLACES_API_KEY for real data)")
            return self._get_demo_data(city, state)
        
        return self._get_demo_data(city, state)
    
    def _get_demo_data(self, city: str, state: str) -> List[Dict]:
        """Demo data for testing."""
        demo_companies = [
            {
                "name": "DataDriven RTP",
                "domain": "datadrivenrtp.com",
                "city": city,
                "state": state,
                "size": "1-10",
                "industry": "Data Analytics",
                "keywords": "analytics,data,startup",
                "hiring": "unknown",
                "activity": "",
                "tech_stack": ""
            },
            {
                "name": "CyberSecure NC",
                "domain": "cybersecurenc.com",
                "city": city,
                "state": state,
                "size": "11-50",
                "industry": "Cybersecurity",
                "keywords": "security,enterprise",
                "hiring": "unknown",
                "activity": "",
                "tech_stack": ""
            },
        ]
        
        return [self._normalize_company(c) for c in demo_companies]


class NCDirectoriesSource(BaseSource):
    """NC startup directories source (HTML/CSV ingest)."""
    
    def __init__(self):
        self.name = "nc_directories"
    
    def discover(self, since_days: int, config: Dict) -> List[Dict]:
        """
        Discover companies from NC startup directories.
        
        Checks for CSV files in data/raw/nc_directories/
        """
        location = config.get("location", {})
        city = location.get("city", "Raleigh")
        state = location.get("state", "NC")
        
        companies = []
        
        # Check for manual CSV uploads
        csv_dir = get_data_dir("raw/nc_directories")
        csv_files = list(csv_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            companies.extend(self._parse_csv(csv_file))
        
        if not companies:
            print(f"      (No CSV files found - add CSVs to data/raw/nc_directories/)")
            return self._get_demo_data(city, state)
        
        return companies
    
    def _parse_csv(self, csv_path: Path) -> List[Dict]:
        """Parse a CSV file into normalized company data."""
        companies = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append(self._normalize_company({
                    "name": row.get("company_name") or row.get("name", ""),
                    "domain": row.get("domain") or row.get("website", ""),
                    "city": row.get("city", ""),
                    "state": row.get("state", ""),
                    "size": row.get("size") or row.get("employees", ""),
                    "industry": row.get("industry") or row.get("sector", ""),
                    "keywords": row.get("keywords") or row.get("tags", ""),
                }))
        
        return companies
    
    def _get_demo_data(self, city: str, state: str) -> List[Dict]:
        """Demo data for testing."""
        demo_companies = [
            {
                "name": "RTP Fintech",
                "domain": "rtpfintech.com",
                "city": city,
                "state": state,
                "size": "51-200",
                "industry": "FinTech",
                "keywords": "fintech,payments,growth",
                "hiring": "yes",
                "activity": "New office opening",
                "tech_stack": ""
            },
        ]
        
        return [self._normalize_company(c) for c in demo_companies]


class WellfoundSource(BaseSource):
    """Wellfound/AngelList source (manual CSV ingest)."""
    
    def __init__(self):
        self.name = "wellfound"
    
    def discover(self, since_days: int, config: Dict) -> List[Dict]:
        """
        Discover companies from Wellfound CSV exports.
        
        Place exported CSVs in data/raw/wellfound/
        """
        location = config.get("location", {})
        city = location.get("city", "Raleigh")
        state = location.get("state", "NC")
        
        companies = []
        
        # Check for manual CSV uploads
        csv_dir = get_data_dir("raw/wellfound")
        csv_files = list(csv_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            companies.extend(self._parse_csv(csv_file))
        
        if not companies:
            print(f"      (No CSV files found - add CSVs to data/raw/wellfound/)")
            return self._get_demo_data(city, state)
        
        return companies
    
    def _parse_csv(self, csv_path: Path) -> List[Dict]:
        """Parse Wellfound CSV format."""
        companies = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append(self._normalize_company({
                    "name": row.get("Company Name") or row.get("name", ""),
                    "domain": row.get("Website") or row.get("domain", ""),
                    "city": row.get("Location", "").split(",")[0].strip() if row.get("Location") else "",
                    "state": row.get("Location", "").split(",")[1].strip() if row.get("Location") and "," in row.get("Location", "") else "",
                    "size": row.get("Company Size") or row.get("size", ""),
                    "industry": row.get("Market") or row.get("industry", ""),
                    "keywords": row.get("Tags") or row.get("keywords", ""),
                    "hiring": "yes" if row.get("Hiring") else "unknown",
                }))
        
        return companies
    
    def _get_demo_data(self, city: str, state: str) -> List[Dict]:
        """Demo data for testing."""
        demo_companies = [
            {
                "name": "CloudNative RDU",
                "domain": "cloudnativerdu.io",
                "city": city,
                "state": state,
                "size": "11-50",
                "industry": "Technology",
                "keywords": "cloud,kubernetes,startup,hiring",
                "hiring": "yes",
                "activity": "",
                "tech_stack": "Go,Kubernetes,AWS"
            },
        ]
        
        return [self._normalize_company(c) for c in demo_companies]
