from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timezone
import json

from app.core.sonar_client import PerplexitySonarClient
from app.db.vector_store import VectorStoreManager
from app.core.prompt_templates import PromptTemplateManager

logger = logging.getLogger(__name__)

class DeepResearchAgent:
    """Deep Research agent"""

    def __init__(self, sonar_client: PerplexitySonarClient, vector_store: VectorStoreManager):
        self.sonar_client = sonar_client
        self.vector_store = vector_store
        self.prompt_manager = PromptTemplateManager()

    async def conduct_comprehensive_research(self, query: str, domain: str = "general") -> Dict[str, Any]:
        """
        Comprehensive research using multiple search approaches
        1. Initial deep research
        2. Multi-perspective analysis
        3. Fact Verification for key claims
        4. Structured Synthesis
        """

        try:
            research_id = f"enhanced_research_{datetime.now(timezone.utc).timestamp()}"
            
            # 1. Initial deep research
            logger.info(f"Starting deep research for: {query}")
            initial_research = await self.sonar_client.deep_research_search(
                query=query,
                context=f"Domain: {domain}. Conduct comprehensive analysis with current information as of 2025-05-26.",
                max_tokens=4000,
                include_images=True,
                recency_filter="month"
            )

            # 2. Multi-perspective analysis
            logger.info("Conducting multi-perspective analysis")
            perspectives = ["academic_researcher", "industry_expert", "policy_analyst", "technical_specialist"]
            perspective_results = await self.sonar_client.multi_perspective_search(
                query=query,
                perspectives=perspectives,
                max_tokens=2500
            )

            # 3. Fact verification for key claims
            logger.info("Extracting and verifying key claims")
            key_claims = self._extract_key_claims(initial_research.content)
            verification_results = []
            # top 5 claims
            for claim in key_claims[:5]:
                try:
                    verification = await self.sonar_client.fact_check_search(
                        claim=claim,
                        verification_level="strict",
                        max_tokens=1500
                    )
                    verification_results.append({
                        "claim": claim,
                        "verification": verification.content,
                        "sources": verification.sources
                    })
                except Exception as e:
                    logger.error(f"Error verifying claim '{claim}': {str(e)}")

            # 4. Structured synthesis
            logger.info("Creating structured synthesis")
            synthesis_schema = {
                "executive_summary": "Brief 2-3 sentence overview",
                "key_findings": ["List of 5-7 key findings"],
                "evidence_strength": "Assessment of overall evidence quality",
                "confidence_level": "Overall confidence score 0-100",
                "recommendations": ["List of actionable recommendations"],
                "knowledge_gaps": ["Areas needing further research"],
                "implications": {
                    "short_term": "Immediate implications",
                    "long_term": "Future implications"
                }
            }

            synthesis_query = f"""
            Based on comprehensive research about '{query}', provide a structured synthesis.
            
            Research findings:
            {initial_research.content[:2000]}
            
            Multi-perspective insights:
            {json.dumps([r.content[:500] for r in perspective_results], indent=2)}
            
            Verification results:
            {json.dumps([v["verification"][:300] for v in verification_results], indent=2)}
            """

            synthesis_result = await self.sonar_client.structured_search(
                query=synthesis_query,
                output_schema=synthesis_schema,
                model="sonar-reasoning-pro",
                max_tokens=3000
            )
            related_questions = initial_research.related_questions
            
            await self._store_research_results(research_id, query, {
                "initial_research": initial_research,
                "perspective_results": perspective_results,
                "verification_results": verification_results,
                "synthesis": synthesis_result
            })

            return {
                "research_id": research_id,
                "query": query,
                "domain": domain,
                "methodology": "enhanced_multi_model_research",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": {
                    "initial_research": {
                        "content": initial_research.content,
                        "sources": initial_research.sources,
                        "model_used": initial_research.model_used,
                        "tokens_used": initial_research.tokens_used,
                        "images": initial_research.images
                    },
                    "perspective_analysis": [
                        {
                            "perspective": perspectives[i] if i < len(perspectives) else "unknown",
                            "content": result.content,
                            "sources": result.sources,
                            "model_used": result.model_used
                        }
                        for i, result in enumerate(perspective_results)
                    ],
                    "fact_verification": verification_results,
                    "structured_synthesis": {
                        "content": synthesis_result.content,
                        "sources": synthesis_result.sources,
                        "model_used": synthesis_result.model_used
                    },
                    "related_questions": related_questions
                },
                "quality_metrics": {
                    "total_sources": len(initial_research.sources) + sum(len(r.sources) for r in perspective_results),
                    "verified_claims": len([v for v in verification_results if "VERIFIED" in v.get("verification", "")]),
                    "perspectives_analyzed": len(perspective_results),
                    "research_depth_score": self._calculate_research_depth_score(initial_research, perspective_results),
                    "source_diversity_score": self._calculate_source_diversity_score(initial_research, perspective_results)
                }
            }

        except Exception as e:
            logger.error(f"Enhanced research error: {str(e)}")
            return {"error": str(e), "query": query, "research_id": research_id}

    async def targeted_domain_research(
        self, 
        query: str, 
        domain: str,
        trusted_domains: List[str] = None,
        blocked_domains: List[str] = None
    ) -> Dict[str, Any]:
        """Conduct research with domain-specific filtering"""

        try:
            # Default trusted domains for different research areas
            domain_trusted_sources = {
                "academic": ["scholar.google.com", "pubmed.ncbi.nlm.nih.gov", "ieee.org", "acm.org"],
                "medical": ["pubmed.ncbi.nlm.nih.gov", "nejm.org", "bmj.com", "who.int", "cdc.gov"],
                "technology": ["ieee.org", "acm.org", "arxiv.org", "github.com"],
                "business": ["harvard.edu", "bloomberg.com", "reuters.com", "wsj.com"],
                "policy": ["gov", "un.org", "oecd.org", "brookings.edu"],
                "news": ["reuters.com", "ap.org", "bbc.com", "npr.org"]
            }

            if trusted_domains is None:
                trusted_domains = domain_trusted_sources.get(domain, [])

            default_blocked = ["reddit.com", "quora.com", "yahoo.com"] if blocked_domains is None else blocked_domains
            filtered_result = await self.sonar_client.search_with_domain_filter(
                query=query,
                allowed_domains=trusted_domains,
                blocked_domains=default_blocked,
                model="sonar-deep-research",
                max_tokens=3500
            )

            reasoning_result = await self.sonar_client.reasoning_search(
                query=f"Analyze and synthesize findings about: {query}",
                reasoning_type="analytical",
                max_tokens=2500
            )

            return {
                "query": query,
                "domain": domain,
                "filtered_research": {
                    "content": filtered_result.content,
                    "sources": filtered_result.sources,
                    "trusted_domains_used": trusted_domains,
                    "blocked_domains": default_blocked
                },
                "reasoning_analysis": {
                    "content": reasoning_result.content,
                    "sources": reasoning_result.sources,
                    "model_used": reasoning_result.model_used
                },
                "quality_assessment": {
                    "source_reliability": self._assess_source_reliability(filtered_result.sources),
                    "domain_coverage": len(set(self._extract_domains_from_sources(filtered_result.sources))),
                    "reasoning_quality": self._assess_reasoning_quality(reasoning_result.content)
                }
            }

        except Exception as e:
            logger.error(f"Targeted domain research error: {str(e)}")
            return {"error": str(e), "query": query, "domain": domain}

    async def real_time_research_update(self, query: str, previous_research_id: str) -> Dict[str, Any]:
        """
        Update previous research with latest information in realtime
        - Get research from vector store
        - Conduct a fresh search with updated filters
        - Compare with previous findings
        - Generate an analysis
        """
        try:
            previous_results = await self.vector_store.semantic_search_research_artifacts(
                query=query,
                limit=5,
                min_certainty=0.8
            )
            fresh_research = await self.sonar_client.deep_research_search(
                query=f"Latest developments and updates about: {query}",
                context=f"Previous research conducted. Focus on new information since {datetime.now(timezone.utc).isoformat()}",
                max_tokens=3000,
                recency_filter="week"
            )

            comparison_query = f"""
            Compare these new findings with previous research:
            
            NEW RESEARCH:
            {fresh_research.content[:1500]}
            
            PREVIOUS RESEARCH SUMMARY:
            {json.dumps([r.get('content', '')[:300] for r in previous_results], indent=2)}
            
            Identify:
            1. What's genuinely new or changed
            2. What remains consistent
            3. Any contradictions or updates needed
            4. Emerging trends or developments
            """
            comparison_result = await self.sonar_client.reasoning_search(
                query=comparison_query,
                reasoning_type="analytical",
                max_tokens=2000
            )

            return {
                "query": query,
                "previous_research_id": previous_research_id,
                "update_timestamp": datetime.utcnow().isoformat(),
                "fresh_research": {
                    "content": fresh_research.content,
                    "sources": fresh_research.sources,
                    "model_used": fresh_research.model_used
                },
                "comparison_analysis": {
                    "content": comparison_result.content,
                    "sources": comparison_result.sources
                },
                "change_summary": {
                    "new_developments": self._extract_new_developments(comparison_result.content),
                    "updated_information": self._extract_updates(comparison_result.content),
                    "consistency_check": self._check_consistency(comparison_result.content),
                    "reliability_assessment": "high" if len(fresh_research.sources) >= 3 else "medium"
                }
            }

        except Exception as e:
            logger.error(f"Real-time research update error: {str(e)}")
            return {"error": str(e), "query": query}

    def _extract_key_claims(self, content: str) -> List[str]:
        """Extract key factual claims from research content"""
        claims = []
        
        # Look for statistical claims
        import re
        stat_patterns = [
            r'\d+%',
            r'\d+\.\d+%', 
            r'\$\d+',
            r'\d+\s*(million|billion|thousand)',
            r'increased by \d+',
            r'decreased by \d+'
        ]
        
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in stat_patterns):
                claims.append(sentence)

            elif any(indicator in sentence.lower() for indicator in [
                'according to', 'research shows', 'study found', 'data indicates', 
                'experts report', 'analysis reveals', 'evidence suggests'
            ]):
                claims.append(sentence)
        
        return claims[:10]

    async def _store_research_results(self, research_id: str, query: str, results: Dict[str, Any]):
        """Store research results in vector database"""
        try:
            await self.vector_store.store_research_artifact(
                session_id=research_id,
                artifact_type="comprehensive_research",
                content=results,
                domain="general",
                source="enhanced_deep_research_agent",
                confidence=0.85,
                tags=["comprehensive", "multi_perspective", "fact_verified"]
            )
        except Exception as e:
            logger.error(f"Error storing research results: {str(e)}")

    def _calculate_research_depth_score(self, initial_research, perspective_results) -> float:
        """Calculate research depth score based on content analysis"""
        score = 0.0
        content_length = len(initial_research.content)
        source_count = len(initial_research.sources)
        score += min(content_length / 2000, 1.0) * 0.3  # Content depth
        score += min(source_count / 10, 1.0) * 0.3      # Source diversity
        score += min(len(perspective_results) / 4, 1.0) * 0.4  # Perspective coverage
        return round(score, 2)

    def _calculate_source_diversity_score(self, initial_research, perspective_results) -> float:
        """Calculate source diversity score"""
        all_sources = initial_research.sources.copy()
        for result in perspective_results:
            all_sources.extend(result.sources)

        domains = set()
        for source in all_sources:
            url = source.get('url', '')
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains.add(domain)
                except:
                    continue
        
        # Domain diversity scoring
        domain_count = len(domains)
        return min(domain_count / 8, 1.0)