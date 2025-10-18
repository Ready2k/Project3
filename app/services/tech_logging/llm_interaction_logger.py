"""
LLM interaction logging service for tracking AI model interactions.

Provides comprehensive logging of LLM interactions including prompts, responses,
processing time, token usage, and quality metrics.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time
import hashlib

from .tech_stack_logger import TechStackLogger, LogCategory


@dataclass
class LLMRequest:
    """LLM request information."""

    request_id: str
    provider: str
    model: str
    prompt: str
    prompt_hash: str
    parameters: Dict[str, Any]
    timestamp: str
    context: Dict[str, Any]


@dataclass
class LLMResponse:
    """LLM response information."""

    response_id: str
    request_id: str
    response_text: str
    response_hash: str
    processing_time_ms: float
    token_usage: Optional[Dict[str, int]]
    quality_metrics: Optional[Dict[str, float]]
    metadata: Optional[Dict[str, Any]]
    timestamp: str


@dataclass
class LLMInteractionTrace:
    """Complete LLM interaction trace."""

    request: LLMRequest
    response: LLMResponse
    success: bool
    error_message: Optional[str]
    retry_count: int
    total_duration_ms: float


class LLMInteractionLogger:
    """
    Service for logging LLM interactions with comprehensive tracking.

    Provides detailed logging of all LLM interactions including performance
    metrics, quality assessment, and debugging information.
    """

    def __init__(self, tech_stack_logger: TechStackLogger):
        """
        Initialize LLM interaction logger.

        Args:
            tech_stack_logger: Main tech stack logger instance
        """
        self.logger = tech_stack_logger
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        self._interaction_history: List[LLMInteractionTrace] = []

    def start_llm_request(
        self,
        request_id: str,
        provider: str,
        model: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMRequest:
        """
        Start tracking an LLM request.

        Args:
            request_id: Unique request identifier
            provider: LLM provider name
            model: Model name
            prompt: Request prompt
            parameters: Model parameters
            context: Additional context

        Returns:
            LLM request object
        """
        # Create prompt hash for deduplication and caching
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        request = LLMRequest(
            request_id=request_id,
            provider=provider,
            model=model,
            prompt=prompt,
            prompt_hash=prompt_hash,
            parameters=parameters or {},
            timestamp=datetime.utcnow().isoformat(),
            context=context or {},
        )

        self._active_requests[request_id] = {
            "request": request,
            "start_time": time.time(),
            "retry_count": 0,
        }

        # Log request start (without full prompt for brevity)
        self.logger.log_info(
            LogCategory.LLM_INTERACTION,
            "LLMInteractionLogger",
            "start_request",
            f"Started LLM request to {provider}/{model}",
            {
                "request_id": request_id,
                "provider": provider,
                "model": model,
                "prompt_hash": prompt_hash,
                "prompt_length": len(prompt),
                "parameters": parameters,
                "context": context,
            },
        )

        return request

    def log_llm_response(
        self,
        request_id: str,
        response_text: str,
        token_usage: Optional[Dict[str, int]] = None,
        quality_metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Log LLM response.

        Args:
            request_id: Request identifier
            response_text: Response text
            token_usage: Token usage statistics
            quality_metrics: Response quality metrics
            metadata: Additional metadata

        Returns:
            LLM response object
        """
        if request_id not in self._active_requests:
            raise ValueError(f"No active request found with ID: {request_id}")

        request_data = self._active_requests[request_id]
        processing_time_ms = (time.time() - request_data["start_time"]) * 1000

        # Create response hash
        response_hash = hashlib.sha256(response_text.encode()).hexdigest()[:16]

        response = LLMResponse(
            response_id=f"{request_id}_response",
            request_id=request_id,
            response_text=response_text,
            response_hash=response_hash,
            processing_time_ms=processing_time_ms,
            token_usage=token_usage,
            quality_metrics=quality_metrics,
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Log response
        self.logger.log_info(
            LogCategory.LLM_INTERACTION,
            "LLMInteractionLogger",
            "receive_response",
            f"Received LLM response in {processing_time_ms:.2f}ms",
            {
                "request_id": request_id,
                "response_hash": response_hash,
                "response_length": len(response_text),
                "processing_time_ms": processing_time_ms,
                "token_usage": token_usage,
                "quality_metrics": quality_metrics,
                "metadata": metadata,
            },
        )

        return response

    def complete_llm_interaction(
        self,
        request_id: str,
        response: Optional[LLMResponse] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> LLMInteractionTrace:
        """
        Complete an LLM interaction and create trace.

        Args:
            request_id: Request identifier
            response: LLM response (if successful)
            success: Whether interaction was successful
            error_message: Error message (if failed)

        Returns:
            Complete interaction trace
        """
        if request_id not in self._active_requests:
            raise ValueError(f"No active request found with ID: {request_id}")

        request_data = self._active_requests.pop(request_id)
        total_duration_ms = (time.time() - request_data["start_time"]) * 1000

        trace = LLMInteractionTrace(
            request=request_data["request"],
            response=response,
            success=success,
            error_message=error_message,
            retry_count=request_data["retry_count"],
            total_duration_ms=total_duration_ms,
        )

        self._interaction_history.append(trace)

        # Log completion
        if success:
            self.logger.log_info(
                LogCategory.LLM_INTERACTION,
                "LLMInteractionLogger",
                "complete_interaction",
                "LLM interaction completed successfully",
                {
                    "request_id": request_id,
                    "total_duration_ms": total_duration_ms,
                    "retry_count": request_data["retry_count"],
                    "success": success,
                },
            )
        else:
            self.logger.log_error(
                LogCategory.LLM_INTERACTION,
                "LLMInteractionLogger",
                "complete_interaction",
                f"LLM interaction failed: {error_message}",
                {
                    "request_id": request_id,
                    "total_duration_ms": total_duration_ms,
                    "retry_count": request_data["retry_count"],
                    "success": success,
                    "error_message": error_message,
                },
            )

        return trace

    def log_retry_attempt(self, request_id: str, retry_reason: str) -> None:
        """
        Log retry attempt for an LLM request.

        Args:
            request_id: Request identifier
            retry_reason: Reason for retry
        """
        if request_id not in self._active_requests:
            raise ValueError(f"No active request found with ID: {request_id}")

        self._active_requests[request_id]["retry_count"] += 1
        retry_count = self._active_requests[request_id]["retry_count"]

        self.logger.log_warning(
            LogCategory.LLM_INTERACTION,
            "LLMInteractionLogger",
            "retry_attempt",
            f"Retrying LLM request (attempt {retry_count}): {retry_reason}",
            {
                "request_id": request_id,
                "retry_count": retry_count,
                "retry_reason": retry_reason,
            },
        )

    def log_prompt_engineering(
        self,
        component: str,
        operation: str,
        prompt_version: str,
        prompt_template: str,
        variables: Dict[str, Any],
        optimization_notes: Optional[str] = None,
    ) -> None:
        """
        Log prompt engineering details.

        Args:
            component: Component creating the prompt
            operation: Operation context
            prompt_version: Version of the prompt template
            prompt_template: Template used
            variables: Variables substituted in template
            optimization_notes: Notes about prompt optimization
        """
        self.logger.log_debug(
            LogCategory.LLM_INTERACTION,
            component,
            operation,
            f"Generated prompt using template {prompt_version}",
            {
                "prompt_version": prompt_version,
                "template_length": len(prompt_template),
                "variables": variables,
                "optimization_notes": optimization_notes,
            },
        )

    def log_response_parsing(
        self,
        component: str,
        operation: str,
        response_text: str,
        parsing_success: bool,
        parsed_data: Optional[Dict[str, Any]] = None,
        parsing_errors: Optional[List[str]] = None,
    ) -> None:
        """
        Log response parsing results.

        Args:
            component: Component parsing the response
            operation: Operation context
            response_text: Raw response text
            parsing_success: Whether parsing was successful
            parsed_data: Successfully parsed data
            parsing_errors: Parsing errors encountered
        """
        if parsing_success:
            self.logger.log_debug(
                LogCategory.LLM_INTERACTION,
                component,
                operation,
                "Successfully parsed LLM response",
                {
                    "response_length": len(response_text),
                    "parsed_data_keys": list(parsed_data.keys()) if parsed_data else [],
                    "parsing_success": parsing_success,
                },
            )
        else:
            self.logger.log_warning(
                LogCategory.LLM_INTERACTION,
                component,
                operation,
                f"Failed to parse LLM response: {parsing_errors}",
                {
                    "response_length": len(response_text),
                    "parsing_success": parsing_success,
                    "parsing_errors": parsing_errors,
                    "response_preview": (
                        response_text[:200] + "..."
                        if len(response_text) > 200
                        else response_text
                    ),
                },
            )

    def log_quality_assessment(
        self,
        component: str,
        operation: str,
        response_text: str,
        quality_metrics: Dict[str, float],
        quality_threshold: float,
        passes_quality: bool,
        improvement_suggestions: Optional[List[str]] = None,
    ) -> None:
        """
        Log response quality assessment.

        Args:
            component: Component assessing quality
            operation: Operation context
            response_text: Response being assessed
            quality_metrics: Quality metric scores
            quality_threshold: Minimum quality threshold
            passes_quality: Whether response meets quality standards
            improvement_suggestions: Suggestions for improvement
        """
        overall_quality = (
            sum(quality_metrics.values()) / len(quality_metrics)
            if quality_metrics
            else 0.0
        )

        self.logger.log_info(
            LogCategory.LLM_INTERACTION,
            component,
            operation,
            f"Quality assessment: {'PASS' if passes_quality else 'FAIL'} (score: {overall_quality:.3f})",
            {
                "quality_metrics": quality_metrics,
                "overall_quality": overall_quality,
                "quality_threshold": quality_threshold,
                "passes_quality": passes_quality,
                "improvement_suggestions": improvement_suggestions,
                "response_length": len(response_text),
            },
            confidence_score=overall_quality,
        )

    def get_interaction_summary(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        time_window_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get summary of LLM interactions.

        Args:
            provider: Filter by provider
            model: Filter by model
            time_window_hours: Filter by time window

        Returns:
            Interaction summary statistics
        """
        interactions = self._interaction_history

        # Apply filters
        if provider:
            interactions = [i for i in interactions if i.request.provider == provider]
        if model:
            interactions = [i for i in interactions if i.request.model == model]
        if time_window_hours:
            cutoff_time = datetime.utcnow().timestamp() - (time_window_hours * 3600)
            interactions = [
                i
                for i in interactions
                if datetime.fromisoformat(i.request.timestamp).timestamp() > cutoff_time
            ]

        if not interactions:
            return {}

        # Calculate statistics
        total_interactions = len(interactions)
        successful_interactions = len([i for i in interactions if i.success])
        failed_interactions = total_interactions - successful_interactions

        durations = [i.total_duration_ms for i in interactions]
        avg_duration = sum(durations) / len(durations)

        # Token usage statistics
        total_tokens = 0
        token_interactions = 0
        for interaction in interactions:
            if interaction.response and interaction.response.token_usage:
                total_tokens += sum(interaction.response.token_usage.values())
                token_interactions += 1

        avg_tokens = total_tokens / token_interactions if token_interactions > 0 else 0

        # Provider and model distribution
        providers = {}
        models = {}
        for interaction in interactions:
            provider = interaction.request.provider
            model = interaction.request.model
            providers[provider] = providers.get(provider, 0) + 1
            models[model] = models.get(model, 0) + 1

        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "failed_interactions": failed_interactions,
            "success_rate": successful_interactions / total_interactions,
            "average_duration_ms": avg_duration,
            "total_tokens_used": total_tokens,
            "average_tokens_per_interaction": avg_tokens,
            "provider_distribution": providers,
            "model_distribution": models,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get LLM performance metrics.

        Returns:
            Performance metrics including latency, throughput, and quality
        """
        if not self._interaction_history:
            return {}

        # Latency metrics
        durations = [i.total_duration_ms for i in self._interaction_history]
        latency_metrics = {
            "min_ms": min(durations),
            "max_ms": max(durations),
            "avg_ms": sum(durations) / len(durations),
            "p50_ms": sorted(durations)[len(durations) // 2],
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)],
            "p99_ms": sorted(durations)[int(len(durations) * 0.99)],
        }

        # Quality metrics
        quality_scores = []
        for interaction in self._interaction_history:
            if (
                interaction.response
                and interaction.response.quality_metrics
                and "overall_quality" in interaction.response.quality_metrics
            ):
                quality_scores.append(
                    interaction.response.quality_metrics["overall_quality"]
                )

        quality_metrics = {}
        if quality_scores:
            quality_metrics = {
                "avg_quality": sum(quality_scores) / len(quality_scores),
                "min_quality": min(quality_scores),
                "max_quality": max(quality_scores),
            }

        # Error rate
        total_interactions = len(self._interaction_history)
        failed_interactions = len(
            [i for i in self._interaction_history if not i.success]
        )
        error_rate = (
            failed_interactions / total_interactions if total_interactions > 0 else 0
        )

        return {
            "latency_metrics": latency_metrics,
            "quality_metrics": quality_metrics,
            "error_rate": error_rate,
            "total_interactions": total_interactions,
        }
