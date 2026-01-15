"""
Company Deduplication Module

Deduplicates company records based on domain and name similarity.
"""

from typing import Dict, List, Tuple
from difflib import SequenceMatcher


def dedupe_companies(companies: List[Dict]) -> List[Dict]:
    """
    Deduplicate company records.
    
    Strategy:
    1. Exact domain match -> merge
    2. High name similarity + same city -> merge
    3. Keep highest confidence record as base
    
    Args:
        companies: List of normalized company dictionaries
    
    Returns:
        Deduplicated list of companies
    """
    if not companies:
        return []
    
    # Index by domain
    domain_index: Dict[str, List[Dict]] = {}
    no_domain: List[Dict] = []
    
    for company in companies:
        domain = company.get("domain", "").strip()
        if domain:
            if domain not in domain_index:
                domain_index[domain] = []
            domain_index[domain].append(company)
        else:
            no_domain.append(company)
    
    # Merge duplicates by domain
    deduped = []
    
    for domain, matches in domain_index.items():
        if len(matches) == 1:
            deduped.append(matches[0])
        else:
            merged = _merge_companies(matches)
            deduped.append(merged)
    
    # Handle companies without domain (use name similarity)
    for company in no_domain:
        similar_idx = _find_similar_by_name(company, deduped)
        if similar_idx is not None:
            deduped[similar_idx] = _merge_companies([deduped[similar_idx], company])
        else:
            deduped.append(company)
    
    return deduped


def _merge_companies(companies: List[Dict]) -> Dict:
    """
    Merge multiple company records into one.
    
    Strategy:
    - Use highest confidence record as base
    - Combine sources
    - Fill in missing fields from other records
    """
    if not companies:
        return {}
    
    if len(companies) == 1:
        return companies[0]
    
    # Sort by confidence (highest first)
    sorted_companies = sorted(
        companies, 
        key=lambda c: c.get("confidence", 0), 
        reverse=True
    )
    
    base = sorted_companies[0].copy()
    
    # Collect all sources
    all_sources = set()
    for company in companies:
        sources = company.get("sources", "")
        if sources:
            all_sources.update(s.strip() for s in sources.split(","))
    
    base["sources"] = ",".join(sorted(all_sources))
    
    # Increase confidence for multi-source attribution
    base["confidence"] = min(1.0, base.get("confidence", 0.5) + 0.1 * (len(all_sources) - 1))
    
    # Fill in missing fields from other records
    fields_to_fill = [
        "hq_city", "hq_state", "size_band", "industry", 
        "hiring_signal", "recent_activity", "tech_stack_hint"
    ]
    
    for field in fields_to_fill:
        if not base.get(field):
            for company in sorted_companies[1:]:
                if company.get(field):
                    base[field] = company[field]
                    break
    
    # Merge keywords
    all_keywords = set()
    for company in companies:
        keywords = company.get("keywords", "")
        if keywords:
            all_keywords.update(k.strip() for k in keywords.split(","))
    
    base["keywords"] = ",".join(sorted(all_keywords))
    
    return base


def _find_similar_by_name(
    company: Dict, 
    existing: List[Dict],
    threshold: float = 0.85
) -> int:
    """
    Find similar company by name in existing list.
    
    Args:
        company: Company to find match for
        existing: List of existing companies
        threshold: Minimum similarity score (0-1)
    
    Returns:
        Index of similar company, or None
    """
    company_name = company.get("company_name", "").lower()
    company_city = company.get("hq_city", "").lower()
    
    if not company_name:
        return None
    
    best_match = None
    best_score = 0
    
    for idx, existing_company in enumerate(existing):
        existing_name = existing_company.get("company_name", "").lower()
        existing_city = existing_company.get("hq_city", "").lower()
        
        # Calculate name similarity
        similarity = SequenceMatcher(None, company_name, existing_name).ratio()
        
        # Boost score if same city
        if company_city and company_city == existing_city:
            similarity += 0.1
        
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = idx
    
    return best_match


def calculate_dedup_stats(original: List[Dict], deduped: List[Dict]) -> Dict:
    """Calculate deduplication statistics."""
    return {
        "original_count": len(original),
        "deduped_count": len(deduped),
        "duplicates_removed": len(original) - len(deduped),
        "reduction_pct": round((1 - len(deduped) / len(original)) * 100, 1) if original else 0
    }
