import asyncio
from typing import Dict, List, Any
import json
import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langsmith import traceable

from app.core.sonar_client import PerplexitySonarClient
from app.db.vector_store import VectorStoreManager
from app.agents.base import BaseAgent, AgentState

logger = logging.getLogger(__name__)

class ResearchPlan(BaseModel):
	methodology: str = Field(description="Research methodology approach")
	focus_areas: List[str] = Field(description="Key areas to investigate")
	sub_queries: List[str] = Field(description="Specific research queries")
	quality_standards: List[str] = Field(description="Quality and verification standards")
	estimated_duration: int = Field(description="Estimated completion time in minutes")
	complexity_score: float = Field(description="Plan complexity score 0-1")

class PlannerAgent(BaseAgent):
	def __init__(self, sonar_client: PerplexitySonarClient, vector_store: VectorStoreManager):
		super().__init__(sonar_client, vector_store)

		self.output_parser = PydanticOutputParser(pydantic_object=ResearchPlan)

		self.planning_template = ChatPromptTemplate.from_messages([
			SystemMessagePromptTemplate.from_template("""
			You are an expert research planning agent for PerplexiQuest.
			Current timestamp: {timestamp}
			User: {user}
			
			Create a comprehensive research plan with the following structure:
			{format_instructions}
			
			Consider:
			- Research complexity and scope
			- Optimal query decomposition
			- Quality assurance requirements
			- Efficient resource utilization
			"""),
			HumanMessagePromptTemplate.from_template("""
			Create a research plan for:
			Query: {query}
			Research Type: {research_type}
			Domain: {domain}
			Target Audience: {target_audience}
			
			Plan should be optimized for {research_type} research with focus on {domain} domain.
			""")
		])

	@traceable(name="planning_execution")
	async def execute(self, state: AgentState) -> AgentState:
		try:
			query = state.input_data.get("query", "")
			research_type = state.input_data.get("research_type", "")
			domain = state.input_data.get("domain", "general")
			target_audience = state.input_data.get("target_audience", "general")

			planning_msg = HumanMessage(content=f"Planning research for: {query}")
			state.messages.append(planning_msg)
			formatted_prompt = self.planning_template.format_messages(
				timestamp=self.current_timestamp,
				user=self.current_user,
				format_instructions=self.output_parser.get_format_instructions(),
				query=query,
				research_type=research_type,
				domain=domain,
				target_audience=target_audience
			)
			planning_query = "\n".join([msg.content for msg in formatted_prompt])
			response = await self.sonar_client.reasoning_search(
				query=planning_query,
				reasoning_type="complex",
				max_tokens=2000
			)

			try:
				research_plan = self.output_parser.parse(response.content)
			except Exception as e:
				logger.warning(f"Failed to parse structured output: {str(e)}")
				research_plan = self._create_fallback_plan(query, research_type, domain)

			state.output_data = {
				"plan": research_plan.model_dump(),
				"sub_queries": research_plan.sub_queries,
				"methodology": research_plan.methodology,
				"quality_standards": research_plan.quality_standards
			}
			state.metrics = {
				"plan_quality": self._assess_plan_quality(research_plan),
				"query_coverage": self._assess_query_coverage(research_plan.sub_queries, query),
				"complexity_score": research_plan.complexity_score,
				"planning_efficiency": 1.0
			}
			success_msg = AIMessage(content=f"Research plan created with {len(research_plan.sub_queries)} sub-queries")
			state.messages.append(success_msg)
			return state
		except Exception as e:
			logger.error(f"Planning execution error: {str(e)}")
			state.errors.append(f"Planning error: {str(e)}")
			state.output_data = {
				"plan": self._create_fallback_plan(
					state.input_data.get("query", ""), 
					state.input_data.get("research_type", "standard"),
					state.input_data.get("domain", "general")
				).dict()
			}
			return state

	def _assess_plan_quality(self, plan: ResearchPlan) -> float:
		quality_factors = {
			"query_count": min(len(plan.sub_queries) / 5, 1.0) * 0.3,
			"methodology_depth": 0.3 if len(plan.methodology) > 50 else 0.1,
			"focus_areas": min(len(plan.focus_areas) / 3, 1.0) * 0.2,
			"standards_defined": min(len(plan.quality_standards) / 2, 1.0) * 0.2
		}
		return sum(quality_factors.values())
	
	def _assess_query_coverage(self, sub_queries: List[str], original_query: str) -> float:
		if not sub_queries:
			return 0.0
		original_words = set(original_query.lower().split())
		covered_words = set()
		for query in sub_queries:
			query_words = set(query.lower().split())
			covered_words.update(query_words.intersection(original_words))
		return len(covered_words) / max(len(original_words), 1)

	def _create_fallback_plan(self, query: str, research_type: str, domain: str) -> ResearchPlan:
		query_counts = {"quick": 3, "standard": 5, "deep": 7, "comprehensive": 10}
		target_queries = query_counts.get(research_type, 5)
		fallback_queries = [
			f"What is {query}? Provide comprehensive background.",
			f"What are current developments in {query}?",
			f"What are the benefits and applications of {query}?",
			f"What challenges or limitations exist with {query}?",
			f"What do experts and authorities say about {query}?",
			f"What are future implications and trends for {query}?",
			f"How does {query} compare to alternatives?",
			f"What practical implementations exist for {query}?",
			f"What recent research has been conducted on {query}?",
			f"What are potential risks or concerns with {query}?"
		]
		
		return ResearchPlan(
			methodology=f"Comprehensive {research_type} research approach for {domain} domain",
			focus_areas=[domain, "current_state", "expert_perspectives", "implications"],
			sub_queries=fallback_queries[:target_queries],
			quality_standards=["authoritative_sources", "fact_verification", "expert_consensus"],
			estimated_duration={"quick": 5, "standard": 15, "deep": 25, "comprehensive": 40}.get(research_type, 15),
			complexity_score=self.assess_query_complexity(query)
		)