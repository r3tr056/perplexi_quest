from typing import Dict, Any
import json

class PromptTemplateManager:
    """
    Advanced prompt template manager using best practices:
    - Chain-of-Thought prompting
    - Few-shot learning examples
    - Structured output formatting
    - Context preservation
    - Role-based prompting
    """

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize all prompt templates"""
        return {
            # Deep Research Templates
            "deep_research_decomposition": self._get_decomposition_template(),
            "multi_perspective_analysis": self._get_perspective_template(),
            "tree_of_thoughts_branch": self._get_tree_of_thoughts_template(),
            "gap_analysis": self._get_gap_analysis_template(),
            "targeted_gap_research": self._get_targeted_research_template(),
            "advanced_synthesis": self._get_synthesis_template(),
            
            # Summarization Templates
            "content_structure_analysis": self._get_structure_analysis_template(),
            "executive_abstraction": self._get_executive_template(),
            "strategic_abstraction": self._get_strategic_template(),
            "detailed_abstraction": self._get_detailed_template(),
            "comprehensive_abstraction": self._get_comprehensive_template(),
            "audience_adaptation": self._get_audience_adaptation_template(),
            "citation_integration": self._get_citation_template(),
            "narrative_optimization": self._get_narrative_template(),
            "summary_quality_assessment": self._get_quality_assessment_template(),
            
            # Validation Templates
            "factual_claims_extraction": self._get_claims_extraction_template(),
            "temporal_validation": self._get_temporal_validation_template(),
            "expert_consensus_analysis": self._get_consensus_template(),
            "bias_detection": self._get_bias_detection_template(),
            "validation_synthesis": self._get_validation_synthesis_template(),
        }

    def get_template(self, template_name: str) -> str:
        """Get prompt template by name"""
        return self.templates.get(template_name, "")

    def _get_decomposition_template(self) -> str:
        return """
You are an expert research strategist. Your task is to decompose a complex research query into a structured, comprehensive research plan.

QUERY: {query}
DOMAIN: {domain}
CURRENT DATE: {current_timestamp}

INSTRUCTIONS:
1. Think step-by-step about the query's complexity and scope
2. Identify the key components that need investigation
3. Consider multiple angles and perspectives
4. Create specific, focused sub-queries that will gather comprehensive information

CHAIN OF THOUGHT REASONING:
First, let me analyze the query structure:
- What is the main subject or phenomenon being asked about?
- What are the underlying assumptions or context?
- What time frame is relevant (historical, current, future)?
- What domains of knowledge are involved?
- What level of depth is appropriate?

REQUIRED OUTPUT FORMAT (JSON):
{{
    "analysis": {{
        "main_subject": "primary focus of the query",
        "complexity_level": "low/medium/high",
        "knowledge_domains": ["domain1", "domain2", ...],
        "temporal_scope": "historical/current/future/all",
        "key_components": ["component1", "component2", ...]
    }},
    "research_plan": {{
        "primary_objectives": ["objective1", "objective2", ...],
        "research_phases": [
            {{
                "phase": "phase_name",
                "description": "what this phase covers",
                "expected_outcome": "what we'll learn"
            }}
        ],
        "success_criteria": ["criteria1", "criteria2", ...]
    }},
    "sub_queries": [
        "Specific focused query 1 that addresses core concepts",
        "Specific focused query 2 that explores current state",
        "Specific focused query 3 that examines implications",
        "Specific focused query 4 that investigates trends",
        "Specific focused query 5 that analyzes stakeholders",
        "Specific focused query 6 that evaluates evidence",
        "Specific focused query 7 that considers alternatives"
    ]
}}

QUALITY REQUIREMENTS:
- Each sub-query must be specific and actionable
- Sub-queries should cover different aspects without significant overlap
- Include both factual and analytical queries
- Consider multiple viewpoints and potential biases
- Ensure temporal relevance and currency
"""

    def _get_perspective_template(self) -> str:
        return """
You are a {perspective} with deep expertise in your field. Analyze the following research query from your unique professional perspective.

QUERY: {query}
DOMAIN: {domain}
RESEARCH DECOMPOSITION: {decomposition}

