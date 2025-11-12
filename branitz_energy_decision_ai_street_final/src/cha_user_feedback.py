#!/usr/bin/env python3
"""
CHA User Feedback Collection System

This module provides comprehensive user feedback collection and analysis capabilities
for the CHA Intelligent Pipe Sizing System, including feedback collection, sentiment analysis,
and iterative improvement recommendations.
"""

import os
import json
import yaml
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics
from collections import defaultdict, Counter
import numpy as np

class FeedbackType(Enum):
    """Types of user feedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    PERFORMANCE_ISSUE = "performance_issue"
    USABILITY_ISSUE = "usability_issue"
    GENERAL_FEEDBACK = "general_feedback"
    SATISFACTION_SURVEY = "satisfaction_survey"

class FeedbackPriority(Enum):
    """Feedback priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeedbackStatus(Enum):
    """Feedback status."""
    NEW = "new"
    IN_REVIEW = "in_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"

class SentimentType(Enum):
    """Sentiment types."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

@dataclass
class UserFeedback:
    """User feedback entry."""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    title: str
    description: str
    priority: FeedbackPriority
    status: FeedbackStatus
    sentiment: SentimentType
    rating: Optional[int] = None  # 1-5 scale
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class FeedbackAnalysis:
    """Feedback analysis result."""
    analysis_id: str
    start_date: datetime
    end_date: datetime
    total_feedback: int
    feedback_by_type: Dict[str, int]
    feedback_by_priority: Dict[str, int]
    feedback_by_status: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    average_rating: float
    top_issues: List[Dict[str, Any]]
    improvement_recommendations: List[str]
    satisfaction_trends: Dict[str, Any]
    timestamp: datetime

class CHAUserFeedback:
    """User feedback collection and analysis system for CHA."""
    
    def __init__(self, config_path: str = "configs/user_feedback.yml"):
        """Initialize the user feedback system.
        
        Args:
            config_path: Path to user feedback configuration file
        """
        self.config_path = config_path
        self.feedback_entries: List[UserFeedback] = []
        self.feedback_callbacks: List[callable] = []
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Load existing feedback
        self._load_feedback()
    
    def _setup_logging(self):
        """Setup logging for user feedback."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self):
        """Load user feedback configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.logger.warning(f"User feedback configuration file not found: {self.config_path}")
                self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load user feedback configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default user feedback configuration."""
        self.config = {
            'feedback_categories': {
                'pipe_sizing': ['accuracy', 'performance', 'usability'],
                'flow_calculation': ['accuracy', 'performance', 'usability'],
                'network_analysis': ['accuracy', 'performance', 'usability'],
                'cost_analysis': ['accuracy', 'performance', 'usability'],
                'user_interface': ['usability', 'design', 'navigation'],
                'documentation': ['clarity', 'completeness', 'accuracy'],
                'performance': ['speed', 'memory', 'stability'],
                'integration': ['compatibility', 'ease_of_use', 'reliability']
            },
            'sentiment_keywords': {
                'positive': ['good', 'great', 'excellent', 'amazing', 'fantastic', 'love', 'perfect', 'awesome', 'brilliant', 'outstanding'],
                'negative': ['bad', 'terrible', 'awful', 'horrible', 'hate', 'disappointing', 'frustrating', 'annoying', 'broken', 'useless'],
                'neutral': ['okay', 'fine', 'average', 'normal', 'standard', 'acceptable', 'decent', 'reasonable', 'adequate', 'satisfactory']
            },
            'priority_keywords': {
                'critical': ['critical', 'urgent', 'emergency', 'broken', 'crash', 'error', 'fail', 'not working'],
                'high': ['important', 'major', 'significant', 'serious', 'problem', 'issue', 'bug', 'slow'],
                'medium': ['moderate', 'minor', 'small', 'suggestion', 'improvement', 'enhancement'],
                'low': ['nice to have', 'optional', 'future', 'wish', 'request', 'feature']
            },
            'feedback_templates': {
                'bug_report': {
                    'title': 'Bug Report: {component}',
                    'description': 'Describe the bug, steps to reproduce, and expected vs actual behavior.'
                },
                'feature_request': {
                    'title': 'Feature Request: {feature}',
                    'description': 'Describe the requested feature and its benefits.'
                },
                'performance_issue': {
                    'title': 'Performance Issue: {component}',
                    'description': 'Describe the performance issue and its impact.'
                },
                'usability_issue': {
                    'title': 'Usability Issue: {component}',
                    'description': 'Describe the usability issue and suggested improvements.'
                }
            }
        }
    
    def _load_feedback(self):
        """Load existing feedback from storage."""
        feedback_file = "data/user_feedback.json"
        try:
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                
                for entry_data in feedback_data:
                    feedback = UserFeedback(
                        feedback_id=entry_data['feedback_id'],
                        user_id=entry_data['user_id'],
                        feedback_type=FeedbackType(entry_data['feedback_type']),
                        title=entry_data['title'],
                        description=entry_data['description'],
                        priority=FeedbackPriority(entry_data['priority']),
                        status=FeedbackStatus(entry_data['status']),
                        sentiment=SentimentType(entry_data['sentiment']),
                        rating=entry_data.get('rating'),
                        tags=entry_data.get('tags', []),
                        metadata=entry_data.get('metadata', {}),
                        timestamp=datetime.fromisoformat(entry_data['timestamp']),
                        resolved_at=datetime.fromisoformat(entry_data['resolved_at']) if entry_data.get('resolved_at') else None,
                        resolution_notes=entry_data.get('resolution_notes')
                    )
                    self.feedback_entries.append(feedback)
                
                self.logger.info(f"Loaded {len(self.feedback_entries)} feedback entries")
                
        except Exception as e:
            self.logger.error(f"Failed to load feedback: {e}")
    
    def _save_feedback(self):
        """Save feedback to storage."""
        feedback_file = "data/user_feedback.json"
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
            
            feedback_data = []
            for feedback in self.feedback_entries:
                entry_data = asdict(feedback)
                entry_data['timestamp'] = feedback.timestamp.isoformat()
                if feedback.resolved_at:
                    entry_data['resolved_at'] = feedback.resolved_at.isoformat()
                feedback_data.append(entry_data)
            
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(self.feedback_entries)} feedback entries")
            
        except Exception as e:
            self.logger.error(f"Failed to save feedback: {e}")
    
    def submit_feedback(self, user_id: str, feedback_type: FeedbackType, title: str, 
                       description: str, rating: Optional[int] = None, 
                       tags: Optional[List[str]] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit user feedback.
        
        Args:
            user_id: User identifier
            feedback_type: Type of feedback
            title: Feedback title
            description: Feedback description
            rating: User rating (1-5 scale)
            tags: Feedback tags
            metadata: Additional metadata
            
        Returns:
            Feedback ID
        """
        # Generate feedback ID
        feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(description)
        
        # Determine priority
        priority = self._determine_priority(description, feedback_type)
        
        # Create feedback entry
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            feedback_type=feedback_type,
            title=title,
            description=description,
            priority=priority,
            status=FeedbackStatus.NEW,
            sentiment=sentiment,
            rating=rating,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Add to entries
        self.feedback_entries.append(feedback)
        
        # Save to storage
        self._save_feedback()
        
        # Call feedback callbacks
        for callback in self.feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                self.logger.error(f"Error in feedback callback: {e}")
        
        self.logger.info(f"Submitted feedback: {feedback_id}")
        return feedback_id
    
    def _analyze_sentiment(self, text: str) -> SentimentType:
        """Analyze sentiment of feedback text.
        
        Args:
            text: Feedback text
            
        Returns:
            Sentiment type
        """
        text_lower = text.lower()
        
        positive_keywords = self.config['sentiment_keywords']['positive']
        negative_keywords = self.config['sentiment_keywords']['negative']
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
        
        if positive_count > negative_count:
            return SentimentType.POSITIVE
        elif negative_count > positive_count:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL
    
    def _determine_priority(self, text: str, feedback_type: FeedbackType) -> FeedbackPriority:
        """Determine feedback priority based on content and type.
        
        Args:
            text: Feedback text
            feedback_type: Type of feedback
            
        Returns:
            Feedback priority
        """
        text_lower = text.lower()
        
        # Check for priority keywords
        for priority, keywords in self.config['priority_keywords'].items():
            if any(keyword in text_lower for keyword in keywords):
                return FeedbackPriority(priority.upper())
        
        # Default priority based on feedback type
        if feedback_type == FeedbackType.BUG_REPORT:
            return FeedbackPriority.HIGH
        elif feedback_type == FeedbackType.PERFORMANCE_ISSUE:
            return FeedbackPriority.HIGH
        elif feedback_type == FeedbackType.FEATURE_REQUEST:
            return FeedbackPriority.MEDIUM
        else:
            return FeedbackPriority.MEDIUM
    
    def get_feedback(self, feedback_id: str) -> Optional[UserFeedback]:
        """Get feedback by ID.
        
        Args:
            feedback_id: Feedback identifier
            
        Returns:
            Feedback entry or None
        """
        for feedback in self.feedback_entries:
            if feedback.feedback_id == feedback_id:
                return feedback
        return None
    
    def get_feedback_by_user(self, user_id: str) -> List[UserFeedback]:
        """Get all feedback from a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of feedback entries
        """
        return [feedback for feedback in self.feedback_entries if feedback.user_id == user_id]
    
    def get_feedback_by_type(self, feedback_type: FeedbackType) -> List[UserFeedback]:
        """Get all feedback of a specific type.
        
        Args:
            feedback_type: Feedback type
            
        Returns:
            List of feedback entries
        """
        return [feedback for feedback in self.feedback_entries if feedback.feedback_type == feedback_type]
    
    def get_feedback_by_status(self, status: FeedbackStatus) -> List[UserFeedback]:
        """Get all feedback with a specific status.
        
        Args:
            status: Feedback status
            
        Returns:
            List of feedback entries
        """
        return [feedback for feedback in self.feedback_entries if feedback.status == status]
    
    def get_feedback_by_priority(self, priority: FeedbackPriority) -> List[UserFeedback]:
        """Get all feedback with a specific priority.
        
        Args:
            priority: Feedback priority
            
        Returns:
            List of feedback entries
        """
        return [feedback for feedback in self.feedback_entries if feedback.priority == priority]
    
    def update_feedback_status(self, feedback_id: str, status: FeedbackStatus, 
                             resolution_notes: Optional[str] = None) -> bool:
        """Update feedback status.
        
        Args:
            feedback_id: Feedback identifier
            status: New status
            resolution_notes: Resolution notes
            
        Returns:
            True if updated, False otherwise
        """
        for feedback in self.feedback_entries:
            if feedback.feedback_id == feedback_id:
                feedback.status = status
                if status == FeedbackStatus.RESOLVED:
                    feedback.resolved_at = datetime.now()
                    feedback.resolution_notes = resolution_notes
                
                self._save_feedback()
                self.logger.info(f"Updated feedback status: {feedback_id} -> {status.value}")
                return True
        
        return False
    
    def add_feedback_callback(self, callback: callable):
        """Add a feedback callback function.
        
        Args:
            callback: Callback function to call when feedback is submitted
        """
        self.feedback_callbacks.append(callback)
    
    def analyze_feedback(self, start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> FeedbackAnalysis:
        """Analyze user feedback.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Feedback analysis result
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # Filter feedback by date range
        filtered_feedback = [
            f for f in self.feedback_entries
            if start_date <= f.timestamp <= end_date
        ]
        
        # Analyze feedback
        feedback_by_type = Counter([f.feedback_type.value for f in filtered_feedback])
        feedback_by_priority = Counter([f.priority.value for f in filtered_feedback])
        feedback_by_status = Counter([f.status.value for f in filtered_feedback])
        sentiment_distribution = Counter([f.sentiment.value for f in filtered_feedback])
        
        # Calculate average rating
        ratings = [f.rating for f in filtered_feedback if f.rating is not None]
        average_rating = statistics.mean(ratings) if ratings else 0.0
        
        # Identify top issues
        top_issues = self._identify_top_issues(filtered_feedback)
        
        # Generate improvement recommendations
        improvement_recommendations = self._generate_improvement_recommendations(filtered_feedback)
        
        # Analyze satisfaction trends
        satisfaction_trends = self._analyze_satisfaction_trends(filtered_feedback)
        
        analysis = FeedbackAnalysis(
            analysis_id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=start_date,
            end_date=end_date,
            total_feedback=len(filtered_feedback),
            feedback_by_type=dict(feedback_by_type),
            feedback_by_priority=dict(feedback_by_priority),
            feedback_by_status=dict(feedback_by_status),
            sentiment_distribution=dict(sentiment_distribution),
            average_rating=average_rating,
            top_issues=top_issues,
            improvement_recommendations=improvement_recommendations,
            satisfaction_trends=satisfaction_trends,
            timestamp=datetime.now()
        )
        
        return analysis
    
    def _identify_top_issues(self, feedback: List[UserFeedback]) -> List[Dict[str, Any]]:
        """Identify top issues from feedback.
        
        Args:
            feedback: List of feedback entries
            
        Returns:
            List of top issues
        """
        # Group feedback by tags and keywords
        issue_counts = defaultdict(int)
        issue_descriptions = defaultdict(list)
        
        for entry in feedback:
            # Extract keywords from title and description
            text = f"{entry.title} {entry.description}".lower()
            
            # Check for common issue keywords
            issue_keywords = [
                'slow', 'performance', 'error', 'bug', 'crash', 'freeze', 'hang',
                'memory', 'cpu', 'disk', 'network', 'connection', 'timeout',
                'interface', 'ui', 'ux', 'usability', 'confusing', 'difficult',
                'documentation', 'help', 'tutorial', 'guide', 'example'
            ]
            
            for keyword in issue_keywords:
                if keyword in text:
                    issue_counts[keyword] += 1
                    issue_descriptions[keyword].append(entry.description[:100])
        
        # Sort by count and return top issues
        top_issues = []
        for keyword, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_issues.append({
                'keyword': keyword,
                'count': count,
                'percentage': (count / len(feedback)) * 100,
                'sample_descriptions': issue_descriptions[keyword][:3]
            })
        
        return top_issues
    
    def _generate_improvement_recommendations(self, feedback: List[UserFeedback]) -> List[str]:
        """Generate improvement recommendations from feedback.
        
        Args:
            feedback: List of feedback entries
            
        Returns:
            List of improvement recommendations
        """
        recommendations = []
        
        # Analyze feedback patterns
        negative_feedback = [f for f in feedback if f.sentiment == SentimentType.NEGATIVE]
        high_priority_feedback = [f for f in feedback if f.priority == FeedbackPriority.HIGH]
        
        # Performance-related recommendations
        performance_issues = [f for f in negative_feedback if 'performance' in f.description.lower() or 'slow' in f.description.lower()]
        if len(performance_issues) > len(feedback) * 0.2:
            recommendations.append("Performance optimization needed - multiple users reporting slow performance")
        
        # Usability-related recommendations
        usability_issues = [f for f in negative_feedback if any(word in f.description.lower() for word in ['confusing', 'difficult', 'hard', 'complex'])]
        if len(usability_issues) > len(feedback) * 0.15:
            recommendations.append("Usability improvements needed - users finding the interface confusing")
        
        # Documentation-related recommendations
        doc_issues = [f for f in feedback if any(word in f.description.lower() for word in ['documentation', 'help', 'tutorial', 'guide'])]
        if len(doc_issues) > len(feedback) * 0.1:
            recommendations.append("Documentation improvements needed - users requesting better help and guides")
        
        # Feature-related recommendations
        feature_requests = [f for f in feedback if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        if len(feature_requests) > len(feedback) * 0.3:
            recommendations.append("Consider implementing frequently requested features")
        
        # Bug-related recommendations
        bug_reports = [f for f in feedback if f.feedback_type == FeedbackType.BUG_REPORT]
        if len(bug_reports) > len(feedback) * 0.2:
            recommendations.append("Bug fixes needed - multiple bug reports received")
        
        return recommendations
    
    def _analyze_satisfaction_trends(self, feedback: List[UserFeedback]) -> Dict[str, Any]:
        """Analyze satisfaction trends over time.
        
        Args:
            feedback: List of feedback entries
            
        Returns:
            Satisfaction trends analysis
        """
        if not feedback:
            return {}
        
        # Group feedback by week
        weekly_feedback = defaultdict(list)
        for entry in feedback:
            week_start = entry.timestamp - timedelta(days=entry.timestamp.weekday())
            weekly_feedback[week_start.strftime('%Y-%m-%d')].append(entry)
        
        # Calculate weekly satisfaction metrics
        weekly_metrics = {}
        for week, week_feedback in weekly_feedback.items():
            ratings = [f.rating for f in week_feedback if f.rating is not None]
            sentiments = [f.sentiment for f in week_feedback]
            
            weekly_metrics[week] = {
                'total_feedback': len(week_feedback),
                'average_rating': statistics.mean(ratings) if ratings else 0.0,
                'positive_sentiment_ratio': sentiments.count(SentimentType.POSITIVE) / len(sentiments) if sentiments else 0.0,
                'negative_sentiment_ratio': sentiments.count(SentimentType.NEGATIVE) / len(sentiments) if sentiments else 0.0
            }
        
        return weekly_metrics
    
    def generate_feedback_report(self, analysis: FeedbackAnalysis, 
                               output_path: Optional[str] = None) -> str:
        """Generate a feedback report.
        
        Args:
            analysis: Feedback analysis result
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            output_path = f"reports/feedback_report_{analysis.analysis_id}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(asdict(analysis), f, indent=2, default=str)
        
        self.logger.info(f"Generated feedback report: {output_path}")
        return output_path
    
    def export_feedback(self, output_path: str, format: str = "json"):
        """Export feedback data.
        
        Args:
            output_path: Path to save the export
            format: Export format ("json", "csv")
        """
        if format == "json":
            feedback_data = []
            for feedback in self.feedback_entries:
                entry_data = asdict(feedback)
                entry_data['timestamp'] = feedback.timestamp.isoformat()
                if feedback.resolved_at:
                    entry_data['resolved_at'] = feedback.resolved_at.isoformat()
                feedback_data.append(entry_data)
            
            with open(output_path, 'w') as f:
                json.dump(feedback_data, f, indent=2, default=str)
        
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'feedback_id', 'user_id', 'feedback_type', 'title', 'description',
                    'priority', 'status', 'sentiment', 'rating', 'tags', 'timestamp'
                ])
                
                for feedback in self.feedback_entries:
                    writer.writerow([
                        feedback.feedback_id, feedback.user_id, feedback.feedback_type.value,
                        feedback.title, feedback.description, feedback.priority.value,
                        feedback.status.value, feedback.sentiment.value, feedback.rating,
                        ','.join(feedback.tags), feedback.timestamp.isoformat()
                    ])
        
        self.logger.info(f"Exported feedback to {output_path}")

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA User Feedback System')
    parser.add_argument('--config', default='configs/user_feedback.yml', help='User feedback configuration file')
    parser.add_argument('--action', choices=['submit', 'list', 'analyze', 'export'], required=True, help='Action to perform')
    parser.add_argument('--user-id', help='User identifier')
    parser.add_argument('--feedback-type', help='Feedback type')
    parser.add_argument('--title', help='Feedback title')
    parser.add_argument('--description', help='Feedback description')
    parser.add_argument('--rating', type=int, help='User rating (1-5)')
    parser.add_argument('--status', help='Feedback status')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    args = parser.parse_args()
    
    # Initialize user feedback system
    feedback_system = CHAUserFeedback(args.config)
    
    if args.action == 'submit':
        if not all([args.user_id, args.feedback_type, args.title, args.description]):
            print("Error: --user-id, --feedback-type, --title, and --description are required for submit action")
            return 1
        
        feedback_id = feedback_system.submit_feedback(
            user_id=args.user_id,
            feedback_type=FeedbackType(args.feedback_type),
            title=args.title,
            description=args.description,
            rating=args.rating
        )
        print(f"✅ Submitted feedback: {feedback_id}")
    
    elif args.action == 'list':
        feedback_entries = feedback_system.feedback_entries
        print(f"📋 User Feedback ({len(feedback_entries)}):")
        for feedback in feedback_entries[-10:]:  # Show last 10
            print(f"  {feedback.feedback_id}: {feedback.title} ({feedback.status.value})")
    
    elif args.action == 'analyze':
        analysis = feedback_system.analyze_feedback()
        output_path = feedback_system.generate_feedback_report(analysis, args.output)
        print(f"✅ Generated feedback analysis: {output_path}")
        print(f"   Total feedback: {analysis.total_feedback}")
        print(f"   Average rating: {analysis.average_rating:.2f}")
        print(f"   Top issues: {len(analysis.top_issues)}")
        print(f"   Recommendations: {len(analysis.improvement_recommendations)}")
    
    elif args.action == 'export':
        if not args.output:
            print("Error: --output is required for export action")
            return 1
        
        feedback_system.export_feedback(args.output, args.format)
        print(f"✅ Exported feedback to {args.output}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
