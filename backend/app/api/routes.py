from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime

from app.api.schemas import (
    ResearchRequest, 
    ResearchResponse, 
    ResearchStatus,
    ResearchSession
)
from app.agents.orchestrator import OrchestratorAgent
from app.core.sonar_client import PerplexitySonarClient
from app.core.websocket_manager import ConnectionManager
from app.core.config import settings
from app.db.models import ResearchSessionModel
from app.db.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/")

# Global instances
sonar_client = PerplexitySonarClient(settings.PERPLEXITY_API_KEY)
websocket_manager = ConnectionManager()
orchestrator = OrchestratorAgent(sonar_client, websocket_manager)

research_sessions: Dict[str, Any] = {}

@router.post("/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest, 
    background_tasks: BackgroundTasks,
    db_session = Depends(get_db_session)
):
    """
    Start a new research session
    """
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Create new research session
        session_id = f"research_{datetime.utcnow().timestamp()}"
        
        # Store session info
        session_data = {
            "session_id": session_id,
            "query": request.query,
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "settings": {
                "max_agents": request.max_agents or 5,
                "timeout": request.timeout or 300,
                "include_validation": request.include_validation or True
            }
        }
        
        research_sessions[session_id] = session_data
        
        # Save to database
        db_research = ResearchSessionModel(
            session_id=session_id,
            query=request.query,
            status="started",
            settings=session_data["settings"]
        )
        db_session.add(db_research)
        await db_session.commit()
        
        # Start research in background
        background_tasks.add_task(
            run_research_workflow, 
            session_id, 
            request.query,
            db_session
        )
        
        return ResearchResponse(
            session_id=session_id,
            status="started",
            message="Research session initiated successfully",
            websocket_url=f"/ws/research/{session_id}"
        )
        
    except Exception as e:
        logger.error(f"Error starting research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")

@router.get("/research/{session_id}", response_model=ResearchStatus)
async def get_research_status(session_id: str, db_session = Depends(get_db_session)):
    """
    Get the current status of a research session
    """
    try:
        # Check in-memory first
        if session_id in research_sessions:
            session_data = research_sessions[session_id]
            return ResearchStatus(
                session_id=session_id,
                status=session_data["status"],
                query=session_data["query"],
                created_at=session_data["created_at"],
                progress=session_data.get("progress", {}),
                results=session_data.get("results", {}),
                errors=session_data.get("errors", [])
            )
        
        # Check database
        db_research = await db_session.get(ResearchSessionModel, session_id)
        if not db_research:
            raise HTTPException(status_code=404, detail="Research session not found")
        
        return ResearchStatus(
            session_id=session_id,
            status=db_research.status,
            query=db_research.query,
            created_at=db_research.created_at.isoformat(),
            progress=db_research.progress or {},
            results=db_research.results or {},
            errors=db_research.errors or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting research status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get research status: {str(e)}")

@router.get("/research", response_model=List[ResearchSession])
async def list_research_sessions(
    limit: int = 20, 
    offset: int = 0,
    db_session = Depends(get_db_session)
):
    """
    List recent research sessions
    """
    try:
        # Get from database
        query = db_session.query(ResearchSessionModel).order_by(
            ResearchSessionModel.created_at.desc()
        ).offset(offset).limit(limit)
        
        sessions = await query.all()
        
        return [
            ResearchSession(
                session_id=session.session_id,
                query=session.query,
                status=session.status,
                created_at=session.created_at.isoformat(),
                completed_at=session.completed_at.isoformat() if session.completed_at else None
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Error listing research sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list research sessions: {str(e)}")

@router.delete("/research/{session_id}")
async def delete_research_session(session_id: str, db_session = Depends(get_db_session)):
    """
    Delete a research session
    """
    try:
        # Remove from in-memory storage
        if session_id in research_sessions:
            del research_sessions[session_id]
        
        # Remove from database
        db_research = await db_session.get(ResearchSessionModel, session_id)
        if db_research:
            await db_session.delete(db_research)
            await db_session.commit()
        
        return {"message": "Research session deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting research session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete research session: {str(e)}")

@router.post("/research/{session_id}/feedback")
async def submit_feedback(
    session_id: str, 
    feedback: Dict[str, Any],
    db_session = Depends(get_db_session)
):
    """
    Submit feedback for a research session
    """
    try:
        # Validate session exists
        if session_id not in research_sessions:
            db_research = await db_session.get(ResearchSessionModel, session_id)
            if not db_research:
                raise HTTPException(status_code=404, detail="Research session not found")
        
        # Store feedback (in production, save to database)
        feedback_data = {
            "session_id": session_id,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update session with feedback
        if session_id in research_sessions:
            if "feedback" not in research_sessions[session_id]:
                research_sessions[session_id]["feedback"] = []
            research_sessions[session_id]["feedback"].append(feedback_data)
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

async def run_research_workflow(session_id: str, query: str, db_session):
    """
    Background task to run the research workflow
    """
    try:
        # Update session status
        if session_id in research_sessions:
            research_sessions[session_id]["status"] = "running"
        
        # Run the research workflow
        result = await orchestrator.conduct_research(query, session_id)
        
        # Update session with results
        session_update = {
            "status": result.status,
            "results": {
                "final_report": result.final_report,
                "research_plan": result.research_plan,
                "research_results": result.research_results,
                "execution_time": (result.completed_at - result.created_at).total_seconds() if result.completed_at else None
            },
            "errors": result.errors,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None
        }
        
        if session_id in research_sessions:
            research_sessions[session_id].update(session_update)
        
        # Update database
        db_research = await db_session.get(ResearchSessionModel, session_id)
        if db_research:
            db_research.status = result.status
            db_research.results = session_update["results"]
            db_research.errors = result.errors
            db_research.completed_at = result.completed_at
            await db_session.commit()
        
    except Exception as e:
        logger.error(f"Research workflow error for session {session_id}: {str(e)}")
        
        # Update session with error
        error_update = {
            "status": "failed",
            "errors": [str(e)],
            "completed_at": datetime.utcnow().isoformat()
        }
        
        if session_id in research_sessions:
            research_sessions[session_id].update(error_update)
        
        # Update database
        try:
            db_research = await db_session.get(ResearchSessionModel, session_id)
            if db_research:
                db_research.status = "failed"
                db_research.errors = [str(e)]
                db_research.completed_at = datetime.utcnow()
                await db_session.commit()
        except Exception as db_error:
            logger.error(f"Failed to update database with error: {str(db_error)}")