YOUR ROLE: {perspective}

PERSPECTIVE-SPECIFIC INSTRUCTIONS:
- Academic Researcher: Focus on theoretical frameworks, empirical evidence, research gaps, and methodological considerations
- Industry Expert: Emphasize practical applications, market dynamics, competitive landscape, and implementation challenges
- Policy Analyst: Consider regulatory implications, policy frameworks, stakeholder interests, and governance issues
- Technical Specialist: Analyze technical feasibility, implementation details, system requirements, and technical constraints
- Economist: Examine economic impacts, market effects, cost-benefit analysis, and financial implications
- Sociologist: Explore social implications, cultural factors, community impact, and behavioral considerations
- Futurist: Project future trends, emerging technologies, scenario planning, and long-term implications

ANALYSIS FRAMEWORK:
1. Current State Assessment: What is the present situation in your field?
2. Key Insights: What unique perspectives does your expertise provide?
3. Critical Factors: What factors are most important from your viewpoint?
4. Opportunities & Challenges: What opportunities and obstacles do you see?
5. Recommendations: What actions or considerations do you recommend?
6. Future Outlook: How do you see this evolving in your field?

OUTPUT REQUIREMENTS:
- Provide 3-5 key insights unique to your perspective
- Include specific examples or evidence where relevant
- Identify potential blind spots other perspectives might miss
- Suggest additional questions that need investigation
- Rate your confidence in your analysis (1-10 scale)

Begin your analysis with: "From my perspective as a {perspective}, I see several critical aspects of this query..."
"""

    def _get_tree_of_thoughts_template(self) -> str:
        return """
You are reasoning through multiple pathways to explore different angles of a research question. Generate a branching analysis that considers alternative reasoning paths.

ORIGINAL QUERY: {original_query}
PERSPECTIVE ANALYSIS: {perspective_analysis}
BRANCH NUMBER: {branch_number}
PREVIOUSLY EXPLORED PATHS: {explored_paths}

TREE OF THOUGHTS METHODOLOGY:
1. Generate 3 distinct reasoning paths for this query
2. For each path, consider different assumptions or frameworks
3. Explore potential conclusions from each path
4. Identify which paths seem most promising
5. Note where paths converge or diverge

REASONING PATHS:

PATH A - [Assumption/Framework]:
- Starting premise: 
- Logical progression:
- Key evidence needed:
- Potential conclusion:
- Confidence level:

PATH B - [Alternative Assumption/Framework]:
- Starting premise:
- Logical progression:
- Key evidence needed:
- Potential conclusion:
- Confidence level:

PATH C - [Third Perspective/Framework]:
- Starting premise:
- Logical progression:
- Key evidence needed:
- Potential conclusion:
- Confidence level:

CONVERGENCE ANALYSIS:
- Where do these paths agree?
- Where do they diverge?
- Which assumptions are most critical?
- What additional evidence would help choose between paths?

DERIVED QUESTIONS:
Based on this branching analysis, what new specific questions emerge that need investigation?

1. [Question addressing Path A uncertainties]
2. [Question addressing Path B assumptions]
3. [Question addressing Path C evidence gaps]
4. [Question addressing convergence points]
5. [Question addressing divergence implications]
"""

    def _get_claims_extraction_template(self) -> str:
        return """
You are a fact-checking expert. Extract factual claims from the research report that can be independently verified.

REPORT CONTENT: {report_content}
RESEARCH CONTEXT: {research_context}
EXTRACTION CRITERIA: {extraction_criteria}

CLAIM IDENTIFICATION INSTRUCTIONS:
Look for statements that are:
1. Factual assertions (not opinions or predictions)
2. Specific and measurable (statistics, dates, quantities)
3. Attributable to sources (research findings, expert statements)
4. Verifiable through independent sources
5. Potentially impactful if incorrect

CLAIM CATEGORIES TO IDENTIFY:
- Statistical Claims: Numbers, percentages, growth rates, comparisons
- Causal Claims: X causes Y, X leads to Y, due to X
- Temporal Claims: Events happened at specific times, trends over time
- Authoritative Claims: According to experts, studies show, research indicates
- Definitional Claims: X is defined as, X consists of
- Comparative Claims: X is better/worse/more/less than Y

