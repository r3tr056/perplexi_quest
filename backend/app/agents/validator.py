import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import json
import re
from dataclasses import dataclass

from app.core.sonar_client import PerplexitySonarClient
from app.core.prompt_templates import PromptTemplateManager
from backend.app.db.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

@dataclass
class FactValidationResult:
    claim: str
    validation_status: str  # "verified", "refuted", "partially_verified", "insufficient_evidence"
    confidence_score: float
    evidence_sources: List[Dict[str, Any]]
    contradicting_sources: List[Dict[str, Any]]
    consensus_analysis: Dict[str, Any]
    temporal_validation: Dict[str, Any]
    expert_verification: Dict[str, Any]

class HighPerformanceFactValidator:
    """
    Advanced fact validation agent using multi-source verification:
    - Cross-source verification
    - Temporal fact checking
    - Expert consensus analysis
    - Evidence strength assessment
    - Bias detection and mitigation
    - Uncertainty quantification
    """

    def __init__(self, sonar_client: PerplexitySonarClient, vector_store: VectorStoreManager):
        self.sonar_client = sonar_client
        self.vector_store = vector_store
        self.prompt_manager = PromptTemplateManager()
        self.validation_threshold = 0.75
        self.max_sources_per_claim = 10

    async def validate_report(
        self, 
        report: Dict[str, Any], 
        research_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of research report
        """
        try:
            # Stage 1: Extract and categorize claims
            claims_extraction = await self._extract_factual_claims(report, research_results)
            
            # Stage 2: Multi-source verification
            verification_results = await self._multi_source_verification(claims_extraction["claims"])
            
            # Stage 3: Temporal validation
            temporal_validation = await self._temporal_fact_validation(verification_results)
            
            # Stage 4: Expert consensus analysis
            consensus_analysis = await self._expert_consensus_analysis(verification_results)
            
            # Stage 5: Bias detection and mitigation
            bias_analysis = await self._detect_and_mitigate_bias(verification_results)
            
            # Stage 6: Uncertainty quantification
            uncertainty_assessment = await self._quantify_validation_uncertainty(verification_results)
            
            # Stage 7: Final validation synthesis
            validation_synthesis = await self._synthesize_validation_results(
                verification_results, temporal_validation, consensus_analysis, 
                bias_analysis, uncertainty_assessment
            )

            return {
                "validation_id": f"validation_{datetime.utcnow().timestamp()}",
                "methodology": "high_performance_multi_stage_validation",
                "validation_timestamp": datetime.utcnow().isoformat(),
                "claims_analyzed": len(claims_extraction["claims"]),
                "claims_extraction": claims_extraction,
                "verification_results": verification_results,
                "temporal_validation": temporal_validation,
                "consensus_analysis": consensus_analysis,
                "bias_analysis": bias_analysis,
                "uncertainty_assessment": uncertainty_assessment,
                "validation_synthesis": validation_synthesis,
                "overall_validation_score": self._calculate_overall_validation_score(validation_synthesis),
                "validation_summary": self._generate_validation_summary(validation_synthesis)
            }

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {"error": str(e), "validation_status": "failed"}

    async def _extract_factual_claims(self, report: Dict[str, Any], research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract factual claims from the report for validation"""
        
        extraction_prompt = self.prompt_manager.get_template("factual_claims_extraction").format(
            report_content=json.dumps(report),
            research_context=json.dumps(research_results),
            extraction_criteria="statistical claims, causal statements, temporal assertions, quantitative data, authoritative statements"
        )

        response = await self.sonar_client.search(
            extraction_prompt,
            temperature=0.1,
            max_tokens=2000
        )

        # Parse extracted claims
        claims = self._parse_extracted_claims(response.content)
        
        # Categorize claims by type and importance
        categorized_claims = self._categorize_claims(claims)

        return {
            "extraction_method": "llm_guided_extraction",
            "total_claims": len(claims),
            "claims": claims,
            "categorized_claims": categorized_claims,
            "extraction_quality": self._assess_extraction_quality(claims, report)
        }

    async def _multi_source_verification(self, claims: List[Dict[str, Any]]) -> List[FactValidationResult]:
        """Verify claims against multiple independent sources"""
        
        validation_results = []
        
        for claim_data in claims:
            claim_text = claim_data["claim"]
            
            # Generate verification query
            verification_query = f"""
            Fact-check this specific claim with multiple authoritative sources: "{claim_text}"
            
            Provide:
            1. Evidence supporting the claim from reputable sources
            2. Evidence contradicting the claim from reputable sources  
            3. Source credibility assessment
            4. Confidence level in the verification
            5. Any important nuances or context
            
            Be thorough and cite specific sources with dates.
            """

            # Execute verification search
            verification_response = await self.sonar_client.search(
                verification_query,
                temperature=0.1,
                max_tokens=1500
            )

            # Cross-verify with alternative search
            alternative_query = f"""
            Independent verification: Is this statement accurate? "{claim_text}"
            
            Check against:
            - Recent authoritative publications
            - Official statistics and data
            - Expert consensus in the field
            - Historical accuracy if applicable
            
            Provide specific contradictory evidence if the claim is false.
            """

            alternative_response = await self.sonar_client.search(
                alternative_query,
                temperature=0.1,
                max_tokens=1200
            )

            # Analyze verification results
            validation_result = await self._analyze_verification_responses(
                claim_text, verification_response, alternative_response, claim_data
            )
            
            validation_results.append(validation_result)

        return validation_results

    async def _temporal_fact_validation(self, verification_results: List[FactValidationResult]) -> Dict[str, Any]:
        """Validate facts with temporal awareness"""
        
        temporal_validations = []
        
        for result in verification_results:
            # Check if claim has temporal components
            if self._has_temporal_component(result.claim):
                temporal_prompt = self.prompt_manager.get_template("temporal_validation").format(
                    claim=result.claim,
                    current_date="2025-05-26",
                    validation_context=json.dumps({
                        "status": result.validation_status,
                        "confidence": result.confidence_score
                    })
                )

                temporal_response = await self.sonar_client.search(
                    temporal_prompt,
                    temperature=0.1,
                    max_tokens=800
                )

                temporal_analysis = {
                    "claim": result.claim,
                    "temporal_validity": self._parse_temporal_validity(temporal_response.content),
                    "time_sensitivity": self._assess_time_sensitivity(result.claim),
                    "update_frequency": self._determine_update_frequency(result.claim),
                    "temporal_confidence": self._calculate_temporal_confidence(temporal_response.content)
                }

                temporal_validations.append(temporal_analysis)

        return {
            "temporal_validations": temporal_validations,
            "temporal_risk_assessment": self._assess_temporal_risk(temporal_validations),
            "recommended_revalidation_schedule": self._create_revalidation_schedule(temporal_validations)
        }

    async def _expert_consensus_analysis(self, verification_results: List[FactValidationResult]) -> Dict[str, Any]:
        """Analyze expert consensus for each claim"""
        
        consensus_analyses = []
        
        for result in verification_results:
            consensus_prompt = self.prompt_manager.get_template("expert_consensus_analysis").format(
                claim=result.claim,
                evidence_sources=json.dumps([s.get("title", "") for s in result.evidence_sources]),
                field_context=self._identify_relevant_field(result.claim)
            )

            consensus_response = await self.sonar_client.search(
                consensus_prompt,
                temperature=0.1,
                max_tokens=1000
            )

            consensus_analysis = {
                "claim": result.claim,
                "expert_field": self._identify_relevant_field(result.claim),
                "consensus_level": self._parse_consensus_level(consensus_response.content),
                "expert_positions": self._extract_expert_positions(consensus_response.content),
                "consensus_confidence": self._calculate_consensus_confidence(consensus_response.content),
                "dissenting_opinions": self._identify_dissenting_opinions(consensus_response.content)
            }

            consensus_analyses.append(consensus_analysis)

        return {
            "consensus_analyses": consensus_analyses,
            "overall_consensus_strength": self._calculate_overall_consensus_strength(consensus_analyses),
            "consensus_reliability": self._assess_consensus_reliability(consensus_analyses)
        }

    async def _detect_and_mitigate_bias(self, verification_results: List[FactValidationResult]) -> Dict[str, Any]:
        """Detect potential biases in sources and validation"""
        
        bias_analyses = []
        
        # Analyze source diversity
        all_sources = []
        for result in verification_results:
            all_sources.extend(result.evidence_sources)
            all_sources.extend(result.contradicting_sources)

        source_diversity = self._analyze_source_diversity(all_sources)
        
        # Bias detection for each claim
        for result in verification_results:
            bias_prompt = self.prompt_manager.get_template("bias_detection").format(
                claim=result.claim,
                sources=json.dumps(result.evidence_sources + result.contradicting_sources),
                validation_status=result.validation_status
            )

            bias_response = await self.sonar_client.search(
                bias_prompt,
                temperature=0.1,
                max_tokens=1000
            )

            bias_analysis = {
                "claim": result.claim,
                "detected_biases": self._parse_detected_biases(bias_response.content),
                "source_bias_assessment": self._assess_source_bias(result.evidence_sources),
                "confirmation_bias_risk": self._assess_confirmation_bias_risk(result),
                "mitigation_recommendations": self._generate_bias_mitigation_recommendations(bias_response.content)
            }

            bias_analyses.append(bias_analysis)

        return {
            "source_diversity": source_diversity,
            "bias_analyses": bias_analyses,
            "overall_bias_risk": self._calculate_overall_bias_risk(bias_analyses),
            "bias_mitigation_plan": self._create_bias_mitigation_plan(bias_analyses)
        }

    async def _quantify_validation_uncertainty(self, verification_results: List[FactValidationResult]) -> Dict[str, Any]:
        """Quantify uncertainty in validation results"""
        
        uncertainty_analyses = []
        
        for result in verification_results:
            uncertainty_sources = {
                "source_reliability": self._assess_source_reliability_uncertainty(result.evidence_sources),
                "evidence_completeness": self._assess_evidence_completeness_uncertainty(result),
                "temporal_uncertainty": self._assess_temporal_uncertainty(result.claim),
                "methodological_uncertainty": self._assess_methodological_uncertainty(result),
                "consensus_uncertainty": self._assess_consensus_uncertainty(result.consensus_analysis) if hasattr(result, 'consensus_analysis') else 0.5
            }

            total_uncertainty = self._calculate_total_uncertainty(uncertainty_sources)
            
            uncertainty_analysis = {
                "claim": result.claim,
                "uncertainty_sources": uncertainty_sources,
                "total_uncertainty": total_uncertainty,
                "confidence_interval": self._calculate_confidence_interval(result.confidence_score, total_uncertainty),
                "uncertainty_category": self._categorize_uncertainty_level(total_uncertainty)
            }

            uncertainty_analyses.append(uncertainty_analysis)

        return {
            "uncertainty_analyses": uncertainty_analyses,
            "overall_uncertainty_score": self._calculate_overall_uncertainty(uncertainty_analyses),
            "uncertainty_recommendations": self._generate_uncertainty_recommendations(uncertainty_analyses)
        }

    async def _synthesize_validation_results(
        self, 
        verification_results: List[FactValidationResult],
        temporal_validation: Dict[str, Any],
        consensus_analysis: Dict[str, Any],
        bias_analysis: Dict[str, Any],
        uncertainty_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize all validation results into final assessment"""
        
        synthesis_prompt = self.prompt_manager.get_template("validation_synthesis").format(
            verification_summary=json.dumps([{
                "claim": r.claim,
                "status": r.validation_status,
                "confidence": r.confidence_score
            } for r in verification_results]),
            temporal_insights=json.dumps(temporal_validation),
            consensus_insights=json.dumps(consensus_analysis),
            bias_insights=json.dumps(bias_analysis),
            uncertainty_insights=json.dumps(uncertainty_assessment)
        )

        synthesis_response = await self.sonar_client.search(
            synthesis_prompt,
            temperature=0.1,
            max_tokens=2000
        )

        # Calculate final validation metrics
        validation_metrics = self._calculate_validation_metrics(
            verification_results, temporal_validation, consensus_analysis, 
            bias_analysis, uncertainty_assessment
        )

        return {
            "synthesis_narrative": synthesis_response.content,
            "validation_metrics": validation_metrics,
            "validated_claims": [r for r in verification_results if r.validation_status == "verified"],
            "refuted_claims": [r for r in verification_results if r.validation_status == "refuted"],
            "uncertain_claims": [r for r in verification_results if r.validation_status in ["partially_verified", "insufficient_evidence"]],
            "high_confidence_validations": [r for r in verification_results if r.confidence_score >= 0.8],
            "recommendations": self._generate_validation_recommendations(verification_results, validation_metrics),
            "validation_quality_score": validation_metrics.get("overall_quality", 0.0)
        }

    # Helper methods for analysis and calculations
    
    def _parse_extracted_claims(self, content: str) -> List[Dict[str, Any]]:
        """Parse claims extracted by LLM"""
        claims = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 'claim:' in line.lower()):
                claim_text = re.sub(r'^[-•]\s*', '', line)
                claim_text = re.sub(r'claim:\s*', '', claim_text, flags=re.IGNORECASE)
                
                if len(claim_text) > 10:  # Filter out very short claims
                    claims.append({
                        "claim": claim_text.strip(),
                        "category": self._categorize_claim_type(claim_text),
                        "importance": self._assess_claim_importance(claim_text),
                        "verifiability": self._assess_claim_verifiability(claim_text)
                    })
        
        return claims

    def _categorize_claim_type(self, claim: str) -> str:
        """Categorize the type of claim"""
        claim_lower = claim.lower()
        
        if any(indicator in claim_lower for indicator in ['%', 'percent', 'million', 'billion', 'increased', 'decreased']):
            return "statistical"
        elif any(indicator in claim_lower for indicator in ['causes', 'leads to', 'results in', 'due to']):
            return "causal"
        elif any(indicator in claim_lower for indicator in ['in 2024', 'in 2025', 'recently', 'last year']):
            return "temporal"
        elif any(indicator in claim_lower for indicator in ['according to', 'study shows', 'research indicates']):
            return "authoritative"
        else:
            return "general"

    def _assess_claim_importance(self, claim: str) -> float:
        """Assess the importance/impact of a claim"""
        importance_indicators = {
            'high': ['critical', 'major', 'significant', 'breakthrough', 'revolutionary'],
            'medium': ['important', 'notable', 'considerable', 'substantial'],
            'low': ['minor', 'slight', 'small', 'limited']
        }
        
        claim_lower = claim.lower()
        for level, indicators in importance_indicators.items():
            if any(indicator in claim_lower for indicator in indicators):
                return {"high": 0.9, "medium": 0.6, "low": 0.3}[level]
        
        return 0.5  # Default medium importance

    def _calculate_overall_validation_score(self, validation_synthesis: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        metrics = validation_synthesis.get("validation_metrics", {})
        
        weights = {
            "verification_rate": 0.3,
            "confidence_average": 0.25,
            "consensus_strength": 0.2,
            "bias_mitigation": 0.15,
            "uncertainty_management": 0.1
        }
        
        weighted_score = 0
        for metric, weight in weights.items():
            score = metrics.get(metric, 0.5)
            weighted_score += score * weight
        
        return min(1.0, max(0.0, weighted_score))

    async def _analyze_verification_responses(
        self, 
        claim: str, 
        primary_response: Any, 
        alternative_response: Any, 
        claim_data: Dict[str, Any]
    ) -> FactValidationResult:
        """Analyze verification responses and create validation result"""
        
        # Extract evidence from responses
        evidence_sources = self._extract_evidence_sources(primary_response.content, primary_response.sources)
        contradicting_sources = self._extract_contradicting_sources(alternative_response.content, alternative_response.sources)
        
        # Determine validation status
        validation_status = self._determine_validation_status(
            primary_response.content, alternative_response.content, evidence_sources, contradicting_sources
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_validation_confidence(
            validation_status, evidence_sources, contradicting_sources, 
            primary_response.content, alternative_response.content
        )
        
        # Create consensus analysis placeholder
        consensus_analysis = {
            "method": "multi_source_comparison",
            "agreement_level": self._assess_source_agreement(evidence_sources, contradicting_sources)
        }
        
        # Create temporal validation placeholder
        temporal_validation = {
            "temporal_relevance": self._assess_temporal_relevance(claim),
            "last_updated": "2025-05-26"
        }
        
        # Expert verification placeholder
        expert_verification = {
            "expert_sources_count": len([s for s in evidence_sources if self._is_expert_source(s)]),
            "expert_consensus": self._assess_expert_consensus_simple(evidence_sources)
        }

        return FactValidationResult(
            claim=claim,
            validation_status=validation_status,
            confidence_score=confidence_score,
            evidence_sources=evidence_sources,
            contradicting_sources=contradicting_sources,
            consensus_analysis=consensus_analysis,
            temporal_validation=temporal_validation,
            expert_verification=expert_verification
        )