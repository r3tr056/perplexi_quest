import httpx
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from pydantic import BaseModel
import logging
import json
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MessageRole(str, Enum):
    USER = 'user'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'


class SonarMessage(BaseModel):
    role: MessageRole
    content: str

class SonarWebSearchOptions(BaseModel):
    search_context_size: str = "high"

class SonarResponseFormat(BaseModel):
    type: str = "json_object"

class SonarResponse(BaseModel):
    content: str
    sources: List[Dict[str, Any]] = []
    related_questions: List[str] = []
    images: List[Dict[str, Any]] = []
    search_query: str
    model_used: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None

class PerplexitySonarClient:
    
    # Available models : https://docs.perplexity.ai/models/model-cards
    MODELS = {
        "sonar-deep-research": {"context_length": 128000, "type": "chat_completion", "best_for": "comprehensive_research"},
        "sonar-reasoning-pro": {"context_length": 128000, "type": "chat_completion", "best_for": "complex_reasoning"},
        "sonar-reasoning": {"context_length": 128000, "type": "chat_completion", "best_for": "logical_analysis"},
        "sonar-pro": {"context_length": 200000, "type": "chat_completion", "best_for": "long_context_tasks"},
        "sonar": {"context_length": 128000, "type": "chat_completion", "best_for": "general_research"},
        "r1-1776": {"context_length": 128000, "type": "chat_completion", "best_for": "specialized_tasks"}
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PerplexiQuest/1.0.0"
        }

    async def search(
        self, 
        query: str,
        model: str = "sonar-deep-research",
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
        top_p: float = 0.9,
        top_k: int = 0,
        search_domain_filter: Optional[List[str]] = None,
        return_images: bool = False,
        return_related_questions: bool = True,
        search_recency_filter: Optional[str] = None,
        stream: bool = False,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 1.0,
        response_format: Optional[Dict[str, Any]] = None,
        web_search_options: Optional[Dict[str, str]] = None
    ) -> Union[SonarResponse, AsyncGenerator[str, None]]:
        """Search with perpelxity sonar API"""
        try:
            if model not in self.MODELS:
                logger.warning(f"Unknown model {model}, using sonar-deep-research")
                model = "sonar-deep-research"

            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": query
            })

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "return_images": return_images,
                "return_related_questions": return_related_questions
            }

            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            if top_k > 0:
                payload["top_k"] = top_k
                
            if search_domain_filter:
                payload["search_domain_filter"] = search_domain_filter
                
            if search_recency_filter:
                payload["search_recency_filter"] = search_recency_filter
                
            if response_format:
                payload["response_format"] = response_format
                
            if web_search_options:
                payload["web_search_options"] = web_search_options
            else:
                payload["web_search_options"] = {"search_context_size": "high"}

            logger.info(f"Searching with model {model}: {query[:100]}...")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"Sonar API error: {response.status_code} - {response.text}")
                    raise Exception(f"Sonar API error: {response.status_code}")

                data = response.json()
                if stream:
                    return self._handle_streaming_response(response)
                return self._parse_response(data, query, model)

        except Exception as e:
            logger.error(f"Error in Sonar search: {str(e)}")
            raise

    async def deep_research_search(
        self,
        query: str,
        context: Optional[str] = None,
        max_tokens: int = 4000,
        include_images: bool = True,
        recency_filter: str = "month"
    ) -> SonarResponse:
        """Deep research using sonar-deep-research model"""

        system_prompt = f"""You are an expert research analyst conducting comprehensive research. 
        Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        Provide thorough, well-sourced analysis with:
        1. Comprehensive background and context
        2. Current state analysis with recent developments
        3. Multiple perspectives and viewpoints
        4. Key evidence and supporting data
        5. Expert opinions and authoritative sources
        6. Implications and conclusions
        
        {f'Additional context: {context}' if context else ''}
        
        Ensure all information is current, accurate, and well-cited."""

        return await self.search(
            query=query,
            model="sonar-deep-research",
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            return_images=include_images,
            return_related_questions=True,
            search_recency_filter=recency_filter,
            web_search_options={"search_context_size": "high"}
        )

    async def reasoning_search(
        self,
        query: str,
        reasoning_type: str = "analytical",
        max_tokens: int = 3000
    ) -> SonarResponse:
        """Search and complex reasoning task"""

        model = "sonar-reasoning-pro" if reasoning_type == "complex" else "sonar-reasoning"
        
        system_prompt = f"""You are an expert reasoning analyst. Think step-by-step and provide:
        1. Clear problem analysis and breakdown
        2. Logical reasoning chain with each step explained
        3. Evidence evaluation and source assessment
        4. Alternative perspectives and counterarguments
        5. Confidence levels for each conclusion
        6. Limitations and assumptions in your reasoning
        
        Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        Use systematic reasoning to analyze: {query}"""

        return await self.search(
            query=query,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            web_search_options={"search_context_size": "high"}
        )

    async def fact_check_search(
        self,
        claim: str,
        verification_level: str = "strict",
        max_tokens: int = 2000
    ) -> SonarResponse:
        """Search for fact checking and source verification"""
        system_prompt = f"""You are a professional fact-checker. Verify this claim with extreme rigor:
        
        CLAIM: {claim}
        
        Provide:
        1. Verification status (VERIFIED/REFUTED/PARTIALLY_VERIFIED/INSUFFICIENT_EVIDENCE)
        2. Supporting evidence from authoritative sources
        3. Contradicting evidence if any exists
        4. Source credibility assessment
        5. Confidence level (0-100%)
        6. Important caveats or context
        7. Date relevance and temporal considerations
        
        Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
        Be thorough and cite specific, recent sources."""

        return await self.search(
            query=f"Fact-check and verify: {claim}",
            model="sonar-reasoning-pro",
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.1,
            search_recency_filter="month",
            web_search_options={"search_context_size": "high"}
        )

    async def multi_perspective_search(
        self,
        query: str,
        perspectives: List[str],
        max_tokens: int = 2500
    ) -> List[SonarResponse]:
        """Multiple expert perspective search"""
        results = []
        
        for perspective in perspectives:
            system_prompt = f"""You are a {perspective} expert providing analysis from your professional perspective.
            
            Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            Analyze this query specifically from your {perspective} viewpoint:
            - What unique insights does your expertise provide?
            - What factors are most critical from your perspective?
            - What opportunities and challenges do you identify?
            - What recommendations would you make?
            - What additional considerations should be explored?
            
            Focus on insights that other perspectives might miss."""

            try:
                response = await self.search(
                    query=query,
                    model="sonar-pro",
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=0.3,
                    web_search_options={"search_context_size": "high"}
                )
                results.append(response)
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in {perspective} perspective search: {str(e)}")
                continue
        
        return results

    async def search_with_domain_filter(
        self,
        query: str,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        model: str = "sonar",
        max_tokens: int = 2000
    ) -> SonarResponse:
        """Search with domain filtering for source control"""
        domain_filter = []
        
        if allowed_domains:
            domain_filter.extend(allowed_domains)
            
        if blocked_domains:
            domain_filter.extend([f"-{domain}" for domain in blocked_domains])

        return await self.search(
            query=query,
            model=model,
            max_tokens=max_tokens,
            search_domain_filter=domain_filter if domain_filter else None,
            web_search_options={"search_context_size": "high"}
        )

    async def structured_search(
        self,
        query: str,
        output_schema: Dict[str, Any],
        model: str = "sonar-reasoning",
        max_tokens: int = 2000
    ) -> SonarResponse:
        system_prompt = f"""Provide your response in the following JSON structure:
        {json.dumps(output_schema, indent=2)}
        
        Ensure all fields are populated with relevant, accurate information based on your research.
        Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"""

        return await self.search(
            query=query,
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            response_format={"type": "json_object"},
            web_search_options={"search_context_size": "high"}
        )

    async def batch_search(
        self,
        queries: List[str],
        model: str = "sonar",
        max_concurrent: int = 3
    ) -> List[SonarResponse]:
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_search(query: str) -> SonarResponse:
            async with semaphore:
                try:
                    result = await self.search(query, model=model)
                    await asyncio.sleep(0.5)
                    return result
                except Exception as e:
                    logger.error(f"Batch search error for query '{query}': {str(e)}")
                    return SonarResponse(
                        content=f"Error: {str(e)}",
                        sources=[],
                        search_query=query,
                        model_used=model
                    )
        
        tasks = [limited_search(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = []
        for result in results:
            if isinstance(result, SonarResponse):
                valid_results.append(result)
            else:
                logger.error(f"Batch search exception: {result}")
        
        return valid_results

    def _parse_response(self, data: Dict[str, Any], query: str, model: str) -> SonarResponse:
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]

            sources = data.get("citations", [])
            related_questions = data.get("related_questions", [])
            images = data.get("images", [])

            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")
            finish_reason = choice.get("finish_reason")

            return SonarResponse(
                content=content,
                sources=sources,
                related_questions=related_questions,
                images=images,
                search_query=query,
                model_used=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason
            )

        except KeyError as e:
            logger.error(f"Error parsing Sonar response: {str(e)}")
            logger.error(f"Response data: {data}")
            raise Exception(f"Invalid response format: {str(e)}")

    async def _handle_streaming_response(self, response: httpx.Response) -> AsyncGenerator[str, None]:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                chunk_data = line[6:]
                if chunk_data == "[DONE]":
                    break
                try:
                    chunk = json.loads(chunk_data)
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                except json.JSONDecodeError:
                    continue

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        return self.MODELS.get(model_name, {})

    def list_available_models(self) -> List[str]:
        return list(self.MODELS.keys())

    def recommend_model(self, task_type: str) -> str:
        recommendations = {
            "deep_research": "sonar-deep-research",
            "comprehensive_research": "sonar-deep-research", 
            "complex_reasoning": "sonar-reasoning-pro",
            "logical_analysis": "sonar-reasoning",
            "fact_checking": "sonar-reasoning-pro",
            "long_context": "sonar-pro",
            "general_research": "sonar",
            "quick_search": "sonar",
            "specialized_tasks": "r1-1776"
        }
        
        return recommendations.get(task_type, "sonar-deep-research")

    async def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": 0,
            "tokens_used": 0,
            "rate_limit_remaining": "unknown",
            "last_request": datetime.now(timezone.utc).isoformat()
        }