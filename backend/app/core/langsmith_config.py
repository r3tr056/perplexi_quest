import os
from langsmith import Client, traceable
from langchain.callbacks import LangChainTracer
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LangSmithConfig:
    
    def __init__(self):
        self.api_key = os.getenv("LANGSMITH_API_KEY")
        self.project_name = os.getenv("LANGSMITH_PROJECT", "perplexi-quest")
        self.endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        if self.api_key:
            self.client = Client(
                api_url=self.endpoint,
                api_key=self.api_key
            )
            self.tracer = LangChainTracer(
                project_name=self.project_name,
                client=self.client
            )
            logger.info(f"LangSmith initialized for project: {self.project_name}")
        else:
            logger.warning("LangSmith API key not found - tracing disabled")
            self.client = None
            self.tracer = None

    def get_tracer(self):
        return self.tracer

    @traceable(name="perplexi_quest_research")
    def trace_research_session(self, session_id: str, query: str, research_type: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "query": query,
            "research_type": research_type,
            "timestamp": "2025-05-26 21:06:53",
            "user": "r3tr056"
        }

    @traceable(name="agent_execution")
    def trace_agent_execution(self, agent_name: str, input_data: Any, output_data: Any) -> Dict[str, Any]:
        return {
            "agent": agent_name,
            "input": str(input_data)[:500],
            "output": str(output_data)[:500],
            "timestamp": "2025-05-26 21:06:53"
        }

    def log_metrics(self, metrics: Dict[str, float], session_id: str):
        if self.client:
            try:
                self.client.create_feedback(
                    run_id=session_id,
                    key="quality_metrics",
                    score=metrics.get("overall_score", 0.0),
                    value=metrics
                )
            except Exception as e:
                logger.error(f"Failed to log metrics to LangSmith: {str(e)}")

langsmith_config = LangSmithConfig()