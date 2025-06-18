"""
Agent monitoring service for real-time agent status tracking and notifications.
Core layer - business logic for agent system monitoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from shared.models.agent_models import AgentProfile, AgentStatus, TaskEvent
from shared.interfaces.agent_personality import AgentNotification


logger = logging.getLogger(__name__)


class MonitoringEventType(Enum):
    """Types of monitoring events."""
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_IDLE = "agent_idle"
    AGENT_BUSY = "agent_busy"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    COLLABORATION_STARTED = "collaboration_started"
    COLLABORATION_ENDED = "collaboration_ended"
    PERFORMANCE_ALERT = "performance_alert"
    SYSTEM_ALERT = "system_alert"


@dataclass
class MonitoringEvent:
    """Monitoring event data structure."""
    event_type: MonitoringEventType
    agent_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error


@dataclass
class AgentMonitoringData:
    """Real-time agent monitoring data."""
    agent_id: str
    status: AgentStatus
    last_activity: datetime
    current_task: Optional[str] = None
    performance_score: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    collaborations: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)


class AgentMonitoringService:
    """Service for monitoring AI agents in real-time."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self.monitoring_data: Dict[str, AgentMonitoringData] = {}
        self.event_handlers: Dict[MonitoringEventType, List[Callable]] = {}
        self.is_monitoring = False
        self.monitoring_task = None
        self.event_history: List[MonitoringEvent] = []
        self.max_history_size = 1000
        self.status_check_interval = 5.0  # seconds
        self.performance_threshold = 0.3  # Alert if performance drops below 30%
        
        # Initialize event handlers
        self._setup_default_handlers()
        
    def _setup_default_handlers(self):
        """Setup default event handlers."""
        # Register default handlers for logging
        for event_type in MonitoringEventType:
            self.register_event_handler(event_type, self._log_event)
    
    def start_monitoring(self):
        """Start the monitoring service."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Agent monitoring service started")
    
    async def stop_monitoring(self):
        """Stop the monitoring service."""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Agent monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_agent_statuses()
                await self._check_performance_alerts()
                await self._cleanup_old_events()
                await asyncio.sleep(self.status_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.status_check_interval)
    
    async def _check_agent_statuses(self):
        """Check and update agent statuses."""
        current_time = datetime.now()
        
        for agent_id, data in self.monitoring_data.items():
            # Check for idle agents
            idle_threshold = timedelta(minutes=10)
            if current_time - data.last_activity > idle_threshold:
                if data.status != AgentStatus.IDLE:
                    await self.update_agent_status(agent_id, AgentStatus.IDLE)
                    await self.emit_event(MonitoringEventType.AGENT_IDLE, agent_id, {
                        "previous_status": data.status.value,
                        "idle_duration": str(current_time - data.last_activity)
                    })
    
    async def _check_performance_alerts(self):
        """Check for performance-related alerts."""
        for agent_id, data in self.monitoring_data.items():
            # Performance score alert
            if data.performance_score < self.performance_threshold:
                alert_id = f"performance_low_{agent_id}"
                if alert_id not in data.alerts:
                    data.alerts.append(alert_id)
                    await self.emit_event(MonitoringEventType.PERFORMANCE_ALERT, agent_id, {
                        "performance_score": data.performance_score,
                        "threshold": self.performance_threshold,
                        "alert_type": "low_performance"
                    }, severity="warning")
            
            # High failure rate alert
            if data.tasks_completed > 0:
                failure_rate = data.tasks_failed / (data.tasks_completed + data.tasks_failed)
                if failure_rate > 0.3:  # 30% failure rate threshold
                    alert_id = f"high_failure_rate_{agent_id}"
                    if alert_id not in data.alerts:
                        data.alerts.append(alert_id)
                        await self.emit_event(MonitoringEventType.PERFORMANCE_ALERT, agent_id, {
                            "failure_rate": failure_rate,
                            "tasks_completed": data.tasks_completed,
                            "tasks_failed": data.tasks_failed,
                            "alert_type": "high_failure_rate"
                        }, severity="warning")
    
    async def _cleanup_old_events(self):
        """Clean up old events to prevent memory buildup."""
        if len(self.event_history) > self.max_history_size:
            # Keep only the most recent events
            self.event_history = self.event_history[-self.max_history_size:]
    
    def register_agent(self, agent_profile: AgentProfile):
        """Register an agent for monitoring."""
        monitoring_data = AgentMonitoringData(
            agent_id=agent_profile.agent_id,
            status=AgentStatus.IDLE,
            last_activity=datetime.now()
        )
        self.monitoring_data[agent_profile.agent_id] = monitoring_data
        
        # Schedule event emission if event loop is available
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit_event(
                MonitoringEventType.AGENT_STARTED,
                agent_profile.agent_id,
                {"agent_name": agent_profile.name, "role": agent_profile.role}
            ))
        except RuntimeError:
            # No event loop running, log the event instead
            logger.info(f"Agent {agent_profile.agent_id} started (no event loop for emission)")
        
        logger.info(f"Agent {agent_profile.agent_id} registered for monitoring")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from monitoring."""
        if agent_id in self.monitoring_data:
            del self.monitoring_data[agent_id]
            
            # Schedule event emission if event loop is available
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.emit_event(
                    MonitoringEventType.AGENT_STOPPED,
                    agent_id,
                    {}
                ))
            except RuntimeError:
                # No event loop running, log the event instead
                logger.info(f"Agent {agent_id} stopped (no event loop for emission)")
            
            logger.info(f"Agent {agent_id} unregistered from monitoring")
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, 
                                  additional_data: Optional[Dict[str, Any]] = None):
        """Update agent status and emit event."""
        if agent_id not in self.monitoring_data:
            logger.warning(f"Agent {agent_id} not registered for monitoring")
            return
        
        data = self.monitoring_data[agent_id]
        previous_status = data.status
        data.status = status
        data.last_activity = datetime.now()
        
        # Update additional data if provided
        if additional_data:
            if "current_task" in additional_data:
                data.current_task = additional_data["current_task"]
            if "performance_score" in additional_data:
                data.performance_score = additional_data["performance_score"]
        
        # Emit status change event
        event_type_map = {
            AgentStatus.ACTIVE: MonitoringEventType.AGENT_BUSY,
            AgentStatus.IDLE: MonitoringEventType.AGENT_IDLE,
        }
        
        if status in event_type_map:
            await self.emit_event(event_type_map[status], agent_id, {
                "previous_status": previous_status.value,
                "new_status": status.value,
                **(additional_data or {})
            })
    
    async def record_task_event(self, agent_id: str, event_type: MonitoringEventType,
                               task_data: Dict[str, Any]):
        """Record a task-related event."""
        if agent_id not in self.monitoring_data:
            logger.warning(f"Agent {agent_id} not registered for monitoring")
            return
        
        data = self.monitoring_data[agent_id]
        data.last_activity = datetime.now()
        
        if event_type == MonitoringEventType.TASK_ASSIGNED:
            data.current_task = task_data.get("task_id")
            await self.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        elif event_type == MonitoringEventType.TASK_COMPLETED:
            data.tasks_completed += 1
            data.current_task = None
            data.performance_score = task_data.get("performance_score", data.performance_score)
            await self.update_agent_status(agent_id, AgentStatus.IDLE)
        
        elif event_type == MonitoringEventType.TASK_FAILED:
            data.tasks_failed += 1
            data.current_task = None
            await self.update_agent_status(agent_id, AgentStatus.IDLE)
        
        await self.emit_event(event_type, agent_id, task_data)
    
    async def record_collaboration_event(self, agents: List[str], 
                                       event_type: MonitoringEventType,
                                       collaboration_data: Dict[str, Any]):
        """Record a collaboration event involving multiple agents."""
        session_id = collaboration_data.get("session_id", "unknown")
        
        for agent_id in agents:
            if agent_id in self.monitoring_data:
                data = self.monitoring_data[agent_id]
                data.last_activity = datetime.now()
                
                if event_type == MonitoringEventType.COLLABORATION_STARTED:
                    if session_id not in data.collaborations:
                        data.collaborations.append(session_id)
                
                elif event_type == MonitoringEventType.COLLABORATION_ENDED:
                    if session_id in data.collaborations:
                        data.collaborations.remove(session_id)
                
                await self.emit_event(event_type, agent_id, collaboration_data)
    
    async def emit_event(self, event_type: MonitoringEventType, agent_id: str,
                        data: Dict[str, Any], severity: str = "info"):
        """Emit a monitoring event."""
        event = MonitoringEvent(
            event_type=event_type,
            agent_id=agent_id,
            timestamp=datetime.now(),
            data=data,
            severity=severity
        )
        
        # Add to history
        self.event_history.append(event)
        
        # Call registered handlers
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def register_event_handler(self, event_type: MonitoringEventType, 
                              handler: Callable):
        """Register an event handler for specific event types."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def unregister_event_handler(self, event_type: MonitoringEventType,
                                handler: Callable):
        """Unregister an event handler."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def get_agent_monitoring_data(self, agent_id: str) -> Optional[AgentMonitoringData]:
        """Get current monitoring data for an agent."""
        return self.monitoring_data.get(agent_id)
    
    def get_all_monitoring_data(self) -> Dict[str, AgentMonitoringData]:
        """Get monitoring data for all agents."""
        return self.monitoring_data.copy()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system monitoring status."""
        total_agents = len(self.monitoring_data)
        active_agents = sum(1 for data in self.monitoring_data.values() 
                           if data.status == AgentStatus.ACTIVE)
        idle_agents = sum(1 for data in self.monitoring_data.values() 
                         if data.status == AgentStatus.IDLE)
        
        # Calculate average performance
        avg_performance = 0.0
        if self.monitoring_data:
            avg_performance = sum(data.performance_score for data in self.monitoring_data.values()) / total_agents
        
        # Count alerts
        total_alerts = sum(len(data.alerts) for data in self.monitoring_data.values())
        
        # Recent events
        recent_events = [event for event in self.event_history 
                        if event.timestamp > datetime.now() - timedelta(hours=1)]
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "average_performance": avg_performance,
            "total_alerts": total_alerts,
            "recent_events_count": len(recent_events),
            "monitoring_active": self.is_monitoring,
            "last_update": datetime.now().isoformat()
        }
    
    def get_recent_events(self, agent_id: Optional[str] = None, 
                         hours: int = 1) -> List[MonitoringEvent]:
        """Get recent events, optionally filtered by agent."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        events = [event for event in self.event_history 
                 if event.timestamp > cutoff_time]
        
        if agent_id:
            events = [event for event in events if event.agent_id == agent_id]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)
    
    def clear_agent_alerts(self, agent_id: str):
        """Clear all alerts for a specific agent."""
        if agent_id in self.monitoring_data:
            self.monitoring_data[agent_id].alerts.clear()
            logger.info(f"Cleared alerts for agent {agent_id}")
    
    def _log_event(self, event: MonitoringEvent):
        """Default event handler for logging."""
        level = logging.INFO
        if event.severity == "warning":
            level = logging.WARNING
        elif event.severity == "error":
            level = logging.ERROR
        
        logger.log(level, 
                  f"Agent {event.agent_id}: {event.event_type.value} - {event.data}")