import re
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import httpx
import json
from urllib.parse import urlparse, parse_qs
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

logger = logging.getLogger(__name__)

class CitationStyle(str, Enum):
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    IEEE = "ieee"
    VANCOUVER = "vancouver"
    AMA = "ama"

class SourceType(str, Enum):
    JOURNAL_ARTICLE = "journal_article"
    BOOK = "book"
    WEBSITE = "website"
    NEWS_ARTICLE = "news_article"
    CONFERENCE_PAPER = "conference_paper"
    THESIS = "thesis"
    GOVERNMENT_DOCUMENT = "government_document"
    PATENT = "patent"
    DATASET = "dataset"
    SOFTWARE = "software"

@dataclass
class Citation:
    citation_id: str
    title: str
    authors: List[str]
    publication_date: str
    source_type: SourceType
    url: str = ""
    doi: str = ""
    isbn: str = ""
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    publisher: str = ""
    institution: str = ""
    access_date: str = ""
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    citation_count: int = 0
    impact_factor: float = 0.0
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CitationValidationResult:
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]

class CitationManager:
    def __init__(self):
        self.crossref_api = "https://api.crossref.org/works"
        self.pubmed_api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.semantic_scholar_api = "https://api.semanticscholar.org/graph/v1"
        
        self.style_formatters = {
            CitationStyle.APA: self._format_apa_citation,
            CitationStyle.MLA: self._format_mla_citation,
            CitationStyle.CHICAGO: self._format_chicago_citation,
            CitationStyle.HARVARD: self._format_harvard_citation,
            CitationStyle.IEEE: self._format_ieee_citation,
            CitationStyle.VANCOUVER: self._format_vancouver_citation,
            CitationStyle.AMA: self._format_ama_citation
        }
        
        self.source_patterns = {
            SourceType.JOURNAL_ARTICLE: [
                r'doi\.org',
                r'pubmed\.ncbi\.nlm\.nih\.gov',
                r'jstor\.org',
                r'springer\.com',
                r'nature\.com',
                r'sciencedirect\.com'
            ],
            SourceType.NEWS_ARTICLE: [
                r'reuters\.com',
                r'bbc\.com',
                r'cnn\.com',
                r'nytimes\.com',
                r'theguardian\.com'
            ],
            SourceType.GOVERNMENT_DOCUMENT: [
                r'\.gov',
                r'europa\.eu',
                r'un\.org'
            ]
        }

    async def extract_citations_from_url(self, url: str) -> Citation:
        try:
            source_type = self._detect_source_type(url)
            citation_data = None
            doi = self._extract_doi_from_url(url)
            if doi:
                citation_data = await self._extract_from_crossref(doi)
            if not citation_data and 'pubmed' in url.lower():
                pmid = self._extract_pubmed_id(url)
                if pmid:
                    citation_data = await self._extract_from_pubmed(pmid)
            if not citation_data:
                citation_data = await self._extract_from_semantic_scholar(url)
            if not citation_data:
                citation_data = await self._extract_from_web_scraping(url)
            if citation_data:
                citation = self._create_citation_from_data(citation_data, url, source_type)
                citation = await self._enhance_citation_metadata(citation)
                return citation
            else:
                return self._create_basic_citation_from_url(url, source_type)
        except Exception as e:
            logger.error(f"Error extracting citation from URL {url}: {str(e)}")
            return self._create_basic_citation_from_url(url, SourceType.WEBSITE)

    async def validate_citation(self, citation: Citation) -> CitationValidationResult:
        validation_issues = []
        suggestions = []
        confidence_factors = []

        required_fields = self._get_required_fields_for_type(citation.source_type)
        for field in required_fields:
            if not getattr(citation, field, None):
                validation_issues.append(f"Missing required field: {field}")
                suggestions.append(f"Add {field} information for complete citation")
        confidence_factors.append(1.0 - (len([f for f in required_fields if not getattr(citation, f, None)]) / len(required_fields)))
        
        author_validation = await self._validate_authors(citation.authors)
        if author_validation["issues"]:
            validation_issues.extend(author_validation["issues"])
            suggestions.extend(author_validation["suggestions"])
        confidence_factors.append(author_validation["confidence"])
        
        date_validation = self._validate_publication_date(citation.publication_date)
        if date_validation["issues"]:
            validation_issues.extend(date_validation["issues"])
            suggestions.extend(date_validation["suggestions"])
        confidence_factors.append(date_validation["confidence"])
        
        if citation.doi:
            doi_validation = await self._validate_doi(citation.doi)
            if doi_validation["issues"]:
                validation_issues.extend(doi_validation["issues"])
                suggestions.extend(doi_validation["suggestions"])
            confidence_factors.append(doi_validation["confidence"])
        else:
            confidence_factors.append(0.7)
        
        if citation.url:
            url_validation = await self._validate_url_accessibility(citation.url)
            if url_validation["issues"]:
                validation_issues.extend(url_validation["issues"])
                suggestions.extend(url_validation["suggestions"])
            confidence_factors.append(url_validation["confidence"])
        
        if citation.journal:
            journal_validation = await self._validate_journal(citation.journal)
            confidence_factors.append(journal_validation["confidence"])

        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        is_valid = len(validation_issues) == 0 and overall_confidence >= 0.7
        return CitationValidationResult(
            is_valid=is_valid,
            confidence=overall_confidence,
            issues=validation_issues,
            suggestions=suggestions,
            metadata={
                "validation_timestamp": datetime.utcnow().isoformat(),
                "validator": "r3tr056",
                "confidence_breakdown": {
                    "required_fields": confidence_factors[0] if confidence_factors else 0.0,
                    "authors": confidence_factors[1] if len(confidence_factors) > 1 else 0.0,
                    "date": confidence_factors[2] if len(confidence_factors) > 2 else 0.0,
                    "doi": confidence_factors[3] if len(confidence_factors) > 3 else 0.0,
                    "url": confidence_factors[4] if len(confidence_factors) > 4 else 0.0,
                    "journal": confidence_factors[5] if len(confidence_factors) > 5 else 0.0
                }
            }
        )

    async def format_citation(self, citation: Citation, style: CitationStyle) -> str:
        try:
            formatter = self.style_formatters.get(style)
            if not formatter:
                raise ValueError(f"Unsupported citation style: {style}")
            formatted_citation = formatter(citation)
            format_validation = self._validate_citation_format(formatted_citation, style)
            if not format_validation["is_valid"]:
                logger.warning(f"Citation formatting issues: {format_validation['issues']}")
            return formatted_citation
        except Exception as e:
            logger.error(f"Error formatting citation: {str(e)}")
            return f"Error formatting citation: {citation.title}"

    async def detect_plagiarism(self, content: str, citations: List[Citation]) -> Dict[str, Any]:
        plagiarism_results = {
            "overall_risk": "low",
            "similarity_score": 0.0,
            "flagged_sections": [],
            "missing_citations": [],
            "recommendations": []
        }
        try:
            quoted_content = re.findall(r'"([^"]*)"', content)
            for quote in quoted_content:
                if len(quote) > 20:
                    citation_found = await self._find_citation_for_quote(quote, citations)
                    if not citation_found:
                        plagiarism_results["flagged_sections"].append({
                            "type": "uncited_quote",
                            "content": quote,
                            "recommendation": "Add citation for quoted content"
                        })
            sentences = re.split(r'[.!?]+', content)
            for sentence in sentences:
                if len(sentence.strip()) > 30:
                    similarity = await self._check_sentence_similarity(sentence, citations)
                    if similarity["max_similarity"] > 0.8 and not similarity["has_citation"]:
                        plagiarism_results["flagged_sections"].append({
                            "type": "potential_paraphrase",
                            "content": sentence.strip(),
                            "similarity_score": similarity["max_similarity"],
                            "similar_source": similarity["source"],
                            "recommendation": "Consider adding citation or rephrasing"
                        })
            word_count = len(content.split())
            citation_density = len(citations) / (word_count / 250)
            if citation_density < 0.5:
                plagiarism_results["recommendations"].append(
                    "Consider adding more citations to support your arguments"
                )
            flagged_word_count = sum(len(section["content"].split()) for section in plagiarism_results["flagged_sections"])
            plagiarism_results["similarity_score"] = flagged_word_count / word_count if word_count > 0 else 0.0
            if plagiarism_results["similarity_score"] > 0.3:
                plagiarism_results["overall_risk"] = "high"
            elif plagiarism_results["similarity_score"] > 0.15:
                plagiarism_results["overall_risk"] = "medium"
            return plagiarism_results
        except Exception as e:
            logger.error(f"Error detecting plagiarism: {str(e)}")
            return {"error": str(e)}

    async def generate_bibliography(
        self, 
        citations: List[Citation], 
        style: CitationStyle,
        sort_by: str = "author"
    ) -> Dict[str, Any]:
        try:
            sorted_citations = self._sort_citations(citations, sort_by)
            formatted_citations = []
            for citation in sorted_citations:
                formatted = await self.format_citation(citation, style)
                formatted_citations.append({
                    "citation_id": citation.citation_id,
                    "formatted": formatted,
                    "metadata": {
                        "source_type": citation.source_type.value,
                        "quality_score": citation.quality_score,
                        "authors": citation.authors,
                        "year": citation.publication_date[:4] if citation.publication_date else "n.d."
                    }
                })
            bibliography_stats = {
                "total_citations": len(citations),
                "source_types": self._analyze_source_types(citations),
                "publication_years": self._analyze_publication_years(citations),
                "quality_distribution": self._analyze_quality_distribution(citations),
                "journal_distribution": self._analyze_journal_distribution(citations)
            }
            return {
                "bibliography": formatted_citations,
                "style": style.value,
                "sort_order": sort_by,
                "statistics": bibliography_stats,
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "r3tr056"
            }
        except Exception as e:
            logger.error(f"Error generating bibliography: {str(e)}")
            return {"error": str(e)}

    def _format_apa_citation(self, citation: Citation) -> str:
        if len(citation.authors) == 1:
            author_str = citation.authors[0]
        elif len(citation.authors) == 2:
            author_str = f"{citation.authors[0]} & {citation.authors[1]}"
        elif len(citation.authors) > 2:
            author_str = f"{citation.authors[0]} et al."
        else:
            author_str = "Anonymous"
        year = citation.publication_date[:4] if citation.publication_date else "n.d."

        if citation.source_type == SourceType.JOURNAL_ARTICLE:
            formatted = f"{author_str} ({year}). {citation.title}. "
            if citation.journal:
                formatted += f"*{citation.journal}*"
                if citation.volume:
                    formatted += f", {citation.volume}"
                if citation.issue:
                    formatted += f"({citation.issue})"
                if citation.pages:
                    formatted += f", {citation.pages}"
            if citation.doi:
                formatted += f". https://doi.org/{citation.doi}"
            elif citation.url:
                formatted += f". {citation.url}"
                
        elif citation.source_type == SourceType.WEBSITE:
            formatted = f"{author_str} ({year}). *{citation.title}*. "
            if citation.publisher:
                formatted += f"{citation.publisher}. "
            if citation.url:
                formatted += citation.url
                
        else:
            formatted = f"{author_str} ({year}). *{citation.title}*."
            if citation.url:
                formatted += f" {citation.url}"
        
        return formatted

    def _format_mla_citation(self, citation: Citation) -> str:
        if citation.authors:
            author_str = citation.authors[0]
        else:
            author_str = "Anonymous"
        
        formatted = f'{author_str}. "{citation.title}." '
        
        if citation.source_type == SourceType.JOURNAL_ARTICLE and citation.journal:
            formatted += f"*{citation.journal}*, "
            if citation.volume:
                formatted += f"vol. {citation.volume}, "
            if citation.issue:
                formatted += f"no. {citation.issue}, "
            if citation.publication_date:
                formatted += f"{citation.publication_date}, "
            if citation.pages:
                formatted += f"pp. {citation.pages}. "
        
        if citation.url:
            formatted += f"{citation.url}. "
        
        if citation.access_date:
            formatted += f"Accessed {citation.access_date}."
        
        return formatted

    def _format_chicago_citation(self, citation: Citation) -> str:
        """Format citation in Chicago style"""
        # Implementation for Chicago style
        return f"Chicago style formatting for: {citation.title}"

    def _format_harvard_citation(self, citation: Citation) -> str:
        """Format citation in Harvard style"""
        # Implementation for Harvard style
        return f"Harvard style formatting for: {citation.title}"

    def _format_ieee_citation(self, citation: Citation) -> str:
        """Format citation in IEEE style"""
        # Implementation for IEEE style
        return f"IEEE style formatting for: {citation.title}"

    def _format_vancouver_citation(self, citation: Citation) -> str:
        """Format citation in Vancouver style"""
        # Implementation for Vancouver style
        return f"Vancouver style formatting for: {citation.title}"

    def _format_ama_citation(self, citation: Citation) -> str:
        """Format citation in AMA style"""
        # Implementation for AMA style
        return f"AMA style formatting for: {citation.title}"

    def _detect_source_type(self, url: str) -> SourceType:
        url_lower = url.lower()
        for source_type, patterns in self.source_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                return source_type
        return SourceType.WEBSITE

    def _extract_doi_from_url(self, url: str) -> Optional[str]:
        doi_patterns = [
            r'doi\.org/(.+)$',
            r'dx\.doi\.org/(.+)$',
            r'doi:(.+)$'
        ]
        for pattern in doi_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _extract_from_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.crossref_api}/{doi}",
                    headers={"Accept": "application/json"}
                )
                if response.status_code == 200:
                    data = response.json()
                    work = data.get("message", {})
                    
                    return {
                        "title": work.get("title", [""])[0],
                        "authors": [
                            f"{author.get('given', '')} {author.get('family', '')}"
                            for author in work.get("author", [])
                        ],
                        "publication_date": self._extract_date_from_crossref(work),
                        "journal": work.get("container-title", [""])[0],
                        "volume": work.get("volume", ""),
                        "issue": work.get("issue", ""),
                        "pages": work.get("page", ""),
                        "doi": doi,
                        "publisher": work.get("publisher", ""),
                        "abstract": work.get("abstract", ""),
                        "citation_count": work.get("is-referenced-by-count", 0)
                    }
        except Exception as e:
            logger.error(f"Error extracting from Crossref: {str(e)}")
        return None

    def _extract_date_from_crossref(self, work: Dict[str, Any]) -> str:
        date_parts = work.get("published-print", {}).get("date-parts", [])
        if not date_parts:
            date_parts = work.get("published-online", {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            if len(parts) >= 3:
                return f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) >= 2:
                return f"{parts[0]}-{parts[1]:02d}"
            elif len(parts) >= 1:
                return str(parts[0])
        return ""

    async def _enhance_citation_metadata(self, citation: Citation) -> Citation:
        citation.quality_score = self._calculate_citation_quality_score(citation)
        if citation.url and not citation.access_date:
            citation.access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not citation.keywords:
            citation.keywords = self._extract_keywords(citation.title, citation.abstract)
        return citation

    def _calculate_citation_quality_score(self, citation: Citation) -> float:
        score = 0.0
        if citation.doi:
            score += 0.3
        if citation.journal:
            high_impact_journals = ['nature', 'science', 'cell', 'lancet', 'nejm']
            if any(journal in citation.journal.lower() for journal in high_impact_journals):
                score += 0.4
            else:
                score += 0.2
        if citation.citation_count > 100:
            score += 0.2
        elif citation.citation_count > 10:
            score += 0.1
        completeness_fields = ['authors', 'publication_date', 'title']
        complete_fields = sum(1 for field in completeness_fields if getattr(citation, field))
        score += (complete_fields / len(completeness_fields)) * 0.1
        return min(score, 1.0)

    def _extract_keywords(self, title: str, abstract: str) -> List[str]:
        text = f"{title} {abstract}".lower()
        research_keywords = [
            'analysis', 'study', 'research', 'investigation', 'evaluation',
            'assessment', 'review', 'survey', 'method', 'approach',
            'framework', 'model', 'algorithm', 'system', 'process'
        ]
        found_keywords = [keyword for keyword in research_keywords if keyword in text]
        technical_terms = re.findall(r'\b[A-Z][a-z]+\b', title)
        return list(set(found_keywords + technical_terms))[:10]