from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
from datetime import datetime, timezone

from app.api.auth.user_context import get_current_user, get_verified_user, require_research_scope, UserContext
from app.db.models import ResearchSession
from app.agents.orchestrator import OrchestratorAgent
from app.agents.base import AgentState, BaseAgent
from app.db.database import get_db_session
from app.core.websocket_manager import ConnectionManager
from app.utils.export import ExportManager, ExportConfiguration, ExportFormat

router = APIRouter(prefix="/api/v1/research", tags=["research"])

class ResearchRequest(BaseModel):
	query: str
	research_type: str = "standard"
	target_audience: str = "general" 
	domain: str = "general"
	title: Optional[str] = None
	collaborative: bool = False

class ResearchExportRequest(BaseModel):
	session_id: str
	format: str
	include_citations: bool = True
	include_images: bool = True
	include_metadata: bool = True
	citation_style: str = "apa"

class ResearchUpdateRequest(BaseModel):
	title: Optional[str] = None
	visibility: Optional[str] = None
	shared_with: Optional[List[str]] = None


@router.post("/sessions")
async def create_research_session(
	research_request: ResearchRequest,
	background_tasks: BackgroundTasks,
	current_user: UserContext = Depends(get_verified_user),
	db_session: AsyncSession = Depends(get_db_session)
):
	try:
		usage_check = await _check_user_research_limits(current_user, db_session)
		if not usage_check["allowed"]:
			raise HTTPException(
				status_code=status.HTTP_429_TOO_MANY_REQUESTS,
				detail=usage_check["message"]
			)
		session = ResearchSession(
			user_id=current_user.user_id,
			title=research_request.title or f"Research: {research_request.query[:50]}...",
			query=research_request.query,
			research_type=research_request.research_type,
			target_audience=research_request.target_audience,
			domain=research_request.domain,
			is_collaborative=research_request.collaborative,
			status="initializing"
		)
		
		db_session.add(session)
		await db_session.commit()
		background_tasks.add_task(
			_execute_research_session,
			session.session_id,
			research_request.dict(),
			current_user.__dict__
		)
		return {
			"success": True,
			"session_id": session.session_id,
			"title": session.title,
			"status": session.status,
			"research_type": research_request.research_type,
			"created_at": session.created_at.isoformat(),
			"estimated_completion": _estimate_completion_time(research_request.research_type),
			"user_id": current_user.user_id,
			"timestamp": "2025-05-28 17:20:15",
			"created_by": "r3tr056"
		}
	except HTTPException:
		raise
	except Exception as e:
		await db_session.rollback()
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to create research session: {str(e)}"
		)
	
@router.get("/sessions/{session_id}")
async def get_research_session(
    session_id: str,
    current_user: UserContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):  
    try:
        from sqlalchemy import select
        result = await db_session.execute(
            select(ResearchSession).where(ResearchSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found"
            )
        if not await _check_session_access(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this research session"
            )
        response_data = {
            "session_id": session.session_id,
            "title": session.title,
            "query": session.query,
            "research_type": session.research_type,
            "target_audience": session.target_audience,
            "domain": session.domain,
            "status": session.status,
            "progress": session.progress,
            "is_collaborative": session.is_collaborative,
            "visibility": session.visibility,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "user_id": session.user_id,
            "is_owner": session.user_id == current_user.user_id
        }

        if current_user.subscription_tier in ["pro", "enterprise"]:
            response_data.update({
                "research_plan": session.research_plan,
                "research_results": session.research_results,
                "validation_results": session.validation_results,
                "quality_metrics": session.quality_metrics
            })

        if session.final_report:
            response_data["final_report"] = session.final_report
        response_data.update({
            "timestamp": "2025-05-28 17:20:15",
            "accessed_by": current_user.username
        })
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research session: {str(e)}"
        )

