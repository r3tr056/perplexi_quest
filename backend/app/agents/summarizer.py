import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json
import re

from app.core.sonar_client import PerplexitySonarClient
from app.core.prompt_templates import PromptTemplateManager
from backend.app.db.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

class AdvancedSummarizerAgent:
    """
    Advanced summarization agent using cutting-edge techniques:
    - Multi-level abstraction
    - Audience-aware summarization
    - Key entity preservation
    - Citation integrity maintenance
    - Narrative coherence optimization
    """

    def __init__(self, sonar_client: PerplexitySonarClient, vector_store: VectorStoreManager):
        self.sonar_client = sonar_client
        self.vector_store = vector_store
        self.prompt_manager = PromptTemplateManager()

    async def synthesize_findings(
        self, 
        original_query: str,
        research_plan: Dict[str, Any],
        research_results: List[Dict[str, Any]],
        target_audience: str = "general",
        summary_length: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Synthesize research findings into a comprehensive, well-structured report
        """
        try:
            # Stage 1: Content Analysis and Structuring
            content_analysis = await self._analyze_content_structure(research_results, original_query)
            
            # Stage 2: Multi-level Abstraction
            abstraction_layers = await self._create_abstraction_layers(content_analysis, research_results)
            
            # Stage 3: Audience-Aware Synthesis
            audience_synthesis = await self._audience_aware_synthesis(
                abstraction_layers, target_audience, summary_length
            )
            
            # Stage 4: Citation Integration and Verification
            citation_integration = await self._integrate_citations(audience_synthesis, research_results)
            
            # Stage 5: Narrative Coherence Optimization
            final_report = await self._optimize_narrative_coherence(citation_integration, original_query)
            
            # Stage 6: Quality Assessment
            quality_metrics = await self._assess_summary_quality(final_report, research_results)

            return {
                "synthesis_id": f"synthesis_{datetime.utcnow().timestamp()}",
                "original_query": original_query,
                "target_audience": target_audience,
                "summary_length": summary_length,
                "methodology": "advanced_multi_stage_synthesis",
                "content_analysis": content_analysis,
                "abstraction_layers": abstraction_layers,
                "final_report": final_report,
                "quality_metrics": quality_metrics,
                "synthesis_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}")
            return {"error": str(e), "query": original_query}

    async def _analyze_content_structure(self, research_results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze content structure and identify key themes"""
        
        structure_prompt = self.prompt_manager.get_template("content_structure_analysis").format(
            query=query,
            research_data=json.dumps(research_results, indent=2),
            analysis_timestamp="2025-05-26 13:21:48"
        )

        response = await self.sonar_client.search(
            structure_prompt,
            temperature=0.2,
            max_tokens=1500
        )

        # Extract structured information
        structure = {
            "main_themes": self._extract_themes(response.content),
            "key_entities": self._extract_entities_advanced(research_results),
            "information_hierarchy": self._build_information_hierarchy(response.content),
            "content_gaps": self._identify_content_gaps(response.content),
            "redundancy_analysis": self._analyze_redundancy(research_results)
        }

        return structure

    async def _create_abstraction_layers(self, content_analysis: Dict[str, Any], research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple abstraction layers for the content"""
        
        layers = {}
        
        # Layer 1: Executive Summary (highest abstraction)
        executive_prompt = self.prompt_manager.get_template("executive_abstraction").format(
            main_themes=json.dumps(content_analysis["main_themes"]),
            key_entities=json.dumps(content_analysis["key_entities"]),
            research_scope=len(research_results)
        )

        executive_response = await self.sonar_client.search(executive_prompt, temperature=0.1, max_tokens=300)
        layers["executive"] = executive_response.content

        # Layer 2: Strategic Overview (medium-high abstraction)
        strategic_prompt = self.prompt_manager.get_template("strategic_abstraction").format(
            executive_summary=layers["executive"],
            information_hierarchy=json.dumps(content_analysis["information_hierarchy"]),
            detailed_findings=json.dumps(research_results)
        )

        strategic_response = await self.sonar_client.search(strategic_prompt, temperature=0.2, max_tokens=800)
        layers["strategic"] = strategic_response.content

        # Layer 3: Detailed Analysis (medium abstraction)
        detailed_prompt = self.prompt_manager.get_template("detailed_abstraction").format(
            strategic_overview=layers["strategic"],
            all_research_data=json.dumps(research_results),
            content_structure=json.dumps(content_analysis)
        )

        detailed_response = await self.sonar_client.search(detailed_prompt, temperature=0.3, max_tokens=2000)
        layers["detailed"] = detailed_response.content

        # Layer 4: Comprehensive (lowest abstraction - includes most detail)
        comprehensive_prompt = self.prompt_manager.get_template("comprehensive_abstraction").format(
            detailed_analysis=layers["detailed"],
            full_research_context=json.dumps(research_results),
            preservation_requirements="Preserve all key insights, data points, and citations"
        )

        comprehensive_response = await self.sonar_client.search(comprehensive_prompt, temperature=0.2, max_tokens=3000)
        layers["comprehensive"] = comprehensive_response.content

        return layers

    async def _audience_aware_synthesis(self, abstraction_layers: Dict[str, Any], target_audience: str, summary_length: str) -> Dict[str, Any]:
        """Create audience-specific synthesis"""
        
        # Define audience parameters
        audience_configs = {
            "executive": {"tone": "formal", "technical_depth": "low", "focus": "strategic_implications"},
            "technical": {"tone": "precise", "technical_depth": "high", "focus": "methodology_and_details"},
            "academic": {"tone": "scholarly", "technical_depth": "high", "focus": "evidence_and_analysis"},
            "general": {"tone": "accessible", "technical_depth": "medium", "focus": "practical_understanding"},
            "policy": {"tone": "formal", "technical_depth": "medium", "focus": "policy_implications"}
        }

        config = audience_configs.get(target_audience, audience_configs["general"])
        
        # Select appropriate abstraction layer based on length requirement
        layer_mapping = {
            "brief": "executive",
            "standard": "strategic", 
            "comprehensive": "detailed",
            "exhaustive": "comprehensive"
        }
        
        selected_layer = layer_mapping.get(summary_length, "strategic")
        base_content = abstraction_layers[selected_layer]

        # Audience adaptation prompt
        adaptation_prompt = self.prompt_manager.get_template("audience_adaptation").format(
            base_content=base_content,
            target_audience=target_audience,
            tone=config["tone"],
            technical_depth=config["technical_depth"],
            focus_area=config["focus"],
            length_requirement=summary_length
        )

        response = await self.sonar_client.search(
            adaptation_prompt,
            temperature=0.3,
            max_tokens=2500
        )

        return {
            "audience": target_audience,
            "configuration": config,
            "adapted_content": response.content,
            "base_layer": selected_layer,
            "adaptation_quality": self._assess_adaptation_quality(response.content, config)
        }

    async def _integrate_citations(self, audience_synthesis: Dict[str, Any], research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integrate and verify citations"""
        
        # Collect all sources from research results
        all_sources = []
        for result in research_results:
            if "sources" in result and result["sources"]:
                all_sources.extend(result["sources"])

        # Remove duplicates while preserving order
        unique_sources = []
        seen_urls = set()
        for source in all_sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(url)

        # Citation integration prompt
        citation_prompt = self.prompt_manager.get_template("citation_integration").format(
            content=audience_synthesis["adapted_content"],
            available_sources=json.dumps(unique_sources),
            citation_style="academic_inline"
        )

        response = await self.sonar_client.search(
            citation_prompt,
            temperature=0.1,
            max_tokens=3000
        )

        # Verify citation accuracy
        citation_verification = await self._verify_citations(response.content, unique_sources)

        return {
            "cited_content": response.content,
            "source_bibliography": unique_sources,
            "citation_verification": citation_verification,
            "total_sources": len(unique_sources),
            "citation_density": self._calculate_citation_density(response.content)
        }

    async def _optimize_narrative_coherence(self, citation_integration: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Optimize narrative flow and coherence"""
        
        coherence_prompt = self.prompt_manager.get_template("narrative_optimization").format(
            content=citation_integration["cited_content"],
            original_query=original_query,
            optimization_goals="clarity, flow, logical_progression, engagement"
        )

        response = await self.sonar_client.search(
            coherence_prompt,
            temperature=0.2,
            max_tokens=3500
        )

        # Analyze narrative quality
        narrative_analysis = await self._analyze_narrative_quality(response.content)

        return {
            "optimized_content": response.content,
            "narrative_analysis": narrative_analysis,
            "coherence_score": narrative_analysis.get("coherence_score", 0.0),
            "readability_metrics": self._calculate_readability_metrics(response.content),
            "final_word_count": len(response.content.split()),
            "structure_quality": self._assess_structure_quality(response.content)
        }

    async def _assess_summary_quality(self, final_report: Dict[str, Any], research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive quality assessment of the summary"""
        
        quality_prompt = self.prompt_manager.get_template("summary_quality_assessment").format(
            summary_content=final_report["optimized_content"],
            original_research_scope=len(research_results),
            research_summary=json.dumps([r.get("summary", "") for r in research_results])
        )

        response = await self.sonar_client.search(
            quality_prompt,
            temperature=0.1,
            max_tokens=1000
        )

        return {
            "quality_assessment": response.content,
            "completeness_score": self._calculate_completeness_score(final_report, research_results),
            "accuracy_score": self._calculate_accuracy_score(final_report),
            "clarity_score": self._calculate_clarity_score(final_report["optimized_content"]),
            "citation_quality": self._assess_citation_quality(final_report),
            "overall_quality_score": self._calculate_overall_quality_score(final_report, research_results)
        }

    # Helper methods
    def _extract_themes(self, content: str) -> List[str]:
        """Extract main themes from content"""
        theme_indicators = ["theme:", "topic:", "main point:", "key area:"]
        themes = []
        
        for line in content.split('\n'):
            for indicator in theme_indicators:
                if indicator.lower() in line.lower():
                    theme = line.split(indicator, 1)[-1].strip()
                    if theme:
                        themes.append(theme)
        
        return themes[:5]

    def _build_information_hierarchy(self, content: str) -> Dict[str, List[str]]:
        """Build hierarchical structure of information"""
        hierarchy = {"primary": [], "secondary": [], "supporting": []}
        
        lines = content.split('\n')
        current_level = "supporting"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect hierarchy level based on formatting
            if line.startswith('#') or 'primary' in line.lower() or 'main' in line.lower():
                current_level = "primary"
            elif line.startswith('##') or 'secondary' in line.lower() or 'sub' in line.lower():
                current_level = "secondary"
            else:
                current_level = "supporting"
            
            hierarchy[current_level].append(line)
        
        return hierarchy

    def _calculate_citation_density(self, content: str) -> float:
        """Calculate citation density in the content"""
        # Count citation markers like [1], (Source:...), etc.
        citation_patterns = [r'\[\d+\]', r'\(Source:', r'\(.*?\d{4}.*?\)']
        total_citations = 0
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            total_citations += len(matches)
        
        words = len(content.split())
        return total_citations / words if words > 0 else 0

    def _calculate_readability_metrics(self, content: str) -> Dict[str, float]:
        """Calculate readability metrics"""
        sentences = content.count('.') + content.count('!') + content.count('?')
        words = len(content.split())
        syllables = self._count_syllables(content)
        
        # Flesch Reading Ease
        if sentences > 0 and words > 0:
            flesch_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        else:
            flesch_score = 0
        
        return {
            "flesch_reading_ease": max(0, min(100, flesch_score)),
            "average_sentence_length": words / sentences if sentences > 0 else 0,
            "average_syllables_per_word": syllables / words if words > 0 else 0,
            "word_count": words,
            "sentence_count": sentences
        }

    def _count_syllables(self, text: str) -> int:
        """Simple syllable counting"""
        words = text.lower().split()
        syllable_count = 0
        
        for word in words:
            word = ''.join(c for c in word if c.isalpha())
            if word:
                # Simple syllable estimation
                vowels = 'aeiouy'
                syllables = 0
                prev_was_vowel = False
                
                for char in word:
                    is_vowel = char in vowels
                    if is_vowel and not prev_was_vowel:
                        syllables += 1
                    prev_was_vowel = is_vowel
                
                # Adjust for silent 'e'
                if word.endswith('e') and syllables > 1:
                    syllables -= 1
                
                syllable_count += max(1, syllables)
        
        return syllable_count

    def _calculate_overall_quality_score(self, final_report: Dict[str, Any], research_results: List[Dict[str, Any]]) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            "completeness": 0.25,
            "accuracy": 0.25, 
            "clarity": 0.20,
            "coherence": 0.15,
            "citation_quality": 0.15
        }
        
        scores = {
            "completeness": self._calculate_completeness_score(final_report, research_results),
            "accuracy": self._calculate_accuracy_score(final_report),
            "clarity": self._calculate_clarity_score(final_report.get("optimized_content", "")),
            "coherence": final_report.get("coherence_score", 0.5),
            "citation_quality": self._assess_citation_quality_score(final_report)
        }
        
        weighted_score = sum(scores[metric] * weights[metric] for metric in weights)
        return min(1.0, max(0.0, weighted_score))