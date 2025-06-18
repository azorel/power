"""
Reasoning API Router

FastAPI router for reasoning endpoints providing hybrid reasoning capabilities
with step-by-step thinking and adaptive response modes.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio

from core.reasoning import ReasoningEngine
from shared.interfaces.reasoning_provider import ReasoningProvider
from shared.models.reasoning_models import (
    ReasoningRequest,
    ReasoningResponse,
    ReasoningMode,
    ReasoningMetrics,
    ComplexityAnalysis
)
from adapters.claude_reasoning import ClaudeReasoningClient
# from core.web.dependencies import get_current_user


# Pydantic models for API
class ReasoningRequestAPI(BaseModel):
    """API model for reasoning requests."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="The reasoning prompt")
    mode: Optional[ReasoningMode] = Field(ReasoningMode.ADAPTIVE, description="Reasoning mode")
    max_steps: Optional[int] = Field(10, ge=1, le=20, description="Maximum reasoning steps")
    timeout: Optional[float] = Field(30.0, ge=1.0, le=300.0, description="Timeout in seconds")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Response temperature")
    include_confidence: Optional[bool] = Field(True, description="Include confidence scores")
    stream_steps: Optional[bool] = Field(False, description="Stream reasoning steps")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ReasoningResponseAPI(BaseModel):
    """API model for reasoning responses."""
    id: str
    request_id: str
    final_answer: str
    mode_used: ReasoningMode
    processing_time: float
    tokens_used: int
    complexity_score: float
    confidence: str
    success: bool
    error_message: Optional[str] = None
    thinking_chain: Optional[Dict[str, Any]] = None
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComplexityAnalysisAPI(BaseModel):
    """API model for complexity analysis."""
    prompt: str
    complexity_score: float
    recommended_mode: ReasoningMode
    reasoning_factors: List[str]
    estimated_time: float
    confidence: float


class ReasoningStepAPI(BaseModel):
    """API model for individual reasoning steps."""
    step_number: int
    step_type: str
    description: str
    content: str
    confidence: str
    timestamp: str


