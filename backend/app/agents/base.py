from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
import re

from langchain.schema import BaseMessage, SystemMessage, AIMessage
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferWindowMemory
from langsmith import traceable

from app.api.auth.user_context import UserContext
from app.core.sonar_client import PerplexitySonarClient
from app.db.vector_store import VectorStoreManager
from app.core.langsmith_config import langsmith_config

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
	session_id: str
	user_context: UserContext
	current_step: str
	input_data: Any
	output_data: Any = None
	errors: List[str] = field(default_factory=list)
	metadata: Dict[str, Any] = field(default_factory=dict)
	messages: List[BaseMessage] = field(default_factory=list)
	metrics: Dict[str, float] = field(default_factory=dict)
	timestamp: str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

	def __post_init__(self):
		self.metadata.update({
			"user_id": self.user_context.user_id,
			"username": self.user_context.username,
			"subscription_tier": self.user_context.subscription_tier,
			"auth_method": self.user_context.auth_method,
			"request_id": self.user_context.request_id
		})

class PerplexiQuestCallbackHandler(BaseCallbackHandler):
	def __init__(self, user_context: UserContext, agent_name: str):
		self.user_context = user_context
		self.agent_name = agent_name

	def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
		logger.info(f"[{self.agent_name}] User {self.user_context.username} - Chain started: {serialized.get('name', 'Unknown')}")
		if langsmith_config.client:
			langsmith_config.client.create_run(
				name=f"{self.agent_name}_chain_start",
				run_type="chain",
				inputs={"user_id": self.user_context.user_id, **inputs},
				extra={"user_context": self.user_context.__dict__}
			)

	def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
		logger.info(f"[{self.agent_name}] User {self.user_context.username} - Chain completed successfully")
		
	def on_chain_error(self, error: Exception, **kwargs) -> None:
		logger.error(f"[{self.agent_name}] User {self.user_context.username} - Chain error: {str(error)}")

