"""
Company Data Normalization Module

Normalizes company data from various sources into a consistent format.
"""

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


def normalize_companies(companies: List[Dict]) -> List[Dict]:
    """
    Normalize a list of company records.
    
    Args:
        companies: List of raw company dictionaries
    
    Returns:
        List of normalized company dictionaries
    """
    normalized = []
    
    for company in companies:
        normalized.append(normalize_company(company))
    
    return normalized


def normalize_company(company: Dict) -> Dict:
    """
    Normalize a single company record.
    
    Normalizations applied:
    - Clean and standardize company name
    - Extract/clean domain
    - Standardize city/state
    - Normalize size bands
    - Clean industry names
    - Parse keywords
    """
    return {
        "company_name": _normalize_name(company.get("company_name", "")),
        "domain": _normalize_domain(company.get("domain", "")),
        "hq_city": _normalize_city(company.get("hq_city", "")),
        "hq_state": _normalize_state(company.get("hq_state", "")),
        "size_band": _normalize_size_band(company.get("size_band", "")),
        "industry": _normalize_industry(company.get("industry", "")),
        "keywords": _normalize_keywords(company.get("keywords", "")),
        "sources": company.get("sources", ""),
        "confidence": float(company.get("confidence", 0.5)),
        "hiring_signal": _normalize_hiring(company.get("hiring_signal", "unknown")),
        "recent_activity": company.get("recent_activity", ""),
        "tech_stack_hint": company.get("tech_stack_hint", "")
    }


def _normalize_name(name: str) -> str:
    """Clean and standardize company name."""
    if not name:
        return ""
    
    # Strip whitespace and common suffixes
    name = name.strip()
    
    # Remove common corporate suffixes for matching (keep original for display)
    # But clean up spacing
    name = re.sub(r'\s+', ' ', name)
    
    return name


def _normalize_domain(domain: str) -> str:
    """Extract and clean domain from URL or domain string."""
    if not domain:
        return ""
    
    domain = domain.strip().lower()
    
    # If it's a full URL, extract domain
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        domain = parsed.netloc
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Remove trailing slashes
    domain = domain.rstrip('/')
    
    return domain


def _normalize_city(city: str) -> str:
    """Normalize city name."""
    if not city:
        return ""
    
    city = city.strip().title()
    
    # Handle common variations
    city_map = {
        "Research Triangle Park": "RTP",
        "Research Triangle": "RTP",
        "Raleigh-Durham": "Raleigh",
        "Durham-Raleigh": "Durham",
    }
    
    return city_map.get(city, city)


def _normalize_state(state: str) -> str:
    """Normalize state to 2-letter abbreviation."""
    if not state:
        return ""
    
    state = state.strip().upper()
    
    # Full name to abbreviation
    state_map = {
        "NORTH CAROLINA": "NC",
        "SOUTH CAROLINA": "SC",
        "VIRGINIA": "VA",
        "GEORGIA": "GA",
        "CALIFORNIA": "CA",
        "NEW YORK": "NY",
        "TEXAS": "TX",
        "FLORIDA": "FL",
    }
    
    return state_map.get(state, state[:2] if len(state) > 2 else state)


def _normalize_size_band(size: str) -> str:
    """Normalize company size to standard bands."""
    if not size:
        return ""
    
    size = str(size).strip().lower()
    
    # Extract numbers if present
    numbers = re.findall(r'\d+', size)
    
    if numbers:
        max_num = max(int(n) for n in numbers)
        
        if max_num <= 10:
            return "1-10"
        elif max_num <= 50:
            return "11-50"
        elif max_num <= 200:
            return "51-200"
        elif max_num <= 500:
            return "201-500"
        elif max_num <= 1000:
            return "501-1000"
        else:
            return "1000+"
    
    # Handle text descriptions
    size_keywords = {
        "seed": "1-10",
        "early": "1-10",
        "small": "11-50",
        "startup": "11-50",
        "mid": "51-200",
        "medium": "51-200",
        "growth": "51-200",
        "large": "201-500",
        "enterprise": "500+",
    }
    
    for keyword, band in size_keywords.items():
        if keyword in size:
            return band
    
    return size


def _normalize_industry(industry: str) -> str:
    """Normalize industry name."""
    if not industry:
        return ""
    
    industry = industry.strip()
    
    # Standardize common variations
    industry_map = {
        "software development": "Software",
        "computer software": "Software",
        "information technology": "Technology",
        "it services": "Technology",
        "artificial intelligence": "AI/ML",
        "machine learning": "AI/ML",
        "health care": "HealthTech",
        "healthcare": "HealthTech",
        "financial services": "FinTech",
        "financial technology": "FinTech",
        "cyber security": "Cybersecurity",
        "information security": "Cybersecurity",
        "data science": "Data Analytics",
        "business intelligence": "Data Analytics",
    }
    
    industry_lower = industry.lower()
    return industry_map.get(industry_lower, industry.title())


def _normalize_keywords(keywords: str) -> str:
    """Normalize and dedupe keywords."""
    if not keywords:
        return ""
    
    # Split by various delimiters
    if isinstance(keywords, list):
        kw_list = keywords
    else:
        kw_list = re.split(r'[,;|]', keywords)
    
    # Clean and dedupe
    cleaned = []
    seen = set()
    
    for kw in kw_list:
        kw = kw.strip().lower().replace('-', ' ').replace('_', ' ')
        if kw and kw not in seen:
            cleaned.append(kw)
            seen.add(kw)
    
    return ",".join(cleaned)


def _normalize_hiring(hiring: str) -> str:
    """Normalize hiring signal."""
    if not hiring:
        return "unknown"
    
    hiring = str(hiring).strip().lower()
    
    if hiring in ('yes', 'true', '1', 'hiring', 'actively hiring'):
        return "yes"
    elif hiring in ('no', 'false', '0', 'not hiring', 'freeze'):
        return "no"
    else:
        return "unknown"
