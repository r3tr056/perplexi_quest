from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from app.collab.session_manager import CollaborationSessionManager, CollaborationRole
from app.core.websocket_manager import ConnectionManager
from app.db.database import get_db_session

router = APIRouter(prefix="/api/v1/collab", tags=["collab"])


@router.post("/sessions")
async def create_collaborative_session(
    title: str,
    description: str,
    owner_id: str,
    initial_research_data: Optional[Dict[str, Any]] = None,
    db_session = Depends(get_db_session)
):
    session_manager = CollaborationSessionManager(ConnectionManager(), db_session)
    session_id = await session_manager.create_collaborative_session(title=title, description=description, owner_id=owner_id, initial_research_data=initial_research_data)
    return {
        "session_id": session_id,
        "title": title,
        "created_at": "2025-05-27 15:55:08",
        "created_by": "r3tr056"
    }

@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: str,
    username: str,
    role: CollaborationRole = CollaborationRole.VIEWER,
    db_session = Depends(get_db_session)
):
    session_manager = CollaborationSessionManager(ConnectionManager(), db_session)
    joined = await session_manager.join_session(
        session_id=session_id,
        user_id=user_id,
        username=username,
        websocket=websocket,
        role=role
    )
    
    if not joined:
        await websocket.close(code=4001, reason="Failed to join session")
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            if message_type == "edit":
                result = await session_manager.handle_real_time_edit(
                    session_id=session_id,
                    user_id=user_id,
                    section_id=message.get("section_id"),
                    edit_data=message.get("edit_data")
                )
                await websocket.send_text(json.dumps({
                    "type": "edit_result",
                    "result": result
                }))
                
            elif message_type == "comment":
                result = await session_manager.add_collaborative_comment(
                    session_id=session_id,
                    user_id=user_id,
                    section_id=message.get("section_id"),
                    comment_data=message.get("comment_data")
                )
                await websocket.send_text(json.dumps({
                    "type": "comment_result",
                    "result": result
                }))
                
            elif message_type == "sync_request":
                result = await session_manager.sync_research_state(session_id)
                await websocket.send_text(json.dumps({
                    "type": "sync_result",
                    "result": result
                }))  
    except WebSocketDisconnect:
        await session_manager.leave_session(session_id, user_id)

@router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    db_session = Depends(get_db_session)
):
    session_manager = CollaborationSessionManager(ConnectionManager(), db_session)
    analytics = await session_manager.get_session_analytics(session_id)
    return analytics

@router.post("/export")
async def export_research_data(
    research_data: Dict[str, Any],
    export_format: str,
    include_citations: bool = True,
    include_images: bool = True,
    include_metadata: bool = True,
    citation_style: str = "apa"
):
    from app.utils.export import ExportManager, ExportConfiguration, ExportFormat
    
    try:
        config = ExportConfiguration(
            format=ExportFormat(export_format),
            include_citations=include_citations,
            include_images=include_images,
            include_metadata=include_metadata,
            citation_style=citation_style
        )
        export_manager = ExportManager()
        result = await export_manager.export_research_data(research_data, config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/integrate")
async def integrate_with_service(
    research_data: Dict[str, Any],
    service: str,
    credentials: Dict[str, str],
    workspace_id: Optional[str] = None,
    custom_settings: Optional[Dict[str, Any]] = None
):
    from app.utils.export import ExportManager, IntegrationConfiguration, IntegrationService
    
    try:
        config = IntegrationConfiguration(
            service=IntegrationService(service),
            credentials=credentials,
            workspace_id=workspace_id,
            custom_settings=custom_settings or {}
        )
        export_manager = ExportManager()
        result = await export_manager.integrate_with_service(research_data, config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/citations/extract")
async def extract_citation_from_url(url: str):
    from app.utils.citation_manager import CitationManager
    citation_manager = CitationManager()
    citation = await citation_manager.extract_citations_from_url(url)
    return {
        "citation": citation.__dict__,
        "extracted_at": "2025-05-27 15:55:08",
        "extracted_by": "r3tr056"
    }

@router.post("/citations/validate")
async def validate_citation(citation_data: Dict[str, Any]):
    from app.utils.citation_manager import CitationManager, Citation, SourceType
    citation = Citation(
        citation_id=citation_data.get("citation_id", ""),
        title=citation_data.get("title", ""),
        authors=citation_data.get("authors", []),
        publication_date=citation_data.get("publication_date", ""),
        source_type=SourceType(citation_data.get("source_type", "website")),
        **{k: v for k, v in citation_data.items() if k not in ["citation_id", "title", "authors", "publication_date", "source_type"]}
    )
    citation_manager = CitationManager()
    validation_result = await citation_manager.validate_citation(citation)
    return validation_result.__dict__

@router.post("/citations/format")
async def format_citation(
    citation_data: Dict[str, Any],
    style: str
):

    from app.utils.citation_manager import CitationManager, Citation, SourceType, CitationStyle

    citation = Citation(
        citation_id=citation_data.get("citation_id", ""),
        title=citation_data.get("title", ""),
        authors=citation_data.get("authors", []),
        publication_date=citation_data.get("publication_date", ""),
        source_type=SourceType(citation_data.get("source_type", "website")),
        **{k: v for k, v in citation_data.items() if k not in ["citation_id", "title", "authors", "publication_date", "source_type"]}
    )
    citation_manager = CitationManager()
    formatted_citation = await citation_manager.format_citation(citation, CitationStyle(style))
    return {
        "formatted_citation": formatted_citation,
        "style": style,
        "formatted_at": "2025-05-27 15:55:08"
    }

@router.post("/plagiarism/check")
async def check_plagiarism(
    content: str,
    citations: List[Dict[str, Any]]
):
    from app.utils.citation_manager import CitationManager, Citation, SourceType

    citation_objects = []
    for citation_data in citations:
        citation = Citation(
            citation_id=citation_data.get("citation_id", ""),
            title=citation_data.get("title", ""),
            authors=citation_data.get("authors", []),
            publication_date=citation_data.get("publication_date", ""),
            source_type=SourceType(citation_data.get("source_type", "website")),
            **{k: v for k, v in citation_data.items() if k not in ["citation_id", "title", "authors", "publication_date", "source_type"]}
        )
        citation_objects.append(citation)
    citation_manager = CitationManager()
    plagiarism_result = await citation_manager.detect_plagiarism(content, citation_objects)
    return plagiarism_result