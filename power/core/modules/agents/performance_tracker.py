"""
Performance tracking and optimization system for AI agents.
Monitors agent performance, generates reports, and identifies optimization opportunities.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import uuid
import statistics
from collections import defaultdict, deque
from dataclasses import asdict

from shared.interfaces.agent_personality import PerformanceTracker
from shared.models.agent_models import PerformanceMetrics, TaskAssignment, TaskStatus


class AgentPerformanceTracker(PerformanceTracker):
    """
    Core performance tracking system for AI agents.
    Implements comprehensive performance monitoring and optimization.
    """

    def __init__(self, database_path: str = "agent_performance.db"):
        """
        Initialize performance tracker.

        Args:
            database_path: Path to SQLite database for performance data
        """
        self.database_path = database_path
        self.performance_cache: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.task_cache: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.optimization_cache: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._initialize_database()
        self._load_recent_performance_data()

    def _initialize_database(self) -> None:
        """Initialize database tables for performance tracking."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Task performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_performance (
                performance_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                completion_time_minutes REAL,
                success INTEGER NOT NULL DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                efficiency_score REAL DEFAULT 0.0,
                collaboration_score REAL DEFAULT 0.0,
                resource_usage TEXT,
                errors_encountered TEXT,
                lessons_learned TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
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
                learning_progress TEXT,
                areas_for_improvement TEXT,
                strengths TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        # Optimization opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_opportunities (
                opportunity_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                opportunity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 5,
                potential_impact TEXT NOT NULL,
                recommended_actions TEXT NOT NULL,
                implementation_effort TEXT NOT NULL,
                identified_at TEXT NOT NULL,
                status TEXT DEFAULT 'identified',
                implementation_notes TEXT
            )
        """)

        # Performance trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_trends (
                trend_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                trend_direction TEXT NOT NULL,
                trend_strength REAL NOT NULL,
                time_period TEXT NOT NULL,
                trend_data TEXT NOT NULL,
                significance_level REAL NOT NULL,
                identified_at TEXT NOT NULL
            )
        """)

        # Skill development tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_development (
                development_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                initial_level INTEGER NOT NULL,
                current_level INTEGER NOT NULL,
                target_level INTEGER NOT NULL,
                development_plan TEXT,
                milestones TEXT,
                progress_data TEXT,
                last_updated TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _load_recent_performance_data(self) -> None:
        """Load recent performance data into cache."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Load recent task performance
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("""
            SELECT * FROM task_performance 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        """, (cutoff_date,))

        for row in cursor.fetchall():
            task_data = {
                'performance_id': row[0],
                'agent_id': row[1],
                'task_id': row[2],
                'task_type': row[3],
                'start_time': row[4],
                'end_time': row[5],
                'completion_time_minutes': row[6],
                'success': bool(row[7]),
                'quality_score': row[8],
                'efficiency_score': row[9],
                'collaboration_score': row[10],
                'resource_usage': json.loads(row[11]) if row[11] else {},
                'errors_encountered': json.loads(row[12]) if row[12] else [],
                'lessons_learned': json.loads(row[13]) if row[13] else [],
                'timestamp': row[14]
            }
            self.task_cache[task_data['agent_id']].append(task_data)

        conn.close()

    def record_task_performance(
        self,
        agent_id: str,
        task_id: str,
        performance_metrics: Dict[str, Any]
    ) -> bool:
        """
        Record performance metrics for a completed task.

        Args:
            agent_id: ID of the agent
            task_id: ID of the completed task
            performance_metrics: Dictionary containing performance data

        Returns:
            True if recording successful
        """
        try:
            performance_id = str(uuid.uuid4())
            
            # Extract metrics with defaults
            task_type = performance_metrics.get('task_type', 'unknown')
            start_time = performance_metrics.get('start_time', datetime.now().isoformat())
            end_time = performance_metrics.get('end_time', datetime.now().isoformat())
            
            # Calculate completion time if not provided
            if 'completion_time_minutes' in performance_metrics:
                completion_time = performance_metrics['completion_time_minutes']
            else:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                completion_time = (end_dt - start_dt).total_seconds() / 60

            # Store in database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO task_performance (
                    performance_id, agent_id, task_id, task_type, start_time,
                    end_time, completion_time_minutes, success, quality_score,
                    efficiency_score, collaboration_score, resource_usage,
                    errors_encountered, lessons_learned, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                performance_id, agent_id, task_id, task_type, start_time,
                end_time, completion_time,
                int(performance_metrics.get('success', False)),
                performance_metrics.get('quality_score', 0.0),
                performance_metrics.get('efficiency_score', 0.0),
                performance_metrics.get('collaboration_score', 0.0),
                json.dumps(performance_metrics.get('resource_usage', {})),
                json.dumps(performance_metrics.get('errors_encountered', [])),
                json.dumps(performance_metrics.get('lessons_learned', [])),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            # Update cache
            task_data = {
                'performance_id': performance_id,
                'agent_id': agent_id,
                'task_id': task_id,
                'task_type': task_type,
                'start_time': start_time,
                'end_time': end_time,
                'completion_time_minutes': completion_time,
                'success': performance_metrics.get('success', False),
                'quality_score': performance_metrics.get('quality_score', 0.0),
                'efficiency_score': performance_metrics.get('efficiency_score', 0.0),
                'collaboration_score': performance_metrics.get('collaboration_score', 0.0),
                'resource_usage': performance_metrics.get('resource_usage', {}),
                'errors_encountered': performance_metrics.get('errors_encountered', []),
                'lessons_learned': performance_metrics.get('lessons_learned', []),
                'timestamp': datetime.now().isoformat()
            }
            
            self.task_cache[agent_id].append(task_data)
            
            # Keep cache size manageable
            if len(self.task_cache[agent_id]) > 100:
                self.task_cache[agent_id] = self.task_cache[agent_id][-100:]

            return True

        except Exception as e:
            print(f"Error recording task performance: {e}")
            return False

    def generate_performance_report(
        self,
        agent_id: str,
        time_period: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            agent_id: ID of the agent
            time_period: Time period for report (e.g., 'last_week', 'last_month')

        Returns:
            Dictionary containing performance report
        """
        # Determine time range
        end_date = datetime.now()
        if time_period == 'last_week':
            start_date = end_date - timedelta(days=7)
        elif time_period == 'last_month':
            start_date = end_date - timedelta(days=30)
        elif time_period == 'last_quarter':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)  # Default to last month

        # Get task performance data
        task_data = self._get_task_performance_in_period(agent_id, start_date, end_date)
        
        if not task_data:
            return {
                'agent_id': agent_id,
                'time_period': time_period,
                'error': 'No performance data available for the specified period'
            }

        # Calculate basic metrics
        total_tasks = len(task_data)
        successful_tasks = sum(1 for task in task_data if task['success'])
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

        # Calculate average scores
        quality_scores = [task['quality_score'] for task in task_data if task['quality_score'] > 0]
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0

        efficiency_scores = [task['efficiency_score'] for task in task_data if task['efficiency_score'] > 0]
        avg_efficiency = statistics.mean(efficiency_scores) if efficiency_scores else 0.0

        collaboration_scores = [task['collaboration_score'] for task in task_data if task['collaboration_score'] > 0]
        avg_collaboration = statistics.mean(collaboration_scores) if collaboration_scores else 0.0

        # Calculate completion times
        completion_times = [task['completion_time_minutes'] for task in task_data if task['completion_time_minutes']]
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0.0

        # Analyze task types
        task_type_performance = self._analyze_task_type_performance(task_data)

        # Identify trends
        trend_analysis = self._analyze_performance_trends(agent_id, task_data)

        # Identify common errors
        error_analysis = self._analyze_common_errors(task_data)

        # Generate recommendations
        recommendations = self._generate_performance_recommendations(
            success_rate, avg_quality, avg_efficiency, avg_completion_time, task_type_performance
        )

        # Create performance metrics object
        performance_metrics = PerformanceMetrics(
            agent_id=agent_id,
            metric_type=f"report_{time_period}",
            period_start=start_date,
            period_end=end_date,
            metrics={
                'total_tasks': total_tasks,
                'success_rate': success_rate,
                'avg_quality': avg_quality,
                'avg_efficiency': avg_efficiency,
                'avg_collaboration': avg_collaboration,
                'avg_completion_time': avg_completion_time
            },
            task_count=total_tasks,
            success_rate=success_rate,
            average_completion_time=avg_completion_time,
            quality_score=avg_quality,
            collaboration_score=avg_collaboration
        )

        # Store performance metrics
        self._store_performance_metrics(performance_metrics)

        return {
            'agent_id': agent_id,
            'time_period': time_period,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'summary': {
                'total_tasks': total_tasks,
                'success_rate': success_rate,
                'average_quality_score': avg_quality,
                'average_efficiency_score': avg_efficiency,
                'average_collaboration_score': avg_collaboration,
                'average_completion_time_minutes': avg_completion_time
            },
            'task_type_performance': task_type_performance,
            'trend_analysis': trend_analysis,
            'error_analysis': error_analysis,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }

    def _get_task_performance_in_period(
        self,
        agent_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get task performance data for a specific time period."""
        # Check cache first
        cached_tasks = []
        for task in self.task_cache.get(agent_id, []):
            task_time = datetime.fromisoformat(task['timestamp'])
            if start_date <= task_time <= end_date:
                cached_tasks.append(task)

        # If we have recent data in cache, use it
        if cached_tasks and (datetime.now() - end_date).days < 7:
            return cached_tasks

        # Otherwise query database
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM task_performance 
                WHERE agent_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """, (agent_id, start_date.isoformat(), end_date.isoformat()))

            task_data = []
            for row in cursor.fetchall():
                task_data.append({
                    'performance_id': row[0],
                    'agent_id': row[1],
                    'task_id': row[2],
                    'task_type': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'completion_time_minutes': row[6],
                    'success': bool(row[7]),
                    'quality_score': row[8],
                    'efficiency_score': row[9],
                    'collaboration_score': row[10],
                    'resource_usage': json.loads(row[11]) if row[11] else {},
                    'errors_encountered': json.loads(row[12]) if row[12] else [],
                    'lessons_learned': json.loads(row[13]) if row[13] else [],
                    'timestamp': row[14]
                })

            conn.close()
            return task_data

        except Exception as e:
            print(f"Error getting task performance data: {e}")
            return []

    def _analyze_task_type_performance(self, task_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by task type."""
        task_type_stats = defaultdict(lambda: {
            'total': 0,
            'successful': 0,
            'quality_scores': [],
            'completion_times': []
        })

        for task in task_data:
            task_type = task['task_type']
            stats = task_type_stats[task_type]
            
            stats['total'] += 1
            if task['success']:
                stats['successful'] += 1
            
            if task['quality_score'] > 0:
                stats['quality_scores'].append(task['quality_score'])
            
            if task['completion_time_minutes']:
                stats['completion_times'].append(task['completion_time_minutes'])

        # Calculate summary statistics
        performance_by_type = {}
        for task_type, stats in task_type_stats.items():
            performance_by_type[task_type] = {
                'total_tasks': stats['total'],
                'success_rate': stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0,
                'average_quality': statistics.mean(stats['quality_scores']) if stats['quality_scores'] else 0.0,
                'average_completion_time': statistics.mean(stats['completion_times']) if stats['completion_times'] else 0.0
            }

        return performance_by_type

    def _analyze_performance_trends(self, agent_id: str, task_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(task_data) < 5:
            return {'trend': 'insufficient_data'}

        # Sort by timestamp
        sorted_tasks = sorted(task_data, key=lambda x: x['timestamp'])
        
        # Split into two halves for comparison
        mid_point = len(sorted_tasks) // 2
        first_half = sorted_tasks[:mid_point]
        second_half = sorted_tasks[mid_point:]

        # Calculate metrics for each half
        first_half_success = sum(1 for t in first_half if t['success']) / len(first_half)
        second_half_success = sum(1 for t in second_half if t['success']) / len(second_half)

        # Quality trend
        first_half_quality = statistics.mean([t['quality_score'] for t in first_half if t['quality_score'] > 0]) or 0
        second_half_quality = statistics.mean([t['quality_score'] for t in second_half if t['quality_score'] > 0]) or 0

        # Time trend
        first_half_time = statistics.mean([t['completion_time_minutes'] for t in first_half if t['completion_time_minutes']]) or 0
        second_half_time = statistics.mean([t['completion_time_minutes'] for t in second_half if t['completion_time_minutes']]) or 0

        return {
            'success_rate_trend': 'improving' if second_half_success > first_half_success else 'declining',
            'quality_trend': 'improving' if second_half_quality > first_half_quality else 'declining',
            'efficiency_trend': 'improving' if second_half_time < first_half_time else 'declining',
            'success_rate_change': second_half_success - first_half_success,
            'quality_change': second_half_quality - first_half_quality,
            'time_change': second_half_time - first_half_time
        }

    def _analyze_common_errors(self, task_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze common errors and issues."""
        all_errors = []
        error_counts = defaultdict(int)

        for task in task_data:
            for error in task['errors_encountered']:
                all_errors.append(error)
                error_counts[error] += 1

        # Find most common errors
        most_common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_errors': len(all_errors),
            'unique_errors': len(error_counts),
            'most_common_errors': most_common_errors,
            'error_rate': len(all_errors) / len(task_data) if task_data else 0.0
        }

    def _generate_performance_recommendations(
        self,
        success_rate: float,
        avg_quality: float,
        avg_efficiency: float,
        avg_completion_time: float,
        task_type_performance: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Success rate recommendations
        if success_rate < 0.7:
            recommendations.append("Focus on improving task completion rate through better preparation and error prevention")
        elif success_rate > 0.9:
            recommendations.append("Excellent success rate - consider taking on more challenging tasks")

        # Quality recommendations
        if avg_quality < 0.7:
            recommendations.append("Implement quality checkpoints and review processes to improve output quality")
        elif avg_quality > 0.9:
            recommendations.append("Maintaining high quality standards - excellent attention to detail")

        # Efficiency recommendations
        if avg_efficiency < 0.6:
            recommendations.append("Explore automation opportunities and process optimization to improve efficiency")

        # Time management recommendations
        if avg_completion_time > 120:  # More than 2 hours average
            recommendations.append("Consider time management techniques and task breakdown strategies")

        # Task-specific recommendations
        worst_performing_task = None
        worst_success_rate = 1.0
        
        for task_type, performance in task_type_performance.items():
            if performance['success_rate'] < worst_success_rate:
                worst_success_rate = performance['success_rate']
                worst_performing_task = task_type

        if worst_performing_task and worst_success_rate < 0.6:
            recommendations.append(f"Focus improvement efforts on {worst_performing_task} tasks")

        return recommendations

    def _store_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Store performance metrics in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            metric_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO performance_metrics (
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
            if metrics.agent_id not in self.performance_cache:
                self.performance_cache[metrics.agent_id] = []
            self.performance_cache[metrics.agent_id].append(metrics)

        except Exception as e:
            print(f"Error storing performance metrics: {e}")

    def compare_agent_performance(
        self,
        agent_ids: List[str],
        metric: str
    ) -> Dict[str, Any]:
        """
        Compare performance across multiple agents.

        Args:
            agent_ids: List of agent IDs to compare
            metric: Specific metric to compare

        Returns:
            Dictionary containing comparison results
        """
        comparison_data = {}
        
        for agent_id in agent_ids:
            # Get recent performance data
            recent_tasks = self.task_cache.get(agent_id, [])[-20:]  # Last 20 tasks
            
            if not recent_tasks:
                comparison_data[agent_id] = {'error': 'No recent performance data'}
                continue

            if metric == 'success_rate':
                value = sum(1 for task in recent_tasks if task['success']) / len(recent_tasks)
            elif metric == 'quality_score':
                quality_scores = [task['quality_score'] for task in recent_tasks if task['quality_score'] > 0]
                value = statistics.mean(quality_scores) if quality_scores else 0.0
            elif metric == 'completion_time':
                completion_times = [task['completion_time_minutes'] for task in recent_tasks if task['completion_time_minutes']]
                value = statistics.mean(completion_times) if completion_times else 0.0
            elif metric == 'efficiency_score':
                efficiency_scores = [task['efficiency_score'] for task in recent_tasks if task['efficiency_score'] > 0]
                value = statistics.mean(efficiency_scores) if efficiency_scores else 0.0
            else:
                value = 0.0

            comparison_data[agent_id] = {
                'value': value,
                'task_count': len(recent_tasks),
                'metric': metric
            }

        # Rank agents
        ranked_agents = sorted(
            comparison_data.items(),
            key=lambda x: x[1].get('value', 0),
            reverse=(metric != 'completion_time')  # Lower completion time is better
        )

        return {
            'metric': metric,
            'comparison_data': comparison_data,
            'ranking': [(agent_id, data) for agent_id, data in ranked_agents],
            'best_performer': ranked_agents[0][0] if ranked_agents else None,
            'comparison_date': datetime.now().isoformat()
        }

    def identify_optimization_opportunities(
        self,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Identify opportunities for performance optimization.

        Args:
            agent_id: ID of the agent

        Returns:
            List of optimization opportunities
        """
        opportunities = []

        # Get recent performance data
        recent_tasks = self.task_cache.get(agent_id, [])[-30:]  # Last 30 tasks
        
        if not recent_tasks:
            return opportunities

        # Analyze for optimization opportunities
        
        # 1. Task type performance gaps
        task_type_performance = self._analyze_task_type_performance(recent_tasks)
        for task_type, performance in task_type_performance.items():
            if performance['success_rate'] < 0.7:
                opportunities.append({
                    'type': 'skill_improvement',
                    'description': f"Improve performance in {task_type} tasks",
                    'priority': 8,
                    'potential_impact': f"Could improve success rate from {performance['success_rate']:.1%} to 85%+",
                    'recommended_actions': [
                        f"Additional training in {task_type}",
                        "Practice with simulated scenarios",
                        "Seek mentoring from high-performing agents"
                    ],
                    'implementation_effort': 'medium'
                })

        # 2. Time efficiency opportunities
        completion_times = [task['completion_time_minutes'] for task in recent_tasks if task['completion_time_minutes']]
        if completion_times:
            avg_time = statistics.mean(completion_times)
            if avg_time > 90:  # More than 1.5 hours average
                opportunities.append({
                    'type': 'time_optimization',
                    'description': "Reduce task completion time through process optimization",
                    'priority': 7,
                    'potential_impact': f"Could reduce average completion time by 20-30%",
                    'recommended_actions': [
                        "Analyze time-consuming steps",
                        "Implement automation where possible",
                        "Optimize decision-making processes"
                    ],
                    'implementation_effort': 'low'
                })

        # 3. Quality improvement opportunities
        quality_scores = [task['quality_score'] for task in recent_tasks if task['quality_score'] > 0]
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            if avg_quality < 0.8:
                opportunities.append({
                    'type': 'quality_improvement',
                    'description': "Implement quality assurance processes",
                    'priority': 9,
                    'potential_impact': f"Could improve quality score from {avg_quality:.1%} to 90%+",
                    'recommended_actions': [
                        "Implement review checkpoints",
                        "Develop quality checklists",
                        "Establish quality metrics"
                    ],
                    'implementation_effort': 'medium'
                })

        # 4. Error pattern analysis
        error_analysis = self._analyze_common_errors(recent_tasks)
        if error_analysis['error_rate'] > 0.2:  # More than 20% error rate
            opportunities.append({
                'type': 'error_reduction',
                'description': "Reduce error rate through preventive measures",
                'priority': 8,
                'potential_impact': f"Could reduce error rate from {error_analysis['error_rate']:.1%} to <10%",
                'recommended_actions': [
                    "Implement error prevention protocols",
                    "Create error checking procedures",
                    "Analyze root causes of common errors"
                ],
                'implementation_effort': 'medium'
            })

        # Store opportunities in database
        for opportunity in opportunities:
            self._store_optimization_opportunity(agent_id, opportunity)

        return opportunities

    def _store_optimization_opportunity(self, agent_id: str, opportunity: Dict[str, Any]) -> None:
        """Store optimization opportunity in database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            opportunity_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO optimization_opportunities (
                    opportunity_id, agent_id, opportunity_type, description,
                    priority, potential_impact, recommended_actions,
                    implementation_effort, identified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity_id, agent_id, opportunity['type'], opportunity['description'],
                opportunity['priority'], opportunity['potential_impact'],
                json.dumps(opportunity['recommended_actions']),
                opportunity['implementation_effort'], datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error storing optimization opportunity: {e}")

    def track_learning_progress(
        self,
        agent_id: str,
        skill_area: str
    ) -> Dict[str, Any]:
        """
        Track progress in learning and skill development.

        Args:
            agent_id: ID of the agent
            skill_area: Specific skill area to track

        Returns:
            Dictionary containing learning progress information
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Get skill development data
            cursor.execute("""
                SELECT * FROM skill_development 
                WHERE agent_id = ? AND skill_name = ?
                ORDER BY last_updated DESC
                LIMIT 1
            """, (agent_id, skill_area))

            skill_data = cursor.fetchone()
            
            if not skill_data:
                # No existing skill data - create baseline
                return {
                    'agent_id': agent_id,
                    'skill_area': skill_area,
                    'status': 'not_tracked',
                    'recommendation': 'Initialize skill tracking with baseline assessment'
                }

            # Calculate progress metrics
            initial_level = skill_data[3]
            current_level = skill_data[4]
            target_level = skill_data[5]
            
            progress_percentage = ((current_level - initial_level) / 
                                 (target_level - initial_level)) * 100 if target_level > initial_level else 0

            # Get recent task performance in this skill area
            cursor.execute("""
                SELECT success, quality_score, completion_time_minutes 
                FROM task_performance 
                WHERE agent_id = ? AND task_type LIKE ?
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (agent_id, f'%{skill_area}%'))

            recent_performance = cursor.fetchall()
            
            performance_trend = 'stable'
            if len(recent_performance) >= 5:
                first_half = recent_performance[:len(recent_performance)//2]
                second_half = recent_performance[len(recent_performance)//2:]
                
                first_success_rate = sum(1 for p in first_half if p[0]) / len(first_half)
                second_success_rate = sum(1 for p in second_half if p[0]) / len(second_half)
                
                if second_success_rate > first_success_rate + 0.1:
                    performance_trend = 'improving'
                elif second_success_rate < first_success_rate - 0.1:
                    performance_trend = 'declining'

            conn.close()

            return {
                'agent_id': agent_id,
                'skill_area': skill_area,
                'initial_level': initial_level,
                'current_level': current_level,
                'target_level': target_level,
                'progress_percentage': progress_percentage,
                'performance_trend': performance_trend,
                'recent_task_count': len(recent_performance),
                'last_updated': skill_data[7],
                'next_milestone': self._calculate_next_milestone(current_level, target_level),
                'estimated_completion': self._estimate_completion_time(
                    current_level, target_level, performance_trend
                )
            }

        except Exception as e:
            print(f"Error tracking learning progress: {e}")
            return {
                'agent_id': agent_id,
                'skill_area': skill_area,
                'error': str(e)
            }

    def _calculate_next_milestone(self, current_level: int, target_level: int) -> Dict[str, Any]:
        """Calculate the next milestone for skill development."""
        if current_level >= target_level:
            return {'status': 'target_achieved'}
        
        next_level = min(current_level + 1, target_level)
        return {
            'next_level': next_level,
            'steps_remaining': target_level - current_level,
            'immediate_goal': f"Advance from level {current_level} to level {next_level}"
        }

    def _estimate_completion_time(
        self,
        current_level: int,
        target_level: int,
        trend: str
    ) -> str:
        """Estimate time to complete skill development."""
        levels_remaining = target_level - current_level
        
        if levels_remaining <= 0:
            return "Target achieved"
        
        # Base estimate: 2 weeks per level
        base_weeks = levels_remaining * 2
        
        # Adjust based on trend
        if trend == 'improving':
            estimated_weeks = base_weeks * 0.8  # 20% faster
        elif trend == 'declining':
            estimated_weeks = base_weeks * 1.3  # 30% slower
        else:
            estimated_weeks = base_weeks

        if estimated_weeks < 4:
            return f"{int(estimated_weeks)} weeks"
        elif estimated_weeks < 12:
            return f"{int(estimated_weeks/4)} months"
        else:
            return f"{int(estimated_weeks/12)} quarters"