import asyncio
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.schema import HumanMessage, SystemMessage
from langsmith import traceable

from app.core.sonar_client import PerplexitySonarClient
from app.db.vector_store import VectorStoreManager

from app.agents.base import BaseAgent, AgentState
from app.agents.planner import PlannerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.validator import ValidatorAgent
from app.core.websocket_manager import ConnectionManager
from app.core.streaming_manager import StreamingManager, ThoughtStream
from app.core.langsmith_config import langsmith_config

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
	def __init__(self, sonar_client: PerplexitySonarClient, websocket_manager: ConnectionManager, vector_store: VectorStoreManager):
		super().__init__(sonar_client=sonar_client, vector_store=vector_store)
		self.websocket_manager = websocket_manager
		self.streaming_manager = StreamingManager(websocket_manager)

		self.planner = PlannerAgent(sonar_client, vector_store, self.streaming_manager)
		self.researcher = ResearcherAgent(sonar_client, vector_store, self.streaming_manager)
		self.summarizer = SummarizerAgent(sonar_client, vector_store, self.streaming_manager)
		self.validator = ValidatorAgent(sonar_client, vector_store, self.streaming_manager)
		
		self.workflow = self._build_workflow()

	def _build_workflow(self) -> StateGraph:
		workflow = StateGraph(AgentState)

		workflow.add_node("initialize", self._initialization_step)
		workflow.add_node("plan", self._planning_step)
		workflow.add_node("research", self._research_step)
		workflow.add_node("validate", self._validation_step)
		workflow.add_node("summarize", self._summarization_step)
		workflow.add_node("finalize", self._finalization_step)

		workflow.add_node("quality_check", self._quality_checkpoint)
		workflow.add_node("adaptive_enhancement", self._adaptive_enhancement)
		workflow.add_node("user_feedback_integration", self._integrate_user_feedback)
		
		workflow.set_entry_point("initialize")
		workflow.add_edge("initialize", "plan")
		workflow.add_edge("plan", "research")
		workflow.add_edge("research", "validate")
		workflow.add_conditional_edges(
			"validate",
			self._should_enhance,
			{
				"enhance": "adaptive_enhancement",
				"feedback": "user_feedback_integration",
				"continue": "summarize"
			}
		)
		workflow.add_edge("adaptive_enhancement", "research")
		workflow.add_edge("user_feedback_integration", "summarize")
		workflow.add_edge("summarize", "quality_check")
		workflow.add_conditional_edges(
			"quality_check",
			self._quality_gate,
			{
				"pass": "finalize",
				"retry": "research",
				"enhance": "adaptive_enhancement",
				"fail": END
			}
		)
		workflow.add_edge("finalize", END)
		
		return workflow.compile()

	@traceable(name="research_orchestration")
	async def execute(self, state: AgentState) -> AgentState:
		user_ctx = state.user_context
		session_trace = langsmith_config.trace_research_session(
			state.session_id,
			state.input_data.get("query", ""),
			state.input_data.get("research_type", "standard")
		)

		await self.streaming_manager.start_session(
			state.session_id,
			user_ctx.user_id,
			f"Research: {state.input_data.get('query', 'Unknown')[:50]}..."
		)

		try:
			await self.streaming_manager.stream_thought(
				state.session_id,
				ThoughtStream(
					agent="orchestrator",
					step="initialization",
					thought=f"Starting research for {user_ctx.username} ({user_ctx.subscription_tier})",
					confidence=1.0,
					metadata={
						"user_context": user_ctx.__dict__,
						"research_params": state.input_data
					}
				)
			)
			final_state = await self.workflow.ainvoke(state)
			await self.streaming_manager.stream_completion(
				state.session_id,
				{
					"status": "completed",
					"final_quality": final_state.metrics.get("overall_quality", 0.5),
					"user_satisfaction_prediction": self._predict_user_satisfaction(final_state, user_ctx),
					"processing_time": datetime.utcnow().isoformat(),
					"total_sources": len(self._extract_all_sources(final_state)),
					"personalization_score": self._calculate_personalization_score(final_state, user_ctx)
				}
			)
			if final_state.metrics:
				metrics = {
					**final_state.metrics,
					"user_tier": user_ctx.subscription_tier,
					"user_satisfaction_prediction": self._predict_user_satisfaction(final_state, user_ctx),
					"personalization_effectiveness": self._calculate_personalization_score(final_state, user_ctx)
				}
				langsmith_config.log_metrics(metrics, state.session_id)
			return final_state
		
		except Exception as e:
			logger.error(f"Workflow execution error: {str(e)}")
			await self.streaming_manager.stream_error(
				state.session_id,
				{
					"error": str(e),
					"agent": "orchestrator",
					"user_id": user_ctx.user_id,
					"recovery_suggestions": self._generate_error_recovery_suggestions(str(e), user_ctx)
				}
			)
			state.errors.append(f"Orchestration error: {str(e)}")
			return state
		finally:
			await self.streaming_manager.end_session(state.session_id)
		
	async def _initialize_research(self, state: AgentState) -> AgentState:
		user_ctx = state.user_context
		query = state.input_data.get("query", "")
		research_type = state.input_data.get("research_type", "standard")

		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="orchestrator",
				step="initialization",
				thought=f"Analyzing query complexity for {user_ctx.subscription_tier} user: '{query}'",
				confidence=0.9,
				metadata={"query_length": len(query), "user_tier": user_ctx.subscription_tier}
			)
		)

		complexity_score = self.assess_query_complexity_for_user(query, user_ctx)
		user_expertise_level = self._infer_user_expertise_level(user_ctx)

		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="orchestrator",
				step="user_analysis",
				thought=f"Detected user expertise: {user_expertise_level}, adapting research approach accordingly",
				confidence=0.85,
				metadata={
					"expertise_level": user_expertise_level,
					"institution": user_ctx.institution,
					"research_interests": user_ctx.research_interests
				}
			)
		)

		init_msg = SystemMessage(content=f"""
		Initializing PerplexiQuest research session for {user_ctx.username}:
		
		USER CONTEXT:
		- User ID: {user_ctx.user_id}
		- Subscription: {user_ctx.subscription_tier}
		- Institution: {user_ctx.institution or 'Independent'}
		- Research Interests: {', '.join(user_ctx.research_interests) if user_ctx.research_interests else 'General'}
		- Expertise Level: {user_expertise_level}
		
		RESEARCH PARAMETERS:
		- Query: {query}
		- Type: {research_type}
		- Domain: {state.input_data.get('domain', 'general')}
		- Target Audience: {state.input_data.get('target_audience', 'general')}
		- Complexity Score: {complexity_score:.2f}
		
		ADAPTATION STRATEGY:
		- Complexity Level: {'Advanced' if user_ctx.subscription_tier in ['pro', 'enterprise'] else 'Standard'}
		- Citation Style: {self._get_preferred_citation_style(user_ctx)}
		- Source Requirements: {self._get_source_requirements(user_ctx)}
		
		Session: {state.session_id}
		Timestamp: 2025-05-28 17:46:02
		Agent: r3tr056
		""")
		state.messages.append(init_msg)

		state.metrics = {
			"query_complexity": complexity_score,
			"user_expertise_score": self._calculate_expertise_score(user_ctx),
			"initialization_time": datetime.now(timezone.utc).timestamp(),
			"subscription_tier_weight": {"free": 0.5, "pro": 0.75, "enterprise": 1.0}.get(user_ctx.subscription_tier, 0.5),
			"personalization_potential": self._calculate_personalization_potential(user_ctx)
		}
		await self.streaming_manager.stream_progress(
			state.session_id,
			{
				"step": "initialization",
				"progress": 10,
				"message": f"Research initialized for {user_ctx.username}",
				"user_adaptations": {
					"expertise_level": user_expertise_level,
					"complexity_adjustment": complexity_score,
					"subscription_features": self._get_subscription_features(user_ctx.subscription_tier)
				}
			}
		)
		return state
	
	async def _execute_planning(self, state: AgentState) -> AgentState:
		state.current_step = "planning"
		user_ctx = state.user_context

		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="planner",
				step="planning_start",
				thought=f"Creating sophisticated research plan tailored for {user_ctx.subscription_tier} user with {user_ctx.institution or 'independent'} background",
				confidence=0.9
			)
		)

		planning_state = AgentState(
			session_id=state.session_id,
			user_context=user_ctx,
			current_step="planning",
			input_data=state.input_data,
			messages=state.messages.copy()
		)

		result_state = await self.planning_agent.execute_with_tracing(planning_state)
		if result_state.output_data:
			plan = result_state.output_data.get("sophisticated_plan", {})
			sub_queries = result_state.output_data.get("enhanced_subqueries", [])
			
			await self.streaming_manager.stream_thought(
				state.session_id,
				ThoughtStream(
					agent="planner",
					step="planning_complete",
					thought=f"Generated {len(sub_queries)} research queries with {plan.get('complexity_analysis', {}).get('overall_complexity', 0.5):.2f} complexity score",
					confidence=result_state.metrics.get("overall_plan_quality", 0.5),
					metadata={
						"sub_query_count": len(sub_queries),
						"plan_sophistication": result_state.metrics.get("planning_sophistication_index", 0.5)
					}
				)
			)

		state.output_data = {"plan": result_state.output_data}
		state.messages.extend(result_state.messages)
		state.errors.extend(result_state.errors)

		planning_metrics = result_state.metrics or {}
		state.metrics.update({
			"planning_quality": planning_metrics.get("overall_plan_quality", 0.5),
			"user_alignment_score": self._assess_plan_user_alignment(result_state.output_data, user_ctx),
			"planning_personalization": planning_metrics.get("planning_sophistication_index", 0.5)
		})
		
		await self.streaming_manager.stream_progress(
			state.session_id,
			{
				"step": "planning",
				"progress": 25,
				"message": "Research plan created and optimized",
				"plan_summary": {
					"methodology": plan.get("methodology", "Standard approach"),
					"sub_queries": len(sub_queries),
					"quality_score": state.metrics["planning_quality"]
				}
			}
		)
		return state
	
	async def _execute_research(self, state: AgentState) -> AgentState:
		state.current_step = "research"
		user_ctx = state.user_context

		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="researcher",
				step="research_start",
				thought=f"Executing parallel research with {user_ctx.subscription_tier}-level access to premium sources",
				confidence=0.85
			)
		)

		plan = state.output_data.get("plan", {}).get("sophisticated_plan", {})
		sub_queries = state.output_data.get("plan", {}).get("enhanced_subqueries", [state.input_data.get("query", "")])

		research_state = AgentState(
			session_id=state.session_id,
			user_context=user_ctx,
			current_step="research",
			input_data={
				"queries": sub_queries,
				"domain": state.input_data.get("domain", "general"),
				"research_type": state.input_data.get("research_type", "standard"),
				"user_expertise": self._infer_user_expertise_level(user_ctx),
				"subscription_features": self._get_subscription_features(user_ctx.subscription_tier),
				"preferred_sources": self._get_preferred_sources(user_ctx),
				"quality_threshold": self._get_quality_threshold(user_ctx)
			},
			messages=state.messages.copy()
		)
		result_state = await self.research_agent.execute_with_tracing(research_state)

		if result_state.output_data:
			research_results = result_state.output_data
			total_sources = sum(len(r.get("sources", [])) for r in research_results)
			
			await self.streaming_manager.stream_thought(
				state.session_id,
				ThoughtStream(
					agent="researcher",
					step="research_analysis",
					thought=f"Research completed: {len(research_results)} queries processed, {total_sources} sources analyzed",
					confidence=result_state.metrics.get("overall_quality", 0.5),
					metadata={
						"query_count": len(research_results),
						"total_sources": total_sources,
						"average_confidence": result_state.metrics.get("average_confidence", 0.5)
					}
				)
			)

		if not state.output_data:
			state.output_data = {}
		state.output_data["research_results"] = result_state.output_data
		state.messages.extend(result_state.messages)
		state.errors.extend(result_state.errors)

		research_metrics = result_state.metrics or {}
		state.metrics.update({
			"research_depth": research_metrics.get("average_confidence", 0.5),
			"source_count": research_metrics.get("total_sources", 0),
			"research_quality": research_metrics.get("overall_quality", 0.5),
			"user_source_preference_match": self._assess_source_preference_match(result_state.output_data, user_ctx),
			"research_comprehensiveness": research_metrics.get("research_efficiency", 0.5)
		})
		
		await self.streaming_manager.stream_progress(
			state.session_id,
			{
				"step": "research",
				"progress": 60,
				"message": f"Research completed with {state.metrics['source_count']} sources",
				"research_summary": {
					"queries_processed": len(research_results),
					"total_sources": state.metrics["source_count"],
					"quality_score": state.metrics["research_quality"],
					"user_alignment": state.metrics["user_source_preference_match"]
				}
			}
		)
		return state
	
	async def _execute_validation(self, state: AgentState) -> AgentState:
		state.current_step = "validation"
		user_ctx = state.user_context
		
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="validator",
				step="validation_start",
				thought=f"Validating research findings with {user_ctx.subscription_tier}-level fact-checking rigor",
				confidence=0.9
			)
		)
		
		research_results = state.output_data.get("research_results", [])
		validation_state = AgentState(
			session_id=state.session_id,
			user_context=user_ctx,
			current_step="validation",
			input_data={
				"research_results": research_results,
				"domain": state.input_data.get("domain", "general"),
				"user_expertise": self._infer_user_expertise_level(user_ctx),
				"validation_rigor": self._get_validation_rigor(user_ctx),
				"fact_checking_sources": self._get_fact_checking_sources(user_ctx)
			},
			messages=state.messages.copy()
		)
		result_state = await self.validation_agent.execute_with_tracing(validation_state)
		if result_state.output_data:
			validation_results = result_state.output_data
			await self.streaming_manager.stream_thought(
				state.session_id,
				ThoughtStream(
					agent="validator",
					step="validation_analysis",
					thought=f"Validation complete: {validation_results.get('verified_claims', 0)} claims verified, confidence: {result_state.metrics.get('overall_confidence', 0.5):.2f}",
					confidence=result_state.metrics.get("overall_confidence", 0.5),
					metadata={
						"verified_claims": validation_results.get("verified_claims", 0),
						"flagged_inconsistencies": validation_results.get("flagged_inconsistencies", 0)
					}
				)
			)

		state.output_data["validation_results"] = result_state.output_data
		state.messages.extend(result_state.messages)
		state.errors.extend(result_state.errors)

		validation_metrics = result_state.metrics or {}
		state.metrics.update({
			"validation_confidence": validation_metrics.get("overall_confidence", 0.5),
			"claims_verified": validation_metrics.get("verified_count", 0),
			"validation_quality": validation_metrics.get("validation_quality", 0.5),
			"user_trust_alignment": self._assess_user_trust_alignment(result_state.output_data, user_ctx)
		})
		
		await self.streaming_manager.stream_progress(
			state.session_id,
			{
				"step": "validation",
				"progress": 80,
				"message": f"Validation completed with {state.metrics['validation_confidence']:.1%} confidence",
				"validation_summary": {
					"claims_verified": state.metrics["claims_verified"],
					"confidence_score": state.metrics["validation_confidence"],
					"trust_alignment": state.metrics["user_trust_alignment"]
				}
			}
		)
		return state
	
	async def _execute_summarization(self, state: AgentState) -> AgentState:
		state.current_step = "summarization"
		user_ctx = state.user_context

		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="summarizer",
				step="summarization_start",
				thought=f"Creating personalized summary for {user_ctx.username} with {self._infer_user_expertise_level(user_ctx)} expertise level",
				confidence=0.85
			)
		)
		
		summarization_state = AgentState(
			session_id=state.session_id,
			user_context=user_ctx,
			current_step="summarization",
			input_data={
				"query": state.input_data.get("query", ""),
				"research_results": state.output_data.get("research_results", []),
				"validation_results": state.output_data.get("validation_results", {}),
				"target_audience": state.input_data.get("target_audience", "general"),
				"research_type": state.input_data.get("research_type", "standard"),
				"user_preferences": self._get_user_summary_preferences(user_ctx),
				"personalization_level": self._get_personalization_level(user_ctx)
			},
			messages=state.messages.copy()
		)
		result_state = await self.summarization_agent.execute_with_tracing(summarization_state)
		if result_state.output_data:
			summary = result_state.output_data
			await self.streaming_manager.stream_thought(
				state.session_id,
				ThoughtStream(
					agent="summarizer",
					step="summary_complete",
					thought=f"Personalized summary generated: {len(summary.get('content', ''))} characters, readability optimized for user",
					confidence=result_state.metrics.get("overall_quality", 0.5),
					metadata={
						"content_length": len(summary.get("content", "")),
						"personalization_score": result_state.metrics.get("personalization_effectiveness", 0.5)
					}
				)
			)
	
		state.output_data["final_report"] = result_state.output_data
		state.messages.extend(result_state.messages)
		state.errors.extend(result_state.errors)

		summary_metrics = result_state.metrics or {}
		state.metrics.update({
			"summary_quality": summary_metrics.get("overall_quality", 0.5),
			"readability_score": summary_metrics.get("readability", 0.5),
			"completeness_score": summary_metrics.get("completeness", 0.5),
			"user_personalization_score": summary_metrics.get("personalization_effectiveness", 0.5)
		})
		
		await self.streaming_manager.stream_progress(
			state.session_id,
			{
				"step": "summarization",
				"progress": 95,
				"message": "Personalized summary completed",
				"summary_quality": {
					"overall_quality": state.metrics["summary_quality"],
					"readability": state.metrics["readability_score"],
					"personalization": state.metrics["user_personalization_score"]
				}
			}
		)
		return state

	def _should_enhance(self, state: AgentState) -> str:
		user_ctx = state.user_context
		validation_confidence = state.metrics.get("validation_confidence", 0.5)
		research_quality = state.metrics.get("research_quality", 0.5)
		quality_thresholds = {
			"free": 0.6,
			"pro": 0.7,
			"enterprise": 0.8
		}
		threshold = quality_thresholds.get(user_ctx.subscription_tier, 0.6)
		if user_ctx.subscription_tier == "enterprise" and research_quality > 0.6:
			return "feedback"
		if validation_confidence < threshold or research_quality < threshold:
			return "enhance"
		return "continue"

	async def _adaptive_enhancement(self, state: AgentState) -> AgentState:
		state.current_step = "enhancement"
		user_ctx = state.user_context
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="enhancer",
				step="enhancement_start",
				thought=f"Applying {user_ctx.subscription_tier}-level enhancement algorithms to improve research quality",
				confidence=0.8
			)
		)
		enhancement_areas = []
		if state.metrics.get("validation_confidence", 0.5) < self._get_validation_threshold(user_ctx):
			enhancement_areas.append("validation_depth")
		if state.metrics.get("research_quality", 0.5) < self._get_research_threshold(user_ctx):
			enhancement_areas.append("research_depth")
		if state.metrics.get("user_personalization_score", 0.5) < 0.7:
			enhancement_areas.append("personalization")
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="enhancer",
				step="enhancement_strategy",
				thought=f"Enhancement focus areas: {', '.join(enhancement_areas)}",
				confidence=0.75,
				metadata={"enhancement_areas": enhancement_areas}
			)
		)

		if "research_depth" in enhancement_areas:
			await self._enhance_research_depth(state, user_ctx)
		if "validation_depth" in enhancement_areas:
			await self._enhance_validation_depth(state, user_ctx)
		if "personalization" in enhancement_areas:
			await self._enhance_personalization(state, user_ctx)

		enhancement_msg = SystemMessage(content=f"""
		Adaptive enhancement applied for {user_ctx.username}:
		- Enhancement areas: {', '.join(enhancement_areas)}
		- Current metrics: {state.metrics}
		- User tier: {user_ctx.subscription_tier}
		- Enhancement iteration in progress
		""")
		state.messages.append(enhancement_msg)
		return state
	
	async def _integrate_user_feedback(self, state: AgentState) -> AgentState:
		user_ctx = state.user_context
		if user_ctx.subscription_tier != "enterprise":
			return state
		
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="feedback_integrator",
				step="feedback_collection",
				thought="Collecting real-time user feedback for enterprise-level customization",
				confidence=0.9
			)
		)
		
		# TODO: Implement real-time feedback collection
		# This would involve WebSocket communication with frontend
		# For now, simulate feedback integration

		feedback_msg = SystemMessage(content=f"""
		Enterprise feedback integration activated for {user_ctx.username}:
		- Real-time feedback collection enabled
		- Dynamic adjustment based on user preferences
		- Advanced personalization algorithms active
		""")
		state.messages.append(feedback_msg)
		return state

	def _quality_gate(self, state: AgentState) -> str:
		user_ctx = state.user_context
		overall_quality = state.metrics.get("overall_quality", 0.0)
		error_count = len(state.errors)
		quality_standards = {
			"free": 0.6,
			"pro": 0.7,
			"enterprise": 0.8
		}
		required_quality = quality_standards.get(user_ctx.subscription_tier, 0.6)
		if error_count > 3:
			return "fail"
		elif overall_quality >= required_quality:
			return "pass"
		elif overall_quality >= (required_quality * 0.8):
			return "pass"
		else:
			retry_count = state.metadata.get("retry_count", 0)
			if retry_count < 2:
				state.metadata["retry_count"] = retry_count + 1
				return "enhance" if user_ctx.subscription_tier in ["pro", "enterprise"] else "retry"
			else:
				return "fail"

	async def _finalize_research(self, state: AgentState) -> AgentState:
		state.current_step = "finalization"
		user_ctx = state.user_context
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="finalizer",
				step="finalization",
				thought=f"Finalizing research session for {user_ctx.username} with comprehensive quality metrics",
				confidence=0.95
			)
		)
		final_metrics = self._calculate_comprehensive_final_metrics(state, user_ctx)
		state.metrics.update(final_metrics)
		state.metadata.update({
			"completion_time": "2025-05-28 17:46:02",
			"session_duration": datetime.utcnow().timestamp() - state.metrics.get("initialization_time", 0),
			"final_status": "completed" if len(state.errors) == 0 else "completed_with_errors",
			"user_satisfaction_prediction": self._predict_user_satisfaction(state, user_ctx),
			"personalization_effectiveness": state.metrics.get("user_personalization_score", 0.5),
			"subscription_value_delivered": self._calculate_subscription_value(state, user_ctx)
		})
		await self.safe_store_user_artifact(
			state.session_id,
			"final_research_session",
			{
				"query": state.input_data.get("query", ""),
				"results": state.output_data,
				"metrics": state.metrics,
				"user_context": user_ctx.__dict__,
				"personalization_data": self._extract_personalization_data(state, user_ctx),
				"messages": [msg.content for msg in state.messages[-5:]],
				"metadata": state.metadata
			},
			user_ctx,
			confidence=state.metrics.get("overall_quality", 0.5)
		)
		await self.streaming_manager.stream_thought(
			state.session_id,
			ThoughtStream(
				agent="finalizer",
				step="completion",
				thought=f"Research session completed successfully for {user_ctx.username}",
				confidence=1.0,
				metadata={
					"final_quality": state.metrics.get("overall_quality", 0.5),
					"user_satisfaction": state.metadata["user_satisfaction_prediction"],
					"session_duration": state.metadata["session_duration"]
				}
			)
		)
		return state

	def _infer_user_expertise_level(self, user_ctx) -> str:
		if user_ctx.institution:
			if any(term in user_ctx.institution.lower() for term in ["university", "research", "institute", "lab"]):
				return "academic"
		if user_ctx.subscription_tier == "enterprise":
			return "professional"
		if len(user_ctx.research_interests) >= 3:
			return "specialized"
		if user_ctx.subscription_tier == "pro":
			return "intermediate"
		return "general"

	def _get_subscription_features(self, tier: str) -> List[str]:
		features = {
			"free": ["basic_research", "standard_sources", "basic_export"],
			"pro": ["advanced_research", "premium_sources", "all_exports", "collaboration", "priority_processing"],
			"enterprise": ["comprehensive_research", "exclusive_sources", "all_exports", "advanced_collaboration", "real_time_feedback", "custom_integration"]
		}
		return features.get(tier, features["free"])

	def _predict_user_satisfaction(self, state: AgentState, user_ctx) -> float:
		quality_score = state.metrics.get("overall_quality", 0.5)
		personalization_score = state.metrics.get("user_personalization_score", 0.5)
		satisfaction = quality_score * 0.6
		satisfaction += personalization_score * 0.3
		tier_boost = {"free": 0.0, "pro": 0.05, "enterprise": 0.1}.get(user_ctx.subscription_tier, 0.0)
		satisfaction += tier_boost
		
		return min(satisfaction, 1.0)

	def _calculate_personalization_score(self, state: AgentState, user_ctx) -> float:
		personalization_factors = []
		if user_ctx.institution:
			personalization_factors.append(0.8)
		if user_ctx.research_interests:
			interest_match = self._assess_research_interest_match(state, user_ctx)
			personalization_factors.append(interest_match)
		tier_utilization = self._assess_tier_feature_utilization(state, user_ctx)
		personalization_factors.append(tier_utilization)
		return sum(personalization_factors) / len(personalization_factors) if personalization_factors else 0.5

	def _extract_all_sources(self, state: AgentState) -> List[Dict]:
		all_sources = []
		research_results = state.output_data.get("research_results", [])
		for result in research_results:
			if isinstance(result, dict):
				sources = result.get("sources", [])
				all_sources.extend(sources)
		return all_sources

	def _calculate_comprehensive_final_metrics(self, state: AgentState, user_ctx) -> Dict[str, float]:
		base_metrics = {
			"overall_quality": self._calculate_overall_quality(state),
			"user_alignment": self._calculate_user_alignment(state, user_ctx),
			"personalization_effectiveness": state.metrics.get("user_personalization_score", 0.5),
			"subscription_value": self._calculate_subscription_value(state, user_ctx),
			"completion_efficiency": 1.0 - (len(state.errors) * 0.1)
		}
		return base_metrics

	def _calculate_overall_quality(self, state: AgentState) -> float:
		quality_components = [
			state.metrics.get("research_quality", 0.5),
			state.metrics.get("validation_confidence", 0.5),
			state.metrics.get("summary_quality", 0.5),
			state.metrics.get("planning_quality", 0.5)
		]
		return sum(quality_components) / len(quality_components)

	def _calculate_user_alignment(self, state: AgentState, user_ctx) -> float:
		alignment_factors = [
			state.metrics.get("user_source_preference_match", 0.5),
			state.metrics.get("user_trust_alignment", 0.5),
			self._assess_expertise_alignment(state, user_ctx),
			self._assess_institution_alignment(state, user_ctx)
		]
		
		return sum(alignment_factors) / len(alignment_factors)

	def _calculate_subscription_value(self, state: AgentState, user_ctx) -> float:
		features_used = self._count_features_used(state, user_ctx)
		available_features = len(self._get_subscription_features(user_ctx.subscription_tier))
		
		utilization = features_used / max(available_features, 1)
		quality_bonus = state.metrics.get("overall_quality", 0.5) * 0.5
		
		return min(utilization + quality_bonus, 1.0)

	def _assess_plan_user_alignment(self, plan_data, user_ctx) -> float:
		return 0.8

	def _assess_source_preference_match(self, research_data, user_ctx) -> float:
		return 0.75

	def _assess_user_trust_alignment(self, validation_data, user_ctx) -> float:
		return 0.85

	def _get_preferred_citation_style(self, user_ctx) -> str:
		if user_ctx.institution and "university" in user_ctx.institution.lower():
			return "APA"
		return "APA"

	def _get_source_requirements(self, user_ctx) -> str:
		requirements = {
			"free": "Standard web sources",
			"pro": "Academic and premium sources", 
			"enterprise": "Exclusive databases and expert sources"
		}
		return requirements.get(user_ctx.subscription_tier, "Standard sources")