class ReasoningMetricsAPI(BaseModel):
    """API model for reasoning metrics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_processing_time: float
    mode_usage: Dict[str, int]
    total_tokens_used: int


# Create router
router = APIRouter(prefix="/reasoning", tags=["reasoning"])
logger = logging.getLogger(__name__)

# Global reasoning engine instance
_reasoning_engine: Optional[ReasoningEngine] = None


def get_current_user() -> Dict[str, Any]:
    """Mock current user for testing."""
    return {
        'user_id': 'test-user',
        'session_id': 'test-session'
    }


def get_reasoning_engine() -> ReasoningEngine:
    """Get or create reasoning engine instance."""
    global _reasoning_engine
    
    if _reasoning_engine is None:
        # Initialize with Claude reasoning provider
        claude_provider = ClaudeReasoningClient()
        _reasoning_engine = ReasoningEngine(claude_provider)
        logger.info("Reasoning engine initialized with Claude provider")
    
    return _reasoning_engine


@router.post("/reason", response_model=ReasoningResponseAPI)
async def reason(
    request: ReasoningRequestAPI,
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> ReasoningResponseAPI:
    """
    Process a reasoning request using hybrid reasoning modes.
    
    This endpoint supports multiple reasoning modes:
    - rapid: Quick responses with minimal processing
    - thoughtful: Detailed analysis with reasoning steps
    - chain_of_thought: Explicit step-by-step reasoning
    - step_by_step: Comprehensive methodical analysis
    - adaptive: Auto-selects best mode based on complexity
    """
    try:
        # Create reasoning request
        reasoning_request = ReasoningRequest(
            prompt=request.prompt,
            mode=request.mode,
            max_steps=request.max_steps,
            timeout=request.timeout,
            temperature=request.temperature,
            include_confidence=request.include_confidence,
            stream_steps=request.stream_steps,
            context=request.context or {}
        )
        
        # Add user context
        reasoning_request.context.update({
            'user_id': current_user.get('user_id'),
            'session_id': current_user.get('session_id', 'default')
        })
        
        # Process the request
        response = await reasoning_engine.process_request(reasoning_request)
        
        # Convert to API format
        return ReasoningResponseAPI(
            id=str(response.id),
            request_id=str(response.request_id),
            final_answer=response.get_final_answer(),
            mode_used=response.mode_used,
            processing_time=response.processing_time,
            tokens_used=response.tokens_used,
            complexity_score=response.complexity_score,
            confidence=response.get_confidence().value,
            success=response.success,
            error_message=response.error_message if not response.success else None,
            thinking_chain=response.thinking_chain.to_dict() if response.thinking_chain else None,
            provider=response.provider,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Reasoning request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")


@router.post("/rapid", response_model=str)
async def rapid_response(
    prompt: str = Field(..., min_length=1, max_length=1000),
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> str:
    """
    Get a rapid response with minimal processing time.
    
    Optimized for quick, direct answers to simple questions.
    """
    try:
        answer = await reasoning_engine.provider.rapid_response(prompt)
        return answer
        
    except Exception as e:
        logger.error(f"Rapid response failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rapid response failed: {str(e)}")


@router.post("/thoughtful")
async def thoughtful_response(
    prompt: str = Field(..., min_length=1, max_length=5000),
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> Dict[str, Any]:
    """
    Get a thoughtful response with detailed reasoning chain.
    
    Provides comprehensive analysis with explicit reasoning steps.
    """
    try:
        thinking_chain = await reasoning_engine.provider.thoughtful_response(prompt)
        return thinking_chain.to_dict()
        
    except Exception as e:
        logger.error(f"Thoughtful response failed: {e}")
        raise HTTPException(status_code=500, detail=f"Thoughtful response failed: {str(e)}")


@router.post("/stream")
async def stream_reasoning(
    request: ReasoningRequestAPI,
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
):
    """
    Stream reasoning steps as they are generated.
    
    Returns a server-sent events stream of reasoning steps.
    """
    try:
        async def generate_steps():
            """Generate SSE stream of reasoning steps."""
            # Create reasoning request
            reasoning_request = ReasoningRequest(
                prompt=request.prompt,
                mode=request.mode,
                max_steps=request.max_steps,
                timeout=request.timeout,
                temperature=request.temperature,
                stream_steps=True,
                context=request.context or {}
            )
            
            # Add user context
            reasoning_request.context.update({
                'user_id': current_user.get('user_id'),
                'session_id': current_user.get('session_id', 'default')
            })
            
            try:
                step_count = 0
                async for step in reasoning_engine.stream_reasoning(reasoning_request):
                    step_data = {
                        'step_number': step.step_number,
                        'step_type': step.step_type.value,
                        'description': step.description,
                        'content': step.content,
                        'confidence': step.confidence.value,
                        'timestamp': step.timestamp.isoformat()
                    }
                    
                    yield f"data: {json.dumps(step_data)}\n\n"
                    step_count += 1
                    
                    if step_count >= request.max_steps:
                        break
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete', 'total_steps': step_count})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = {'type': 'error', 'message': str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_steps(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stream setup failed: {str(e)}")


@router.post("/analyze-complexity", response_model=ComplexityAnalysisAPI)
async def analyze_complexity(
    prompt: str = Field(..., min_length=1, max_length=5000),
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> ComplexityAnalysisAPI:
    """
    Analyze prompt complexity to recommend optimal reasoning mode.
    
    Returns complexity score and recommended reasoning approach.
    """
    try:
        analysis_data = await reasoning_engine.provider.analyze_complexity(prompt)
        
        return ComplexityAnalysisAPI(
            prompt=prompt,
            complexity_score=analysis_data['complexity_score'],
            recommended_mode=ReasoningMode(analysis_data['recommended_mode']),
            reasoning_factors=analysis_data.get('reasoning_factors', []),
            estimated_time=analysis_data['reasoning_time_estimate'],
            confidence=analysis_data['confidence']
        )
        
    except Exception as e:
        logger.error(f"Complexity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Complexity analysis failed: {str(e)}")


@router.get("/modes", response_model=List[str])
async def get_supported_modes(
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> List[str]:
    """Get list of supported reasoning modes."""
    try:
        modes = reasoning_engine.provider.get_supported_modes()
        return [mode.value for mode in modes]
        
    except Exception as e:
        logger.error(f"Failed to get supported modes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get modes: {str(e)}")


@router.get("/metrics", response_model=ReasoningMetricsAPI)
async def get_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> ReasoningMetricsAPI:
    """Get reasoning metrics and statistics."""
    try:
        metrics = reasoning_engine.get_metrics()
        
        return ReasoningMetricsAPI(
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            success_rate=metrics.success_rate(),
            average_processing_time=metrics.average_processing_time,
            mode_usage=metrics.mode_usage,
            total_tokens_used=metrics.total_tokens_used
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/provider-info")
async def get_provider_info(
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> Dict[str, Any]:
    """Get information about the current reasoning provider."""
    try:
        return reasoning_engine.provider.get_provider_info()
        
    except Exception as e:
        logger.error(f"Failed to get provider info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


@router.get("/health")
async def health_check(
    reasoning_engine: ReasoningEngine = Depends(get_reasoning_engine)
) -> Dict[str, Any]:
    """Check reasoning system health."""
    try:
        is_healthy = await reasoning_engine.health_check()
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'provider': reasoning_engine.provider.get_provider_info()['name'],
            'timestamp': '2025-01-18T00:00:00Z'  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': '2025-01-18T00:00:00Z'
        }


@router.post("/feedback")
async def record_feedback(
    request_id: str,
    satisfaction_score: float = Field(..., ge=0.0, le=1.0),
    feedback_text: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, str]:
    """
    Record user feedback for a reasoning response.
    
    This helps improve future reasoning quality through learning.
    """
    try:
        def record_feedback_task():
            """Background task to record feedback."""
            logger.info(
                f"Feedback recorded for request {request_id}: "
                f"satisfaction={satisfaction_score}, text={feedback_text}"
            )
            # TODO: Implement feedback storage and learning system
        
        background_tasks.add_task(record_feedback_task)
        
        return {"status": "Feedback recorded successfully"}
        
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")