"""
Learning and adaptation engine for AI agents.
Analyzes performance, identifies improvements, and adapts agent behavior.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import uuid
import statistics
from collections import defaultdict, deque

from shared.interfaces.agent_personality import LearningSystem
from shared.models.agent_models import (
    LearningRecord,
    PerformanceMetrics,
    SkillAssessment,
    AgentProfile,
    TaskAssignment,
    TaskStatus
)


class LearningEngine(LearningSystem):
    """
    Core learning and adaptation system for AI agents.
    Implements performance analysis, improvement identification, and adaptation.
    """

    def __init__(self, database_path: str = "agent_learning.db"):
        """
        Initialize learning engine.

        Args:
            database_path: Path to SQLite database for learning data
        """
        self.database_path = database_path
        self.learning_cache: Dict[str, List[LearningRecord]] = defaultdict(list)
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        self.skill_assessments: Dict[str, Dict[str, SkillAssessment]] = defaultdict(dict)
        self._initialize_database()
        self._load_recent_learning_data()

    def _initialize_database(self) -> None:
        """Initialize database tables for learning data."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Learning records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_records (
                record_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                learning_type TEXT NOT NULL,
                experience_data TEXT NOT NULL,
                outcome TEXT NOT NULL,
                lessons_learned TEXT NOT NULL,
                skill_improvements TEXT NOT NULL,
                confidence_changes TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                feedback_received TEXT,
                applied_successfully INTEGER DEFAULT 0
            )
        """)

        # Performance tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_history (
                metric_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                metrics TEXT NOT NULL,
                task_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                average_completion_time REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,
                collaboration_score REAL DEFAULT 0.0,
                learning_progress TEXT NOT NULL,
                areas_for_improvement TEXT NOT NULL,
                strengths TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # Skill assessments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_assessments (
                assessment_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                skill_domain TEXT NOT NULL,
                assessed_skills TEXT NOT NULL,
                strengths TEXT NOT NULL,
                improvement_areas TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                assessor TEXT NOT NULL,
                assessment_date TEXT NOT NULL,
                next_assessment_date TEXT
            )
        """)

        # Adaptation tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptations (
                adaptation_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                adaptation_type TEXT NOT NULL,
                changes_made TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                expected_impact TEXT NOT NULL,
                actual_impact TEXT,
                timestamp TEXT NOT NULL,
                success_indicator REAL,
                rollback_data TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_recent_learning_data(self) -> None:
        """Load recent learning data into cache."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Load recent learning records
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT * FROM learning_records 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        """, (cutoff_date,))

        for row in cursor.fetchall():
            record = LearningRecord(
                record_id=row[0],
                agent_id=row[1],
                learning_type=row[2],
                experience_data=json.loads(row[3]),
                outcome=row[4],
                lessons_learned=json.loads(row[5]),
                skill_improvements=json.loads(row[6]),
                confidence_changes=json.loads(row[7]),
                timestamp=datetime.fromisoformat(row[8]),
                feedback_received=row[9],
                applied_successfully=bool(row[10])
            )
            self.learning_cache[record.agent_id].append(record)

        conn.close()

    def analyze_performance(
        self,
        agent_id: str,
        task_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze agent performance across multiple tasks.

        Args:
            agent_id: ID of the agent to analyze
            task_results: List of task completion results

        Returns:
            Dictionary containing performance analysis
        """
        if not task_results:
            return {"error": "No task results provided"}

        # Calculate basic metrics
        total_tasks = len(task_results)
        successful_tasks = sum(1 for task in task_results if task.get('success', False))
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

        # Calculate completion times
        completion_times = [
            task.get('completion_time', 0) for task in task_results 
            if task.get('completion_time') is not None
        ]
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0.0

        # Calculate quality scores
        quality_scores = [
            task.get('quality_score', 0) for task in task_results 
            if task.get('quality_score') is not None
        ]
        avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0.0

        # Analyze task types and difficulty
        task_types = defaultdict(list)
        for task in task_results:
            task_type = task.get('task_type', 'unknown')
            task_types[task_type].append(task)

        # Performance by task type
        performance_by_type: Dict[str, Any] = {}
        for task_type, tasks in task_types.items():
            type_success_rate = sum(1 for t in tasks if t.get('success', False)) / len(tasks)
            type_avg_time = statistics.mean([
                t.get('completion_time', 0) for t in tasks 
                if t.get('completion_time') is not None
            ]) if any(t.get('completion_time') for t in tasks) else 0.0
            
            performance_by_type[task_type] = {
                'success_rate': type_success_rate,
                'average_time': type_avg_time,
                'task_count': len(tasks)
            }

        # Identify trends over time
        if len(task_results) >= 5:
            recent_tasks = sorted(task_results, key=lambda x: x.get('timestamp', ''))[-5:]
            recent_success_rate = sum(1 for t in recent_tasks if t.get('success', False)) / len(recent_tasks)
            trend = "improving" if recent_success_rate > success_rate else "declining"
        else:
            trend = "insufficient_data"

        # Create performance metrics object
        performance_metrics = PerformanceMetrics(
            agent_id=agent_id,
            metric_type="task_analysis",
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            metrics={
                'success_rate': success_rate,
                'completion_time': avg_completion_time,
                'quality_score': avg_quality_score,
                'task_count': total_tasks
            },
            task_count=total_tasks,
            success_rate=success_rate,
            average_completion_time=avg_completion_time,
            quality_score=avg_quality_score
        )

        # Store performance data
        self._store_performance_metrics(performance_metrics)

        analysis_result = {
            'agent_id': agent_id,
            'total_tasks': total_tasks,
            'success_rate': success_rate,
            'average_completion_time': avg_completion_time,
            'average_quality_score': avg_quality_score,
            'performance_by_type': performance_by_type,
            'trend': trend,
            'analysis_date': datetime.now().isoformat(),
            'recommendations': self._generate_performance_recommendations(
                success_rate, avg_completion_time, avg_quality_score, performance_by_type
            )
        }

        return analysis_result

    def _store_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Store performance metrics in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            metric_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO performance_history (
                    metric_id, agent_id, metric_type, period_start, period_end,
                    metrics, task_count, success_rate, average_completion_time,
                    quality_score, collaboration_score, learning_progress,
                    areas_for_improvement, strengths, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric_id, metrics.agent_id, metrics.metric_type,
                metrics.period_start.isoformat(), metrics.period_end.isoformat(),
                json.dumps(metrics.metrics), metrics.task_count,
                metrics.success_rate, metrics.average_completion_time,
                metrics.quality_score, metrics.collaboration_score,
                json.dumps(metrics.learning_progress),
                json.dumps(metrics.areas_for_improvement),
                json.dumps(metrics.strengths),
                metrics.timestamp.isoformat()
            ))

            conn.commit()
            conn.close()

            # Update cache
            self.performance_cache[metrics.agent_id] = metrics

        except Exception as e:
            print(f"Error storing performance metrics: {e}")

    def _generate_performance_recommendations(
        self,
        success_rate: float,
        avg_completion_time: float,
        avg_quality_score: float,
        performance_by_type: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Success rate recommendations
        if success_rate < 0.7:
            recommendations.append("Focus on task completion accuracy and error reduction")
        elif success_rate > 0.9:
            recommendations.append("Excellent success rate - consider taking on more challenging tasks")

        # Completion time recommendations
        if avg_completion_time > 120:  # More than 2 hours average
            recommendations.append("Consider time management techniques and task prioritization")
        elif avg_completion_time < 30:  # Less than 30 minutes average
            recommendations.append("Fast completion time - ensure quality is maintained")

        # Quality score recommendations
        if avg_quality_score < 0.7:
            recommendations.append("Focus on improving output quality and attention to detail")
        elif avg_quality_score > 0.9:
            recommendations.append("High quality work - excellent attention to detail")

        # Task type specific recommendations
        worst_performing_type = min(
            performance_by_type.items(),
            key=lambda x: x[1]['success_rate'],
            default=(None, {'success_rate': 1.0})
        )
        
        if worst_performing_type[0] and worst_performing_type[1]['success_rate'] < 0.6:
            recommendations.append(
                f"Consider additional training or support for {worst_performing_type[0]} tasks"
            )

        return recommendations

    def identify_improvement_areas(
        self,
        agent_id: str,
        performance_data: Dict[str, Any]
    ) -> List[str]:
        """
        Identify areas where the agent can improve.

        Args:
            agent_id: ID of the agent
            performance_data: Performance analysis results

        Returns:
            List of improvement areas
        """
        improvement_areas = []

        # Analyze success rates by task type
        performance_by_type = performance_data.get('performance_by_type', {})
        for task_type, metrics in performance_by_type.items():
            if metrics['success_rate'] < 0.7:
                improvement_areas.append(f"Task execution in {task_type}")

        # Analyze completion times
        if performance_data.get('average_completion_time', 0) > 100:
            improvement_areas.append("Time management and efficiency")

        # Analyze quality scores
        if performance_data.get('average_quality_score', 0) < 0.7:
            improvement_areas.append("Output quality and attention to detail")

        # Check historical learning data
        recent_learning = self.learning_cache.get(agent_id, [])
        if recent_learning:
            # Identify recurring issues
            common_issues = defaultdict(int)
            for record in recent_learning[-10:]:  # Last 10 learning records
                for lesson in record.lessons_learned:
                    if "failed" in lesson.lower() or "error" in lesson.lower():
                        common_issues[record.learning_type] += 1

            for issue_type, count in common_issues.items():
                if count >= 3:  # Recurring issue
                    improvement_areas.append(f"Recurring challenges in {issue_type}")

        # Analyze skill gaps from assessments
        if agent_id in self.skill_assessments:
            for domain, assessment in self.skill_assessments[agent_id].items():
                improvement_areas.extend(assessment.improvement_areas)

        # Remove duplicates and return
        return list(set(improvement_areas))

    def adapt_personality(
        self,
        agent_id: str,
        adaptation_data: Dict[str, Any]
    ) -> bool:
        """
        Adapt agent personality based on learning.

        Args:
            agent_id: ID of the agent to adapt
            adaptation_data: Data indicating what adaptations to make

        Returns:
            True if adaptation successful
        """
        try:
            # Extract adaptation parameters
            personality_changes = adaptation_data.get('personality_changes', {})
            skill_updates = adaptation_data.get('skill_updates', {})
            behavior_modifications = adaptation_data.get('behavior_modifications', {})

            # Create adaptation record
            adaptation_id = str(uuid.uuid4())
            changes_made = {
                'personality_changes': personality_changes,
                'skill_updates': skill_updates,
                'behavior_modifications': behavior_modifications
            }

            # Store adaptation record
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO adaptations (
                    adaptation_id, agent_id, adaptation_type, changes_made,
                    reasoning, expected_impact, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                adaptation_id,
                agent_id,
                adaptation_data.get('adaptation_type', 'personality_update'),
                json.dumps(changes_made),
                adaptation_data.get('reasoning', 'Learning-based adaptation'),
                json.dumps(adaptation_data.get('expected_impact', {})),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            # Create learning record for this adaptation
            learning_record = LearningRecord(
                record_id=str(uuid.uuid4()),
                agent_id=agent_id,
                learning_type="personality_adaptation",
                experience_data=adaptation_data,
                outcome="adaptation_applied",
                lessons_learned=[f"Adapted based on {adaptation_data.get('trigger', 'performance analysis')}"],
                skill_improvements=skill_updates,
                confidence_changes={}
            )

            self._store_learning_record(learning_record)

            return True

        except Exception as e:
            print(f"Error adapting personality: {e}")
            return False

    def generate_training_data(
        self,
        agent_id: str,
        improvement_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate training scenarios for improvement.

        Args:
            agent_id: ID of the agent
            improvement_areas: Areas identified for improvement

        Returns:
            List of training scenarios
        """
        training_scenarios = []

        for area in improvement_areas:
            scenarios = self._create_scenarios_for_area(area, agent_id)
            training_scenarios.extend(scenarios)

        return training_scenarios

    def _create_scenarios_for_area(self, area: str, agent_id: str) -> List[Dict[str, Any]]:
        """Create training scenarios for a specific improvement area."""
        scenarios = []

        if "time management" in area.lower():
            scenarios.extend([
                {
                    'scenario_id': str(uuid.uuid4()),
                    'title': 'Priority Task Management',
                    'description': 'Practice managing multiple tasks with different priorities',
                    'skill_focus': 'time_management',
                    'difficulty': 'medium',
                    'expected_duration': 45,
                    'success_criteria': ['Complete high priority tasks first', 'Meet all deadlines']
                },
                {
                    'scenario_id': str(uuid.uuid4()),
                    'title': 'Deadline Pressure Simulation',
                    'description': 'Handle tasks under tight deadline constraints',
                    'skill_focus': 'time_management',
                    'difficulty': 'high',
                    'expected_duration': 30,
                    'success_criteria': ['Maintain quality under pressure', 'Complete within deadline']
                }
            ])

        elif "quality" in area.lower():
            scenarios.extend([
                {
                    'scenario_id': str(uuid.uuid4()),
                    'title': 'Quality Review Process',
                    'description': 'Practice thorough quality checking procedures',
                    'skill_focus': 'quality_assurance',
                    'difficulty': 'medium',
                    'expected_duration': 60,
                    'success_criteria': ['Identify all quality issues', 'Propose effective solutions']
                }
            ])

        elif "task execution" in area.lower():
            scenarios.extend([
                {
                    'scenario_id': str(uuid.uuid4()),
                    'title': 'Complex Task Breakdown',
                    'description': 'Practice breaking down complex tasks into manageable steps',
                    'skill_focus': 'task_management',
                    'difficulty': 'medium',
                    'expected_duration': 40,
                    'success_criteria': ['Create clear task breakdown', 'Execute systematically']
                }
            ])

        return scenarios

    def record_learning_experience(
        self,
        agent_id: str,
        experience_type: str,
        experience_data: Dict[str, Any],
        outcome: str,
        lessons_learned: List[str],
        feedback: Optional[str] = None
    ) -> str:
        """
        Record a learning experience for an agent.

        Args:
            agent_id: ID of the agent
            experience_type: Type of learning experience
            experience_data: Details of the experience
            outcome: Result of the experience
            lessons_learned: Key lessons from the experience
            feedback: Optional feedback on the experience

        Returns:
            Learning record ID
        """
        learning_record = LearningRecord(
            record_id=str(uuid.uuid4()),
            agent_id=agent_id,
            learning_type=experience_type,
            experience_data=experience_data,
            outcome=outcome,
            lessons_learned=lessons_learned,
            skill_improvements={},
            confidence_changes={},
            feedback_received=feedback
        )

        self._store_learning_record(learning_record)
        
        # Add to cache
        self.learning_cache[agent_id].append(learning_record)
        
        # Keep cache size manageable
        if len(self.learning_cache[agent_id]) > 50:
            self.learning_cache[agent_id] = self.learning_cache[agent_id][-50:]

        return learning_record.record_id

    def _store_learning_record(self, record: LearningRecord) -> None:
        """Store learning record in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO learning_records (
                    record_id, agent_id, learning_type, experience_data,
                    outcome, lessons_learned, skill_improvements,
                    confidence_changes, timestamp, feedback_received,
                    applied_successfully
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id, record.agent_id, record.learning_type,
                json.dumps(record.experience_data), record.outcome,
                json.dumps(record.lessons_learned),
                json.dumps(record.skill_improvements),
                json.dumps(record.confidence_changes),
                record.timestamp.isoformat(), record.feedback_received,
                int(record.applied_successfully)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error storing learning record: {e}")

    def get_learning_progress(
        self,
        agent_id: str,
        skill_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get learning progress for an agent.

        Args:
            agent_id: ID of the agent
            skill_domain: Optional specific skill domain

        Returns:
            Learning progress information
        """
        # Get learning records
        learning_records = self.learning_cache.get(agent_id, [])
        
        if not learning_records:
            # Try loading from database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM learning_records 
                WHERE agent_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            """, (agent_id,))
            
            for row in cursor.fetchall():
                record = LearningRecord(
                    record_id=row[0],
                    agent_id=row[1],
                    learning_type=row[2],
                    experience_data=json.loads(row[3]),
                    outcome=row[4],
                    lessons_learned=json.loads(row[5]),
                    skill_improvements=json.loads(row[6]),
                    confidence_changes=json.loads(row[7]),
                    timestamp=datetime.fromisoformat(row[8]),
                    feedback_received=row[9],
                    applied_successfully=bool(row[10])
                )
                learning_records.append(record)
            
            conn.close()

        # Analyze progress
        if skill_domain:
            learning_records = [r for r in learning_records if skill_domain in r.learning_type]

        total_experiences = len(learning_records)
        successful_applications = sum(1 for r in learning_records if r.applied_successfully)
        
        # Calculate skill improvements over time
        skill_progress = defaultdict(list)
        for record in learning_records:
            for skill, improvement in record.skill_improvements.items():
                skill_progress[skill].append({
                    'improvement': improvement,
                    'timestamp': record.timestamp.isoformat()
                })

        # Calculate learning velocity (learning per time period)
        if len(learning_records) >= 2:
            time_span = (learning_records[0].timestamp - learning_records[-1].timestamp).days
            learning_velocity = total_experiences / max(time_span, 1)
        else:
            learning_velocity = 0.0

        return {
            'agent_id': agent_id,
            'total_experiences': total_experiences,
            'successful_applications': successful_applications,
            'application_rate': successful_applications / total_experiences if total_experiences > 0 else 0.0,
            'skill_progress': dict(skill_progress),
            'learning_velocity': learning_velocity,
            'recent_lessons': [
                record.lessons_learned for record in learning_records[:5]
            ],
            'analysis_date': datetime.now().isoformat()
        }