class BaseAgent(ABC):

	def __init__(self, sonar_client: PerplexitySonarClient, vector_store: VectorStoreManager = None, current_user: str = None):
		self.sonar_client = sonar_client
		self.vector_store = vector_store
		self.current_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
		self.current_user = current_user

		self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)
		self.tracer = langsmith_config.get_tracer()

	def get_user_context(self) -> Optional[UserContext]:
		try:
			return self.user_context.get()
		except LookupError:
			return None
	
	def create_callback_handler(self, user_ctx: UserContext) -> PerplexiQuestCallbackHandler:
		return PerplexiQuestCallbackHandler(uesr_ctx, self.__class__.__name__)
	
	@traceable(name="agent_execution")
	async def execute_with_tracing(self, state: AgentState) -> AgentState:

		user_ctx = state.user_context
		try:
			system_msg = SystemMessage(content=f"""
			You are {self.__class__.__name__} executing for user {user_ctx.username}.
			User context:
			- User ID: {user_ctx.user_id}
			- Subscription: {user_ctx.subscription_tier}
			- Institution: {user_ctx.institution or 'Not specified'}
			- Research interests: {', '.join(user_ctx.research_interests) if user_ctx.research_interests else 'General'}
			- Timestamp: {self.current_timestamp}
			- Request ID: {user_ctx.request_id}
			
			Adapt your research approach to the user's background and subscription level.
			For {user_ctx.subscription_tier} users, provide {'advanced' if user_ctx.subscription_tier in ['pro', 'enterprise'] else 'standard'} features.
			""")
			state.messages.append(system_msg)
			if not await self._check_user_limits(user_ctx):
				state.errors.append("User has exceeded subscription limits")
				return state

			result = await self.execute(state)

			if langsmith_config.client:
				langsmith_config.trace_agent_execution(
					self.__class__.__name__,
					{
						"user_id": user_ctx.user_id,
						"input_data": str(state.input_data)[:500]
					},
					{
						"user_id": user_ctx.user_id,
						"output_data": str(result.output_data)[:500] if result.output_data else None
					}
				)
			await self._update_user_usage(user_ctx)
			return result
		except Exception as e:
			logger.error(f"Agent execution error: {str(e)}")
			state.errors.append(f"{self.__class__.__name__}: {str(e)}")
			error_msg = AIMessage(content=f"Error in {self.__class__.__name__}: {str(e)}")
			state.messages.append(error_msg)
			return state

	async def _check_user_limits(self, user_ctx: UserContext) -> bool:
		limits = {
			"free": {"daily_queries": 10, "concurrent_sessions": 1},
			"pro": {"daily_queries": 100, "concurrent_sessions": 5},
			"enterprise": {"daily_queries": 1000, "concurrent_sessions": 20}
		}
		user_limits = limits.get(user_ctx.subscription_tier, limits["free"])
		# TODO : Implement the usage checking via the TokenManager
		return True
	
	async def _update_user_usage(self, user_ctx: UserContext):
		# TODO: Implenent the user usage update via the TokenManager
		pass

	def create_user_personalized_prompt(self, base_prompt: str, user_ctx: UserContext) -> str:
		personalization = f"""
		User Profile Context:
		- Academic/Professional Level: {self._infer_user_level(user_ctx)}
		- Institution: {user_ctx.institution or 'Independent researcher'}
		- Research Focus: {', '.join(user_ctx.research_interests) if user_ctx.research_interests else 'General research'}
		- Subscription: {user_ctx.subscription_tier}
		
		Personalization Instructions:
		- Adapt complexity to user's {"advanced" if user_ctx.subscription_tier in ["pro", "enterprise"] else "standard"} level
		- Consider user's research background when explaining concepts
		- Use terminology appropriate for {"academic" if user_ctx.institution else "general"} audience
		{"- Provide advanced analysis and detailed citations for pro/enterprise users" if user_ctx.subscription_tier in ["pro", "enterprise"] else ""}
		
		Original Request:
		{base_prompt}
		"""
		return personalization
	
	def _infer_user_level(self, user_ctx: UserContext) -> str:
		if user_ctx.institution and any(term in user_ctx.institution.lower() for term in ["university", "college", "institute"]):
			return "academic"
		elif user_ctx.subscription_tier == "enterprise":
			return "professional"
		elif user_ctx.research_interests:
			return "specialized"
		else:
			return "general"

	def assess_query_complexity(self, query: str, user_ctx: UserContext) -> float:
		if not query:
			return 0.0
		words = query.split()
		base_complexity = min(
			len(words) / 20 * 0.3 +
			len([w for w in words if len(w) > 8]) / max(len(words), 1) * 0.4 +
			len([w for w in words if w.lower() in ["analyze", "compare", "evaluate", "why", "how"]]) / 10 * 0.3,
			1.0
		)
		user_level_multiplier = {
			"academic": 1.2,
            "professional": 1.1,
            "specialized": 1.0,
            "general": 0.8
		}
		user_level = self._infer_user_level(user_ctx)
		adjusted_complexity = base_complexity * user_level.get(user_level, 1.0)
		return min(adjusted_complexity, 1.0)

	def calculate_source_authority(self, sources: List[Dict[str, Any]]) -> float:
		if not sources:
			return 0.0
		authority_map = {
			".edu": 0.9, ".gov": 0.95, ".org": 0.7, "ieee.org": 0.95,
			"nature.com": 0.95, "science.org": 0.9, "pubmed": 0.9
		}
		total_score = 0.0
		for source in sources:
			url = source.get('url', '').lower()
			score = next((v for k, v in authority_map.items() if k in url), 0.5)
			total_score += score
		return total_score / len(sources)

	def assess_information_freshness(self, content: str) -> float:
		years = [int(y) for y in re.findall(r'\b(20[0-9]{2})\b', content)]
		if not years:
			return 0.5
		avg_year = sum(years) / len(years)
		return max(0.0, 1.0 - ((2025 - avg_year) / 10))

	def calculate_content_metrics(self, content: str, sources: List[Dict[str, Any]] = None) -> Dict[str, float]:
		if not content:
			return {"density": 0.0, "readability": 0.0, "factual_ratio": 0.0}
		words = content.split()
		sentences = content.count('.') + content.count('!') + content.count('?')
		# Information density
		numbers = len(re.findall(r'\d+', content))
		proper_nouns = len(re.findall(r'\b[A-Z][a-z]+\b', content))
		density = min((numbers + proper_nouns) / max(len(words), 1) * 2, 1.0)
		# Readability
		avg_sentence_length = len(words) / max(sentences, 1)
		readability = 0.8 if 10 <= avg_sentence_length <= 25 else 0.5
		# Factual content ratio
		factual_indicators = ['according to', 'study found', 'research shows', '%', 'million']
		factual_count = sum(1 for indicator in factual_indicators if indicator in content.lower())
		factual_ratio = min(factual_count / max(len(words) / 100, 1), 1.0)
		return {
			"density": density,
			"readability": readability,
			"factual_ratio": factual_ratio,
			"authority_score": self.calculate_source_authority(sources or []),
			"freshness": self.assess_information_freshness(content)
		}

	def extract_verifiable_claims(self, content: str, max_claims: int = 10) -> List[str]:
		claims = []
		sentences = content.split('.')
		claim_patterns = [
			r'\d+%', r'\$\d+', r'\d+\s*(million|billion)',
			'according to', 'study found', 'research shows'
		]
		for sentence in sentences:
			sentence = sentence.strip()
			if len(sentence) > 15 and any(
				re.search(pattern, sentence, re.IGNORECASE) if pattern.startswith('\\') 
				else pattern in sentence.lower() 
				for pattern in claim_patterns
			):
				claims.append(sentence)
		return claims[:max_claims]

	def parse_verification_status(self, content: str) -> str:
		content_lower = content.lower()
		status_map = [
			(["verified", "confirmed", "accurate"], "verified"),
			(["partially", "somewhat"], "partially_verified"),
			(["refuted", "false", "incorrect"], "refuted"),
			(["contradictory", "conflicting"], "contradictory"),
			(["insufficient", "unclear", "unknown"], "insufficient_evidence")
		]
		for indicators, status in status_map:
			if any(indicator in content_lower for indicator in indicators):
				return status
		return "insufficient_evidence"

	def combine_sources(self, *source_lists) -> List[Dict[str, Any]]:
		seen_urls = set()
		combined = []
		for source_list in source_lists:
			for source in source_list:
				url = source.get('url', '')
				if url and url not in seen_urls:
					combined.append(source)
					seen_urls.add(url)
		return combined

	def create_metadata(self, user_ctx: UserContext, **kwargs) -> Dict[str, Any]:
		return {
			"timestamp": self.current_timestamp,
			"created_by": self.current_user,
			"agent_class": self.__class__.__name__,
			"user_id": user_ctx.user_id,
            "username": user_ctx.username,
            "subscription_tier": user_ctx.subscription_tier,
            "auth_method": user_ctx.auth_method,
            "request_id": user_ctx.request_id,
			**kwargs
		}

	async def safe_store_artifact(self, session_id: str, artifact_type: str, content: Any, user_ctx: UserContext,  **kwargs):
		if not self.vector_store:
			logger.warning("Vector store not available for artifact storage")
			return
		try:
			await self.vector_store.store_research_artifact(
				session_id=session_id,
				artifact_type=artifact_type,
				content=content,
				source=self.__class__.__name__,
				user_id=user_ctx.user_id,
				metadata=self.create_metadata(user_ctx)
				**kwargs
			)
		except Exception as e:
			logger.error(f"Error storing artifact: {str(e)}")

	@abstractmethod
	async def execute(self, state: AgentState):
		pass