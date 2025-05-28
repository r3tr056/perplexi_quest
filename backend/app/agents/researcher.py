import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
from langchain.schema import HumanMessage, AIMessage
from langsmith import traceable

from app.core.sonar_client import PerplexitySonarClient, SonarResponse
from app.agents.base import BaseAgent, AgentState

logger = logging.getLogger(__name__)

@dataclass
class ResearchResult:
	query: str
	content: str
	sources: List[Dict[str, Any]]
	confidence_score: float
	quality_metrics: Dict[str, float]
	model_used: str
	processing_time: float


class ResearcherAgent(BaseAgent):
	def __init__(self, sonar_client: PerplexitySonarClient):
		self.sonar_client = sonar_client

	@traceable(name="research_execution")
	async def execute(self, state: AgentState) -> AgentState:
		try:
			queries = state.input_data.get("queries", [])
			domain = state.input_data.get("domain", "general")
			research_type = state.input_data.get("research_type", "standard")
			research_msg = HumanMessage(content=f"Executing research for {len(queries)} queries in {domain} domain")
			state.messages.append(research_msg)
			
			model_config = {
				"quick": ("sonar", 3, 2000),
				"standard": ("sonar-deep-research", 3, 3000),
				"deep": ("sonar-deep-research", 2, 4000),
				"comprehensive": ("sonar-deep-research", 2, 5000)
			}
			model, max_concurrent, max_tokens = model_config.get(research_type, model_config["standard"])
			research_results = await self._execute_parallel_research(
				queries, domain, model, max_concurrent, max_tokens
			)
			processed_results = self._process_research_results(research_results)
			state.output_data = processed_results
			state.metrics = self._calculate_research_metrics(research_results)
			completion_msg = AIMessage(content=f"Research completed: {len(research_results)} queries processed")
			state.messages.append(completion_msg)

			return state
		except Exception as e:
			logger.error(f"Research execution error: {str(e)}")
			state.errors.append(f"Research error: {str(e)}")
			return state

	async def _execute_parallel_research(self, queries: List[str], domain: str, model: str, max_concurrent: int, max_tokens: int) -> List[ResearchResult]:
		semaphore = asyncio.Semaphore(max_concurrent)

		async def research_single_query(query: str, index: int) -> ResearchResult:
			async with semaphore:
				start_time = asyncio.get_event_loop().time()
				try:
					response = await self.sonar_client.search(
						query=query,
						model=model,
						system_prompt=f"""You are researching {domain} domain. Provide comprehensive, authoritative analysis.
						Current timestamp: {self.current_timestamp}
						Focus on accuracy, recent information, and expert perspectives.""",
						max_tokens=max_tokens,
						temperature=0.2,
						return_images=True,
						return_related_questions=True,
						web_search_options={"search_context_size": "high"}
					)
					quality_metrics = self.calculate_content_metrics(response.content, response.sources)
					confidence = self._calculate_research_confidence(response, quality_metrics)
					processing_time = asyncio.get_event_loop().time() - start_time
					result = ResearchResult(
						query=query,
						content=response.content,
						sources=response.sources,
						confidence_score=confidence,
						quality_metrics=quality_metrics,
						model_used=model,
						processing_time=processing_time
					)
					await asyncio.sleep(0.6)
					return result
				except Exception as e:
					logger.error(f"Error researching query {index}: {str(e)}")
					return ResearchResult(
						query=query,
						content=f"Research error: {str(e)}",
						sources=[],
						confidence_score=0.0,
						quality_metrics={},
						model_used=model,
						processing_time=asyncio.get_event_loop().time() - start_time
					)
		tasks = [research_single_query(query, i) for i, query in enumerate(queries)]
		results = await asyncio.gather(*tasks)
		return [r for r in results if r is not None]
	
	def _calculate_research_confidence(self, response, quality_metrics: Dict[str, float]) -> float:

		base_confidence = 0.4
		base_confidence += quality_metrics.get("authority_score", 0.0) * 0.25
		base_confidence += quality_metrics.get("factual_ratio", 0.0) * 0.2
		base_confidence += quality_metrics.get("freshness", 0.0) * 0.15
		source_count = len(response.sources)
		source_bonus = min(source_count / 8, 1.0) * 0.15
		base_confidence += source_bonus
		content_length = len(response.content.split())
		depth_bonus = min(content_length / 1000, 1.0) * 0.1
		base_confidence += depth_bonus
		
		return min(1.0, max(0.1, base_confidence))

	def _process_research_results(self, results: List[ResearchResult]) -> List[Dict[str, Any]]:
		processed = []
		for i, result in enumerate(results):
			processed.append({
				"query": result.query,
				"index": i,
				"content": result.content,
				"sources": result.sources,
				"related_questions": [],
				"confidence_score": result.confidence_score,
				"quality_metrics": result.quality_metrics,
				"model_used": result.model_used,
				"processing_time": result.processing_time,
				"metadata": self.create_metadata(
					query_index=i,
					processing_time=result.processing_time
				)
			})
		return processed

	def _calculate_research_metrics(self, results: List[ResearchResult]) -> Dict[str, float]:
		if not results:
			return {"average_confidence": 0.0, "overall_quality": 0.0}
		confidences = [r.confidence_score for r in results]
		processing_times = [r.processing_time for r in results]
		total_sources = sum(len(r.sources) for r in results)
		unique_domains = set()
		
		for result in results:
			for source in result.sources:
				url = source.get("url", "")
				if url:
					try:
						from urllib.parse import urlparse
						domain = urlparse(url).netloc
						unique_domains.add(domain)
					except:
						continue
		quality_scores = []
		for result in results:
			if result.quality_metrics:
				avg_quality = sum(result.quality_metrics.values()) / len(result.quality_metrics)
				quality_scores.append(avg_quality)
		return {
			"average_confidence": sum(confidences) / len(confidences),
			"min_confidence": min(confidences),
			"max_confidence": max(confidences),
			"total_sources": total_sources,
			"unique_domains": len(unique_domains),
			"source_diversity": min(len(unique_domains) / 10, 1.0),
			"average_processing_time": sum(processing_times) / len(processing_times),
			"overall_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0.5,
			"successful_queries": len([r for r in results if r.confidence_score > 0.3]),
			"research_efficiency": len(results) / max(sum(processing_times), 1)
		}
