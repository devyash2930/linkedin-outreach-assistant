"""
Company Ranking Module

Scores and ranks companies based on relevance criteria from config.
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.config import load_config, get_data_dir
from db.repo import DatabaseRepo


def rank_companies(top_n: int = 50) -> Dict[str, Any]:
    """
    Score and rank companies based on configuration criteria.
    
    Args:
        top_n: Number of top companies to output
    
    Returns:
        Ranking results and statistics
    """
    config = load_config()
    db = DatabaseRepo()
    
    # Get all companies from database
    companies = db.get_all_companies()
    
    if not companies:
        print("   No companies found in database. Run 'discover' first.")
        return {"total": 0, "ranked": []}
    
    print(f"   Scoring {len(companies)} companies...")
    
    # Score each company
    scorer = CompanyScorer(config)
    scored_companies = []
    
    for company in companies:
        score, breakdown = scorer.score(company)
        company["relevance_score"] = score
        company["score_breakdown"] = breakdown
        scored_companies.append(company)
        
        # Update score in database
        db.update_company_score(company["company_id"], score)
    
    # Sort by score
    scored_companies.sort(key=lambda c: c["relevance_score"], reverse=True)
    
    # Take top N
    top_companies = scored_companies[:top_n]
    
    # Save ranked output
    output_path = save_ranked_csv(top_companies)
    
    return {
        "total": len(companies),
        "ranked": top_companies,
        "output_path": str(output_path)
    }


class CompanyScorer:
    """Scores companies based on configuration criteria."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.filters = config.get("company_filters", {})
        self.weights = config.get("ranking", {})
        
        # Pre-process include/exclude keywords
        self.include_keywords = set(
            kw.lower() for kw in self.filters.get("include_keywords", [])
        )
        self.exclude_keywords = set(
            kw.lower() for kw in self.filters.get("exclude_keywords", [])
        )
        self.target_industries = set(
            ind.lower() for ind in self.filters.get("industries", [])
        )
        self.target_sizes = set(self.filters.get("size_bands", []))
        self.exclude_domains = set(
            d.lower() for d in config.get("exclude_domains", [])
        )
    
    def score(self, company: Dict) -> tuple[float, Dict]:
        """
        Calculate relevance score for a company.
        
        Args:
            company: Company dictionary
        
        Returns:
            Tuple of (total_score, breakdown_dict)
        """
        breakdown = {}
        
        # Check for exclusions first
        if self._is_excluded(company):
            return 0.0, {"excluded": True}
        
        # Size score (0-1)
        breakdown["size"] = self._score_size(company)
        
        # Industry score (0-1)
        breakdown["industry"] = self._score_industry(company)
        
        # Keyword score (0-1)
        breakdown["keywords"] = self._score_keywords(company)
        
        # Confidence score (0-1)
        breakdown["confidence"] = company.get("confidence", 0.5)
        
        # Signal score (hiring, activity) (0-1)
        breakdown["signals"] = self._score_signals(company)
        
        # Calculate weighted total
        weights = self.weights
        total = (
            breakdown["size"] * weights.get("size_weight", 0.2) +
            breakdown["industry"] * weights.get("industry_weight", 0.3) +
            breakdown["keywords"] * weights.get("keyword_weight", 0.2) +
            breakdown["confidence"] * weights.get("confidence_weight", 0.15) +
            breakdown["signals"] * weights.get("signal_weight", 0.15)
        )
        
        return round(total, 3), breakdown
    
    def _is_excluded(self, company: Dict) -> bool:
        """Check if company should be excluded."""
        domain = company.get("domain", "").lower()
        
        # Check domain exclusion
        if domain in self.exclude_domains:
            return True
        
        # Check keyword exclusions
        company_keywords = company.get("keywords", "").lower()
        company_name = company.get("company_name", "").lower()
        company_industry = company.get("industry", "").lower()
        
        text_to_check = f"{company_keywords} {company_name} {company_industry}"
        
        for excl_kw in self.exclude_keywords:
            if excl_kw in text_to_check:
                return True
        
        return False
    
    def _score_size(self, company: Dict) -> float:
        """Score based on company size."""
        size = company.get("size_band", "")
        
        if not size:
            return 0.3  # Unknown size gets partial score
        
        if size in self.target_sizes:
            return 1.0
        
        # Partial score for adjacent sizes
        size_order = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
        
        if size in size_order:
            size_idx = size_order.index(size)
            for target_size in self.target_sizes:
                if target_size in size_order:
                    target_idx = size_order.index(target_size)
                    distance = abs(size_idx - target_idx)
                    if distance == 1:
                        return 0.5
                    elif distance == 2:
                        return 0.2
        
        return 0.0
    
    def _score_industry(self, company: Dict) -> float:
        """Score based on industry match."""
        industry = company.get("industry", "").lower()
        
        if not industry:
            return 0.2  # Unknown industry gets small score
        
        # Exact match
        if industry in self.target_industries:
            return 1.0
        
        # Partial match (industry contains target or vice versa)
        for target in self.target_industries:
            if target in industry or industry in target:
                return 0.7
        
        return 0.0
    
    def _score_keywords(self, company: Dict) -> float:
        """Score based on keyword matches."""
        company_keywords = company.get("keywords", "").lower()
        company_name = company.get("company_name", "").lower()
        recent_activity = company.get("recent_activity", "").lower()
        
        text_to_check = f"{company_keywords} {company_name} {recent_activity}"
        
        if not text_to_check.strip():
            return 0.0
        
        # Count matching keywords
        matches = 0
        for incl_kw in self.include_keywords:
            if incl_kw in text_to_check:
                matches += 1
        
        if not self.include_keywords:
            return 0.5
        
        # Score based on match percentage
        return min(1.0, matches / max(1, len(self.include_keywords) * 0.3))
    
    def _score_signals(self, company: Dict) -> float:
        """Score based on intent signals (hiring, activity)."""
        score = 0.0
        
        # Hiring signal
        hiring = company.get("hiring_signal", "unknown")
        if hiring == "yes":
            score += 0.5
        elif hiring == "unknown":
            score += 0.1
        
        # Recent activity
        activity = company.get("recent_activity", "")
        if activity:
            activity_lower = activity.lower()
            
            # High-value activity signals
            high_value = ["series", "funding", "raised", "expansion", "launch", "new office"]
            for signal in high_value:
                if signal in activity_lower:
                    score += 0.5
                    break
        
        return min(1.0, score)


def save_ranked_csv(companies: List[Dict], filename: str = "companies_ranked.csv") -> Path:
    """Save ranked companies to CSV."""
    output_dir = get_data_dir("out")
    output_path = output_dir / filename
    
    columns = [
        "rank", "company_id", "company_name", "domain", "relevance_score",
        "hq_city", "hq_state", "size_band", "industry", "keywords",
        "hiring_signal", "recent_activity", "sources", "confidence"
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for idx, company in enumerate(companies, 1):
            company["rank"] = idx
            writer.writerow(company)
    
    return output_path