@router.put("/sessions/{session_id}")
async def update_research_session(
    session_id: str,
    update_request: ResearchUpdateRequest,
    current_user: UserContext = Depends(get_verified_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    try:
        from sqlalchemy import select, update
        result = await db_session.execute(
            select(ResearchSession).where(
                ResearchSession.session_id == session_id,
                ResearchSession.user_id == current_user.user_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found or access denied"
            )
        
        update_data = {"updated_at": datetime.now(timezone.utc)}
        if update_request.title:
            update_data["title"] = update_request.title
        if update_request.visibility in ["private", "public", "shared"]:
            update_data["visibility"] = update_request.visibility
        if update_request.shared_with is not None:
            update_data["shared_with"] = update_request.shared_with
        
        await db_session.execute(
            update(ResearchSession).where(ResearchSession.session_id == session_id).values(**update_data)
        )
        await db_session.commit()
        return {
            "success": True,
            "session_id": session_id,
            "updated_fields": list(update_data.keys()),
            "timestamp": "2025-05-28 17:20:15",
            "updated_by": current_user.username
        }
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update research session: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_research_session(
    session_id: str,
    current_user: UserContext = Depends(get_verified_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    try:
        from sqlalchemy import select, delete

        result = await db_session.execute(
            select(ResearchSession).where(
                ResearchSession.session_id == session_id,
                ResearchSession.user_id == current_user.user_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found or access denied"
            )
        await db_session.execute(
            delete(ResearchSession).where(ResearchSession.session_id == session_id)
        )
        await db_session.commit()
        return {
            "success": True,
            "message": f"Research session '{session.title}' deleted successfully",
            "session_id": session_id,
            "timestamp": "2025-05-28 17:20:15",
            "deleted_by": current_user.username
        }
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete research session: {str(e)}"
        )

@router.post("/sessions/{session_id}/export")
async def export_research_session(
    session_id: str,
    export_request: ResearchExportRequest,
    current_user: UserContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    try:
        from sqlalchemy import select

        result = await db_session.execute(
            select(ResearchSession).where(ResearchSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found"
            )
        if not await _check_session_access(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this research session"
            )
        allowed_formats = {
            "free": ["json", "markdown"],
            "pro": ["json", "markdown", "pdf", "docx", "html"],
            "enterprise": ["json", "markdown", "pdf", "docx", "html", "latex", "bibtex", "csv"]
        }
        
        user_formats = allowed_formats.get(current_user.subscription_tier, allowed_formats["free"])
        if export_request.format not in user_formats:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Export format '{export_request.format}' not available for {current_user.subscription_tier} subscription"
            )

        research_data = {
            "session_id": session.session_id,
            "query": session.query,
            "research_type": session.research_type,
            "target_audience": session.target_audience,
            "domain": session.domain,
            "plan": session.research_plan,
            "research_results": session.research_results,
            "validation_results": session.validation_results,
            "final_report": session.final_report,
            "quality_metrics": session.quality_metrics,
            "created_at": session.created_at.isoformat(),
            "user_context": {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "institution": current_user.institution
            }
        }

        config = ExportConfiguration(
            format=ExportFormat(export_request.format),
            include_citations=export_request.include_citations,
            include_images=export_request.include_images,
            include_metadata=export_request.include_metadata,
            citation_style=export_request.citation_style
        )

        export_manager = ExportManager()
        export_result = await export_manager.export_research_data(research_data, config)
        if not export_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {export_result.get('error', 'Unknown error')}"
            )
        def generate():
            yield export_result["content"]
        return StreamingResponse(
            generate(),
            media_type=export_result["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={export_result['filename']}",
                "Content-Length": str(export_result["size"])
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/sessions/{session_id}/stream")
async def stream_research_progress(
    session_id: str,
    current_user: UserContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    try:
        from sqlalchemy import select

        result = await db_session.execute(
            select(ResearchSession).where(ResearchSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found"
            )
        if not await _check_session_access(session, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this research session"
            )
        
        async def generate_progress_stream():
            connection_manager = ConnectionManager()
            last_progress = 0
            
            while True:
                try:
                    result = await db_session.execute(
                        select(ResearchSession).where(ResearchSession.session_id == session_id)
                    )
                    updated_session = result.scalar_one_or_none()
                    
                    if not updated_session:
                        break

                    if updated_session.progress != last_progress:
                        progress_data = {
                            "session_id": session_id,
                            "progress": updated_session.progress,
                            "status": updated_session.status,
                            "timestamp": "2025-05-28 17:20:15",
                            "user_id": current_user.user_id
                        }
                        
                        yield f"data: {json.dumps(progress_data)}\n\n"
                        last_progress = updated_session.progress
                    
                    if updated_session.status in ["completed", "failed"]:
                        final_data = {
                            "session_id": session_id,
                            "status": updated_session.status,
                            "completed_at": updated_session.completed_at.isoformat() if updated_session.completed_at else None,
                            "final": True,
                            "timestamp": "2025-05-28 17:20:15"
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                    
                    await asyncio.sleep(2)
                except Exception as e:
                    error_data = {
                        "error": str(e),
                        "timestamp": "2025-05-28 17:20:15"
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                
        return StreamingResponse(
            generate_progress_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream progress: {str(e)}"
        )

@router.get("/templates")
async def get_research_templates(
    current_user: UserContext = Depends(get_current_user)
):
    base_templates = [
        {
            "template_id": "academic_paper",
            "name": "Academic Paper Research",
            "description": "Comprehensive research for academic writing",
            "research_type": "deep",
            "target_audience": "academic",
            "estimated_time": "15-25 minutes",
            "features": ["peer_reviewed_sources", "citation_management", "methodology_analysis"]
        },
        {
            "template_id": "market_analysis",
            "name": "Market Analysis",
            "description": "Business and market research",
            "research_type": "standard",
            "target_audience": "business",
            "estimated_time": "10-15 minutes",
            "features": ["industry_data", "competitor_analysis", "trend_identification"]
        },
        {
            "template_id": "quick_overview",
            "name": "Quick Overview",
            "description": "Fast general research",
            "research_type": "quick",
            "target_audience": "general",
            "estimated_time": "5-8 minutes",
            "features": ["basic_search", "summary_generation"]
        }
    ]
    
    pro_templates = [
        {
            "template_id": "comprehensive_analysis",
            "name": "Comprehensive Analysis",
            "description": "Deep multi-perspective analysis",
            "research_type": "comprehensive",
            "target_audience": "expert",
            "estimated_time": "25-40 minutes",
            "features": ["multi_source_validation", "expert_opinions", "trend_prediction", "risk_analysis"]
        },
        {
            "template_id": "competitive_intelligence",
            "name": "Competitive Intelligence",
            "description": "Strategic competitive analysis",
            "research_type": "deep",
            "target_audience": "business",
            "estimated_time": "20-30 minutes",
            "features": ["competitor_tracking", "market_positioning", "strategic_insights"]
        }
    ]
    
    enterprise_templates = [
        {
            "template_id": "regulatory_compliance",
            "name": "Regulatory Compliance Research",
            "description": "Legal and regulatory analysis",
            "research_type": "comprehensive",
            "target_audience": "legal",
            "estimated_time": "30-45 minutes",
            "features": ["legal_database_access", "compliance_tracking", "regulatory_updates"]
        },
        {
            "template_id": "strategic_planning",
            "name": "Strategic Planning Research",
            "description": "Executive-level strategic analysis",
            "research_type": "comprehensive",
            "target_audience": "executive",
            "estimated_time": "35-50 minutes",
            "features": ["scenario_planning", "strategic_recommendations", "executive_briefing"]
        }
    ]

    available_templates = base_templates.copy()
    if current_user.subscription_tier in ["pro", "enterprise"]:
        available_templates.extend(pro_templates)
    if current_user.subscription_tier == "enterprise":
        available_templates.extend(enterprise_templates)
    return {
        "templates": available_templates,
        "subscription_tier": current_user.subscription_tier,
        "total_templates": len(available_templates),
        "timestamp": "2025-05-28 17:20:15",
        "user_id": current_user.user_id
    }

async def _check_user_research_limits(user_ctx: UserContext, db_session: AsyncSession) -> Dict[str, Any]:
    try:
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        limits = {
            "free": {"daily": 5, "monthly": 20, "concurrent": 1},
            "pro": {"daily": 50, "monthly": 200, "concurrent": 5},
            "enterprise": {"daily": 200, "monthly": 1000, "concurrent": 20}
        }
        
        user_limits = limits.get(user_ctx.subscription_tier, limits["free"])

        today = datetime.now(timezone.utc).date()
        daily_count = await db_session.execute(
            select(func.count(ResearchSession.session_id)).where(
                ResearchSession.user_id == user_ctx.user_id,
                func.date(ResearchSession.created_at) == today
            )
        )
        daily_usage = daily_count.scalar()
        if daily_usage >= user_limits["daily"]:
            return {
                "allowed": False,
                "message": f"Daily limit of {user_limits['daily']} research sessions exceeded. Upgrade subscription for higher limits."
            }

        concurrent_count = await db_session.execute(
            select(func.count(ResearchSession.session_id)).where(
                ResearchSession.user_id == user_ctx.user_id,
                ResearchSession.status.in_(["initializing", "planning", "researching", "validating", "summarizing"])
            )
        )
        concurrent_usage = concurrent_count.scalar()
        if concurrent_usage >= user_limits["concurrent"]:
            return {
                "allowed": False,
                "message": f"Maximum {user_limits['concurrent']} concurrent research sessions allowed. Please wait for current sessions to complete."
            }
        return {
            "allowed": True,
            "remaining_daily": user_limits["daily"] - daily_usage,
            "remaining_concurrent": user_limits["concurrent"] - concurrent_usage
        }
    except Exception as e:
        return {"allowed": True, "error": str(e)}

async def _check_session_access(session: ResearchSession, user_ctx: UserContext) -> bool:
    if session.user_id == user_ctx.user_id:
        return True
    if session.visibility == "public":
        return True
    if session.visibility == "shared" and session.shared_with:
        return user_ctx.user_id in session.shared_with
    if user_ctx.is_superuser:
        return True
    return False

async def _execute_research_session(session_id: str, research_request: Dict[str, Any], user_context_dict: Dict[str, Any]):
    try:
        user_ctx = UserContext(**user_context_dict)
        state = AgentState(
            session_id=session_id,
            user_context=user_ctx,
            current_step="initialization",
            input_data=research_request
        )
        
        # Initialize orchestrator with user context
        # This would use the user-aware orchestrator implementation
        orchestrator = OrchestratorAgent(sonar_client, websocket_manager, vector_store)
        final_state = await orchestrator.execute_with_user_context(state)
        await asyncio.sleep(5)
        
        from app.db.database import async_session_factory
        async with async_session_factory() as db_session:
            from sqlalchemy import update
            
            await db_session.execute(
                update(ResearchSession).where(ResearchSession.session_id == session_id).values(
                    status="completed",
                    progress=100,
                    completed_at=datetime.utcnow(),
                    final_report={"content": f"Research completed for: {research_request['query']}"}
                )
            )
            await db_session.commit()
    except Exception as e:
        try:
            from app.db.database import async_session_factory
            async with async_session_factory() as db_session:
                from sqlalchemy import update
                
                await db_session.execute(
                    update(ResearchSession).where(ResearchSession.session_id == session_id).values(
                        status="failed",
                        progress=0
                    )
                )
                await db_session.commit()
        except:
            pass

def _estimate_completion_time(research_type: str) -> str:
    estimates = {
        "quick": "5-8 minutes",
        "standard": "10-15 minutes", 
        "deep": "15-25 minutes",
        "comprehensive": "25-40 minutes"
    }
    return estimates.get(research_type, "10-15 minutes")