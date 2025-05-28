import asyncio
import weaviate
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta, timezone
import json
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Advanced vector database manager using Weaviate
    Handles semantic search, knowledge persistence, and research memory
    """

    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.initialize_client()

    def initialize_client(self):
        try:
            self.client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                additional_headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
            )
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            asyncio.create_task(self._create_schemas())
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    async def _create_schemas(self):
        """Create Weaviate schemas for different data types"""
        try:
            # Research Sessions schema
            research_session_schema = {
                "class": "ResearchSession",
                "description": "Research session data and metadata",
                "properties": [
                    {"name": "sessionId", "dataType": ["string"], "description": "Unique session identifier"},
                    {"name": "query", "dataType": ["text"], "description": "Original research query"},
                    {"name": "domain", "dataType": ["string"], "description": "Research domain/category"},
                    {"name": "timestamp", "dataType": ["date"], "description": "Session creation timestamp"},
                    {"name": "status", "dataType": ["string"], "description": "Session status"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional session metadata"}
                ],
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                }
            }

            # Research Artifacts schema
            research_artifact_schema = {
                "class": "ResearchArtifact",
                "description": "Individual research findings and artifacts",
                "properties": [
                    {"name": "sessionId", "dataType": ["string"], "description": "Associated session ID"},
                    {"name": "artifactType", "dataType": ["string"], "description": "Type of artifact (finding, source, analysis)"},
                    {"name": "content", "dataType": ["text"], "description": "Main content of the artifact"},
                    {"name": "source", "dataType": ["string"], "description": "Source URL or reference"},
                    {"name": "confidence", "dataType": ["number"], "description": "Confidence score 0-1"},
                    {"name": "domain", "dataType": ["string"], "description": "Research domain"},
                    {"name": "tags", "dataType": ["string[]"], "description": "Categorization tags"},
                    {"name": "timestamp", "dataType": ["date"], "description": "Artifact creation timestamp"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional artifact metadata"}
                ],
                "vectorizer": "text2vec-openai"
            }

            # Knowledge Base schema
            knowledge_base_schema = {
                "class": "KnowledgeBase",
                "description": "Persistent knowledge base for research insights",
                "properties": [
                    {"name": "topic", "dataType": ["string"], "description": "Main topic or subject"},
                    {"name": "concept", "dataType": ["text"], "description": "Concept or insight content"},
                    {"name": "evidence", "dataType": ["text"], "description": "Supporting evidence"},
                    {"name": "sources", "dataType": ["string[]"], "description": "Source references"},
                    {"name": "reliability", "dataType": ["number"], "description": "Reliability score 0-1"},
                    {"name": "lastUpdated", "dataType": ["date"], "description": "Last update timestamp"},
                    {"name": "updateCount", "dataType": ["int"], "description": "Number of updates"},
                    {"name": "domain", "dataType": ["string"], "description": "Knowledge domain"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"}
                ],
                "vectorizer": "text2vec-openai"
            }

            # Validation Records schema
            validation_record_schema = {
                "class": "ValidationRecord",
                "description": "Fact validation records and results",
                "properties": [
                    {"name": "claim", "dataType": ["text"], "description": "Original claim being validated"},
                    {"name": "validationStatus", "dataType": ["string"], "description": "Validation result status"},
                    {"name": "confidence", "dataType": ["number"], "description": "Validation confidence 0-1"},
                    {"name": "evidence", "dataType": ["text"], "description": "Validation evidence"},
                    {"name": "sources", "dataType": ["string[]"], "description": "Validation sources"},
                    {"name": "methodology", "dataType": ["string"], "description": "Validation methodology used"},
                    {"name": "timestamp", "dataType": ["date"], "description": "Validation timestamp"},
                    {"name": "domain", "dataType": ["string"], "description": "Subject domain"},
                    {"name": "metadata", "dataType": ["object"], "description": "Validation metadata"}
                ],
                "vectorizer": "text2vec-openai"
            }

            schemas = [
                research_session_schema,
                research_artifact_schema,
                knowledge_base_schema,
                validation_record_schema
            ]

            for schema in schemas:
                if not self.client.schema.exists(schema["class"]):
                    self.client.schema.create_class(schema)
                    logger.info(f"Created schema for {schema['class']}")

        except Exception as e:
            logger.error(f"Error creating schemas: {str(e)}")

    async def store_research_session(self, session_data: Dict[str, Any]) -> str:
        """Store research session data"""
        try:
            data_object = {
                "sessionId": session_data["session_id"],
                "query": session_data["query"],
                "domain": session_data.get("domain", "general"),
                "timestamp": datetime.utcnow().isoformat(),
                "status": session_data.get("status", "active"),
                "metadata": session_data.get("metadata", {})
            }
            result = self.client.data_object.create(
                data_object=data_object,
                class_name="ResearchSession"
            )
            logger.info(f"Stored research session: {session_data['session_id']}")
            return result
        except Exception as e:
            logger.error(f"Error storing research session: {str(e)}")
            raise

    async def store_research_artifact(
        self, 
        session_id: str, 
        artifact_type: str, 
        content: Any, 
        domain: str = "general",
        source: str = "",
        confidence: float = 0.5,
        tags: List[str] = None
    ) -> str:
        """Store individual research artifact"""
        try:
            data_object = {
                "sessionId": session_id,
                "artifactType": artifact_type,
                "content": json.dumps(content) if isinstance(content, (dict, list)) else str(content),
                "source": source,
                "confidence": confidence,
                "domain": domain,
                "tags": tags or [],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "contentType": type(content).__name__,
                    "contentLength": len(str(content))
                }
            }
            result = self.client.data_object.create(
                data_object=data_object,
                class_name="ResearchArtifact"
            )
            logger.info(f"Stored research artifact: {artifact_type} for session {session_id}")
            return result
        except Exception as e:
            logger.error(f"Error storing research artifact: {str(e)}")
            raise

    async def store_knowledge_base_entry(
        self,
        topic: str,
        concept: str,
        evidence: str,
        sources: List[str],
        reliability: float,
        domain: str = "general"
    ) -> str:
        """Store entry in persistent knowledge base"""
        try:
            existing = await self.search_knowledge_base(concept, limit=1, min_certainty=0.9)
            if existing and len(existing) > 0:
                return await self.update_knowledge_base_entry(existing[0]["id"], concept, evidence, sources, reliability)
            else:
                data_object = {
                    "topic": topic,
                    "concept": concept,
                    "evidence": evidence,
                    "sources": sources,
                    "reliability": reliability,
                    "lastUpdated": datetime.now(timezone.utc).isoformat(),
                    "updateCount": 1,
                    "domain": domain,
                    "metadata": {
                        "sourceCount": len(sources),
                        "conceptLength": len(concept),
                        "evidenceLength": len(evidence)
                    }
                }
                result = self.client.data_object.create(data_object=data_object, class_name="KnowledgeBase")
                logger.info(f"Stored knowledge base entry: {topic}")
                return result
        except Exception as e:
            logger.error(f"Error storing knowledge base entry: {str(e)}")
            raise

    async def store_validation_record(
        self,
        claim: str,
        validation_status: str,
        confidence: float,
        evidence: str,
        sources: List[str],
        methodology: str,
        domain: str = "general"
    ) -> str:
        """Store fact validation record"""
        try:
            data_object = {
                "claim": claim,
                "validationStatus": validation_status,
                "confidence": confidence,
                "evidence": evidence,
                "sources": sources,
                "methodology": methodology,
                "timestamp": datetime.utcnow().isoformat(),
                "domain": domain,
                "metadata": {
                    "claimLength": len(claim),
                    "evidenceLength": len(evidence),
                    "sourceCount": len(sources),
                    "validationDate": "2025-05-26 13:31:43"
                }
            }
            result = self.client.data_object.create(data_object=data_object, class_name="ValidationRecord")
            logger.info(f"Stored validation record for claim: {claim[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Error storing validation record: {str(e)}")
            raise

    async def semantic_search_research_artifacts(
        self,
        query: str,
        session_id: Optional[str] = None,
        artifact_type: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 10,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Semantic search across research artifacts"""
        try:
            where_filter = {}
            if session_id:
                where_filter["sessionId"] = {"equal": session_id}
            if artifact_type:
                where_filter["artifactType"] = {"equal": artifact_type}
            if domain:
                where_filter["domain"] = {"equal": domain}

            query_builder = (
                self.client.query
                .get("ResearchArtifact", [
                    "sessionId", "artifactType", "content", "source", 
                    "confidence", "domain", "tags", "timestamp", "metadata"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )

            if where_filter:
                query_builder = query_builder.with_where(where_filter)
            result = query_builder.do()
            artifacts = []
            for item in result["data"]["Get"]["ResearchArtifact"]:
                if item["_additional"]["certainty"] >= min_certainty:
                    artifacts.append({
                        "id": item.get("id"),
                        "session_id": item["sessionId"],
                        "artifact_type": item["artifactType"],
                        "content": item["content"],
                        "source": item["source"],
                        "confidence": item["confidence"],
                        "domain": item["domain"],
                        "tags": item["tags"],
                        "timestamp": item["timestamp"],
                        "metadata": item["metadata"],
                        "semantic_similarity": item["_additional"]["certainty"],
                        "vector_distance": item["_additional"]["distance"]
                    })
            logger.info(f"Found {len(artifacts)} artifacts for query: {query}")
            return artifacts
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    async def search_knowledge_base(
        self,
        query: str,
        domain: Optional[str] = None,
        min_reliability: float = 0.5,
        limit: int = 5,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search persistent knowledge base"""
        try:
            where_filter = {"reliability": {"greaterThan": min_reliability}}
            if domain:
                where_filter["domain"] = {"equal": domain}

            result = (
                self.client.query
                .get("KnowledgeBase", [
                    "topic", "concept", "evidence", "sources", "reliability",
                    "lastUpdated", "updateCount", "domain", "metadata"
                ])
                .with_near_text({"concepts": [query]})
                .with_where(where_filter)
                .with_limit(limit)
                .with_additional(["certainty"])
                .do()
            )

            knowledge_entries = []
            for item in result["data"]["Get"]["KnowledgeBase"]:
                if item["_additional"]["certainty"] >= min_certainty:
                    knowledge_entries.append({
                        "topic": item["topic"],
                        "concept": item["concept"],
                        "evidence": item["evidence"],
                        "sources": item["sources"],
                        "reliability": item["reliability"],
                        "last_updated": item["lastUpdated"],
                        "update_count": item["updateCount"],
                        "domain": item["domain"],
                        "metadata": item["metadata"],
                        "semantic_similarity": item["_additional"]["certainty"]
                    })
            return knowledge_entries
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []

    async def find_similar_research_sessions(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 5,
        min_certainty: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find similar past research sessions"""
        try:
            where_filter = {}
            if domain:
                where_filter["domain"] = {"equal": domain}
            result = (
                self.client.query
                .get("ResearchSession", [
                    "sessionId", "query", "domain", "timestamp", "status", "metadata"
                ])
                .with_near_text({"concepts": [query]})
                .with_where(where_filter)
                .with_limit(limit)
                .with_additional(["certainty"])
                .do()
            )

            similar_sessions = []
            for item in result["data"]["Get"]["ResearchSession"]:
                if item["_additional"]["certainty"] >= min_certainty:
                    similar_sessions.append({
                        "session_id": item["sessionId"],
                        "query": item["query"],
                        "domain": item["domain"],
                        "timestamp": item["timestamp"],
                        "status": item["status"],
                        "metadata": item["metadata"],
                        "similarity_score": item["_additional"]["certainty"]
                    })
            return similar_sessions
        except Exception as e:
            logger.error(f"Error finding similar sessions: {str(e)}")
            return []

    async def get_validation_history(
        self,
        claim: str,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get validation history for similar claims"""
        try:
            where_filter = {}
            if domain:
                where_filter["domain"] = {"equal": domain}
            result = (
                self.client.query
                .get("ValidationRecord", [
                    "claim", "validationStatus", "confidence", "evidence",
                    "sources", "methodology", "timestamp", "domain", "metadata"
                ])
                .with_near_text({"concepts": [claim]})
                .with_where(where_filter)
                .with_limit(limit)
                .with_additional(["certainty"])
                .do()
            )
            validation_history = []
            for item in result["data"]["Get"]["ValidationRecord"]:
                validation_history.append({
                    "claim": item["claim"],
                    "validation_status": item["validationStatus"],
                    "confidence": item["confidence"],
                    "evidence": item["evidence"],
                    "sources": item["sources"],
                    "methodology": item["methodology"],
                    "timestamp": item["timestamp"],
                    "domain": item["domain"],
                    "metadata": item["metadata"],
                    "similarity_to_query": item["_additional"]["certainty"]
                })
            return validation_history
        except Exception as e:
            logger.error(f"Error getting validation history: {str(e)}")
            return []

    async def update_knowledge_base_entry(
        self,
        entry_id: str,
        concept: str,
        evidence: str,
        sources: List[str],
        reliability: float
    ) -> str:
        """Update existing knowledge base entry"""
        try:
            current_entry = self.client.data_object.get_by_id(entry_id, class_name="KnowledgeBase")
            updated_data = {
                "concept": concept,
                "evidence": evidence,
                "sources": list(set(current_entry["sources"] + sources)),
                "reliability": max(current_entry["reliability"], reliability),
                "lastUpdated": datetime.utcnow().isoformat(),
                "updateCount": current_entry["updateCount"] + 1,
                "metadata": {
                    **current_entry["metadata"],
                    "lastUpdateDate": "2025-05-26 13:31:43",
                    "evidenceUpdated": True
                }
            }
            self.client.data_object.update(
                data_object=updated_data,
                class_name="KnowledgeBase",
                uuid=entry_id
            )
            logger.info(f"Updated knowledge base entry: {entry_id}")
            return entry_id
        except Exception as e:
            logger.error(f"Error updating knowledge base entry: {str(e)}")
            raise

    async def cleanup_old_data(self, days_old: int = 30):
        try:
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
            where_filter = {
                "timestamp": {"lessThan": cutoff_date},
                "status": {"equal": "completed"}
            }
            logger.info(f"Cleanup initiated for data older than {days_old} days")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")