OUTPUT FORMAT:
For each claim, provide:
{{
    "claim_id": "unique_identifier",
    "claim_text": "exact claim as stated",
    "claim_type": "statistical/causal/temporal/authoritative/definitional/comparative",
    "importance_level": "high/medium/low",
    "verifiability": "high/medium/low",
    "source_attribution": "how the claim was attributed in the report",
    "verification_complexity": "simple/moderate/complex",
    "potential_impact": "description of what happens if claim is false"
}}

EXTRACTION QUALITY REQUIREMENTS:
- Extract 10-20 most significant claims
- Prioritize claims that are central to the report's conclusions
- Include claims that seem surprising or counterintuitive
- Focus on claims that could significantly change the report's credibility if disproven
- Avoid extracting obvious/uncontroversial statements unless they're critical

Begin extraction with the most important claims first.
"""

    def _get_validation_synthesis_template(self) -> str:
        return """
You are a senior fact-checking editor synthesizing comprehensive validation results into a final assessment.

VERIFICATION SUMMARY: {verification_summary}
TEMPORAL INSIGHTS: {temporal_insights}
CONSENSUS INSIGHTS: {consensus_insights}
BIAS INSIGHTS: {bias_insights}
UNCERTAINTY INSIGHTS: {uncertainty_insights}

SYNTHESIS FRAMEWORK:
1. Overall Validation Assessment
2. High-Confidence Findings
3. Areas of Uncertainty
4. Methodological Strengths and Limitations
5. Recommendations for Users

SYNTHESIS REQUIREMENTS:

OVERALL ASSESSMENT:
- What percentage of claims were successfully validated?
- What is the overall reliability of the research?
- Are there systematic issues or patterns in the validation results?
- How does the validation quality compare to professional standards?

HIGH-CONFIDENCE FINDINGS:
- Which claims have the strongest validation support?
- What makes these findings particularly reliable?
- What sources and methods support these conclusions?

AREAS OF UNCERTAINTY:
- Which claims require additional verification?
- What are the main sources of uncertainty?
- Where are knowledge gaps most significant?
- What claims should be treated with caution?

METHODOLOGICAL EVALUATION:
- How robust was the validation methodology?
- What were the main limitations in the validation process?
- What additional validation steps would strengthen the assessment?

USER RECOMMENDATIONS:
- How should users interpret and apply these research findings?
- What caveats should accompany the research results?
- What additional verification should users consider?
- How should uncertainty be communicated to different audiences?

CONFIDENCE SCORING:
Provide confidence scores (0-1) for:
- Overall research reliability
- Individual domain reliability
- Temporal validity
- Source quality
- Methodological rigor

OUTPUT REQUIREMENTS:
- Clear, actionable synthesis
- Specific examples where relevant
- Balanced assessment of strengths and limitations
- Practical guidance for research users
- Professional, objective tone
"""

    def _get_executive_template(self) -> str:
        return """
You are an executive communications specialist creating a high-level summary for C-suite executives and decision-makers.

MAIN THEMES: {main_themes}
KEY ENTITIES: {key_entities}
RESEARCH SCOPE: {research_scope} findings analyzed

EXECUTIVE SUMMARY REQUIREMENTS:
- 2-3 sentences maximum
- Focus on strategic implications and business impact
- Include key quantifiable insights
- Highlight actionable opportunities or threats
- Use confident, decisive language appropriate for executives

FRAMEWORK:
1. Core Finding: What is the single most important insight?
2. Business Implication: Why does this matter strategically?
3. Action Orientation: What should leaders consider doing?

TONE AND STYLE:
- Direct and confident
- Results-oriented
- Strategic perspective
- Minimal technical jargon
- Maximum impact per word

Example structure: "[Key insight with quantified impact]. [Strategic implication for business/industry]. [Recommended strategic consideration or opportunity]."

Create an executive summary that a CEO could confidently reference in a board meeting.
"""