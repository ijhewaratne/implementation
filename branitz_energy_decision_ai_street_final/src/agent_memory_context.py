#!/usr/bin/env python3
"""
ADK Agent Memory and Context Management
Advanced memory and context systems for ADK agents with persistence and learning capabilities.
"""

import os
import sys
import json
import pickle
import sqlite3
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Memory entry data structure."""
    id: str
    timestamp: datetime
    request: str
    response: str
    context: Dict[str, Any]
    performance_metrics: Dict[str, float]
    user_feedback: Optional[str] = None
    tags: List[str] = None
    importance_score: float = 0.0

@dataclass
class ContextSnapshot:
    """Context snapshot data structure."""
    timestamp: datetime
    conversation_state: Dict[str, Any]
    user_state: Dict[str, Any]
    system_state: Dict[str, Any]
    analysis_context: Dict[str, Any]

class SessionMemory:
    """Session-based memory management."""
    
    def __init__(self, session_id: str, max_entries: int = 1000):
        self.session_id = session_id
        self.max_entries = max_entries
        self.memories: deque = deque(maxlen=max_entries)
        self.memory_index: Dict[str, List[int]] = defaultdict(list)
        self.current_context: Dict[str, Any] = {}
    
    def add_memory(self, memory: MemoryEntry):
        """Add memory entry to session."""
        self.memories.append(memory)
        self._index_memory(len(self.memories) - 1)
    
    def get_recent_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories from session."""
        return list(self.memories)[-limit:]
    
    def get_memories_by_tags(self, tags: List[str]) -> List[MemoryEntry]:
        """Get memories by tags."""
        matching_memories = []
        for memory in self.memories:
            if memory.tags and any(tag in memory.tags for tag in tags):
                matching_memories.append(memory)
        return matching_memories
    
    def get_context(self) -> Dict[str, Any]:
        """Get current session context."""
        return self.current_context.copy()
    
    def update_context(self, context_updates: Dict[str, Any]):
        """Update session context."""
        self.current_context.update(context_updates)
    
    def _index_memory(self, index: int):
        """Index memory for fast retrieval."""
        memory = self.memories[index]
        if memory.tags:
            for tag in memory.tags:
                self.memory_index[tag].append(index)

class LearningMemory:
    """Learning-based memory system."""
    
    def __init__(self, learning_db_path: str = "data/learning_memory.db"):
        self.learning_db_path = Path(learning_db_path)
        self.learning_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.pattern_cache: Dict[str, Any] = {}
        self.learning_models: Dict[str, Any] = {}
    
    def _init_database(self):
        """Initialize learning database."""
        with sqlite3.connect(self.learning_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    success_rate REAL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def update_patterns(self, request: str, result: Dict[str, Any]):
        """Update learning patterns."""
        pattern_type = self._classify_pattern_type(request)
        pattern_data = self._extract_pattern_data(request, result)
        
        with sqlite3.connect(self.learning_db_path) as conn:
            # Check if pattern exists
            cursor = conn.execute(
                'SELECT id, success_rate, usage_count FROM learning_patterns WHERE pattern_type = ? AND pattern_data = ?',
                (pattern_type, json.dumps(pattern_data))
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pattern
                pattern_id, current_success_rate, usage_count = existing
                new_success_rate = (current_success_rate * usage_count + (1.0 if result.get('success', False) else 0.0)) / (usage_count + 1)
                
                conn.execute(
                    'UPDATE learning_patterns SET success_rate = ?, usage_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (new_success_rate, usage_count + 1, pattern_id)
                )
            else:
                # Insert new pattern
                success_rate = 1.0 if result.get('success', False) else 0.0
                conn.execute(
                    'INSERT INTO learning_patterns (pattern_type, pattern_data, success_rate, usage_count) VALUES (?, ?, ?, 1)',
                    (pattern_type, json.dumps(pattern_data), success_rate)
                )
    
    def get_relevant_patterns(self, request: str) -> List[Dict[str, Any]]:
        """Get relevant patterns for request."""
        pattern_type = self._classify_pattern_type(request)
        
        with sqlite3.connect(self.learning_db_path) as conn:
            cursor = conn.execute(
                'SELECT pattern_data, success_rate, usage_count FROM learning_patterns WHERE pattern_type = ? ORDER BY success_rate DESC, usage_count DESC LIMIT 5',
                (pattern_type,)
            )
            
            patterns = []
            for row in cursor.fetchall():
                pattern_data, success_rate, usage_count = row
                patterns.append({
                    'pattern_data': json.loads(pattern_data),
                    'success_rate': success_rate,
                    'usage_count': usage_count
                })
            
            return patterns
    
    def _classify_pattern_type(self, request: str) -> str:
        """Classify pattern type from request."""
        request_lower = request.lower()
        
        if 'district heating' in request_lower:
            return 'district_heating_analysis'
        elif 'heat pump' in request_lower:
            return 'heat_pump_analysis'
        elif 'compare' in request_lower:
            return 'scenario_comparison'
        elif 'analyze' in request_lower:
            return 'general_analysis'
        else:
            return 'general_interaction'
    
    def _extract_pattern_data(self, request: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pattern data from request and result."""
        return {
            'request_length': len(request),
            'request_words': len(request.split()),
            'has_specific_street': any(word.isupper() for word in request.split()),
            'response_length': len(str(result.get('agent_response', ''))),
            'success': result.get('success', False),
            'response_time': result.get('response_time', 0)
        }

class UserProfiles:
    """User profile management system."""
    
    def __init__(self, profiles_db_path: str = "data/user_profiles.db"):
        self.profiles_db_path = Path(profiles_db_path)
        self.profiles_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.active_profiles: Dict[str, Dict[str, Any]] = {}
    
    def _init_database(self):
        """Initialize user profiles database."""
        with sqlite3.connect(self.profiles_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,
                    interaction_history TEXT,
                    performance_metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def get_user_preferences(self, user_id: str = "default") -> Dict[str, Any]:
        """Get user preferences."""
        # Check active profiles first
        if user_id in self.active_profiles:
            return self.active_profiles[user_id].get('preferences', {})
        
        # Load from database
        with sqlite3.connect(self.profiles_db_path) as conn:
            cursor = conn.execute(
                'SELECT preferences FROM user_profiles WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                preferences = json.loads(row[0])
            else:
                preferences = self._get_default_preferences()
                self._save_user_preferences(user_id, preferences)
            
            # Cache in active profiles
            if user_id not in self.active_profiles:
                self.active_profiles[user_id] = {}
            self.active_profiles[user_id]['preferences'] = preferences
            
            return preferences
    
    def update_preferences(self, user_id: str, request: str, result: Dict[str, Any]):
        """Update user preferences based on interaction."""
        preferences = self.get_user_preferences(user_id)
        
        # Update preferences based on interaction patterns
        self._update_preferences_from_interaction(preferences, request, result)
        
        # Save updated preferences
        self._save_user_preferences(user_id, preferences)
        
        # Update active profile
        if user_id in self.active_profiles:
            self.active_profiles[user_id]['preferences'] = preferences
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences."""
        return {
            'detail_level': 'medium',
            'preferred_analysis_type': 'auto',
            'response_format': 'comprehensive',
            'visualization_preference': 'interactive',
            'notification_preferences': {
                'email_notifications': False,
                'progress_updates': True
            },
            'accessibility_preferences': {
                'high_contrast': False,
                'large_text': False
            }
        }
    
    def _update_preferences_from_interaction(self, preferences: Dict[str, Any], request: str, result: Dict[str, Any]):
        """Update preferences based on interaction."""
        # Update detail level preference
        response_length = len(str(result.get('agent_response', '')))
        if response_length > 1000:
            preferences['detail_level'] = 'high'
        elif response_length < 300:
            preferences['detail_level'] = 'low'
        
        # Update analysis type preference
        request_lower = request.lower()
        if 'district heating' in request_lower:
            preferences['preferred_analysis_type'] = 'district_heating'
        elif 'heat pump' in request_lower:
            preferences['preferred_analysis_type'] = 'heat_pump'
        
        # Update response format preference
        if 'summary' in request_lower or 'brief' in request_lower:
            preferences['response_format'] = 'summary'
        elif 'detailed' in request_lower or 'comprehensive' in request_lower:
            preferences['response_format'] = 'comprehensive'
    
    def _save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user preferences to database."""
        with sqlite3.connect(self.profiles_db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO user_profiles (user_id, preferences, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                (user_id, json.dumps(preferences))
            )

class ContextPersistence:
    """Context persistence and retrieval system."""
    
    def __init__(self, context_db_path: str = "data/context_persistence.db"):
        self.context_db_path = Path(context_db_path)
        self.context_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.context_cache: Dict[str, ContextSnapshot] = {}
    
    def _init_database(self):
        """Initialize context database."""
        with sqlite3.connect(self.context_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_key TEXT NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_context_key ON context_snapshots(context_key);
            ''')
    
    def save_context(self, context_key: str, context_data: Dict[str, Any]):
        """Save context snapshot."""
        snapshot = ContextSnapshot(
            timestamp=datetime.now(),
            conversation_state=context_data.get('conversation_state', {}),
            user_state=context_data.get('user_state', {}),
            system_state=context_data.get('system_state', {}),
            analysis_context=context_data.get('analysis_context', {})
        )
        
        # Save to database
        with sqlite3.connect(self.context_db_path) as conn:
            # Convert datetime to string for JSON serialization
            snapshot_dict = asdict(snapshot)
            snapshot_dict['timestamp'] = snapshot_dict['timestamp'].isoformat()
            
            conn.execute(
                'INSERT INTO context_snapshots (context_key, snapshot_data) VALUES (?, ?)',
                (context_key, json.dumps(snapshot_dict))
            )
        
        # Cache in memory
        self.context_cache[context_key] = snapshot
    
    def get_historical_context(self, context_key: str) -> Optional[ContextSnapshot]:
        """Get historical context."""
        # Check cache first
        if context_key in self.context_cache:
            return self.context_cache[context_key]
        
        # Load from database
        with sqlite3.connect(self.context_db_path) as conn:
            cursor = conn.execute(
                'SELECT snapshot_data FROM context_snapshots WHERE context_key = ? ORDER BY created_at DESC LIMIT 1',
                (context_key,)
            )
            row = cursor.fetchone()
            
            if row:
                snapshot_data = json.loads(row[0])
                snapshot = ContextSnapshot(**snapshot_data)
                self.context_cache[context_key] = snapshot
                return snapshot
        
        return None
    
    def get_similar_contexts(self, context_key: str, limit: int = 5) -> List[ContextSnapshot]:
        """Get similar historical contexts."""
        # Simple similarity based on key prefix matching
        with sqlite3.connect(self.context_db_path) as conn:
            cursor = conn.execute(
                'SELECT snapshot_data FROM context_snapshots WHERE context_key LIKE ? ORDER BY created_at DESC LIMIT ?',
                (f"{context_key}%", limit)
            )
            
            similar_contexts = []
            for row in cursor.fetchall():
                snapshot_data = json.loads(row[0])
                snapshot = ContextSnapshot(**snapshot_data)
                similar_contexts.append(snapshot)
            
            return similar_contexts

class ConversationContext:
    """Conversation context management."""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.conversation_history: deque = deque(maxlen=max_history)
        self.current_topic: Optional[str] = None
        self.conversation_flow: List[str] = []
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return {
            'conversation_history': list(self.conversation_history),
            'current_topic': self.current_topic,
            'conversation_flow': self.conversation_flow,
            'total_interactions': len(self.conversation_history),
            'history_length': len(self.conversation_history)
        }
    
    def add_interaction(self, request: str, response: str, metadata: Dict = None):
        """Add interaction to conversation history."""
        interaction = {
            'request': request,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(interaction)
        self._update_conversation_flow(request)
        self._update_current_topic(request)
    
    def _update_conversation_flow(self, request: str):
        """Update conversation flow patterns."""
        request_type = self._classify_request_type(request)
        self.conversation_flow.append(request_type)
        
        # Keep only recent flow
        if len(self.conversation_flow) > 20:
            self.conversation_flow = self.conversation_flow[-20:]
    
    def _update_current_topic(self, request: str):
        """Update current conversation topic."""
        request_lower = request.lower()
        
        if 'district heating' in request_lower:
            self.current_topic = 'district_heating'
        elif 'heat pump' in request_lower:
            self.current_topic = 'heat_pump'
        elif 'compare' in request_lower:
            self.current_topic = 'comparison'
        elif 'analyze' in request_lower:
            self.current_topic = 'analysis'
        else:
            self.current_topic = 'general'
    
    def _classify_request_type(self, request: str) -> str:
        """Classify request type."""
        request_lower = request.lower()
        
        if any(keyword in request_lower for keyword in ['analyze', 'analysis']):
            return 'analysis'
        elif any(keyword in request_lower for keyword in ['compare', 'comparison']):
            return 'comparison'
        elif any(keyword in request_lower for keyword in ['show', 'list', 'display']):
            return 'exploration'
        elif any(keyword in request_lower for keyword in ['help', 'guide']):
            return 'help'
        else:
            return 'general'

class AnalysisContext:
    """Analysis context management."""
    
    def __init__(self):
        self.current_analysis: Optional[Dict[str, Any]] = None
        self.analysis_history: List[Dict[str, Any]] = []
        self.analysis_parameters: Dict[str, Any] = {}
    
    def get_context(self) -> Dict[str, Any]:
        """Get current analysis context."""
        return {
            'current_analysis': self.current_analysis,
            'analysis_history': self.analysis_history,
            'analysis_parameters': self.analysis_parameters,
            'history_length': len(self.analysis_history)
        }
    
    def start_analysis(self, analysis_type: str, parameters: Dict[str, Any]):
        """Start new analysis."""
        self.current_analysis = {
            'type': analysis_type,
            'parameters': parameters,
            'start_time': datetime.now().isoformat(),
            'status': 'in_progress'
        }
        
        self.analysis_parameters.update(parameters)
    
    def complete_analysis(self, results: Dict[str, Any]):
        """Complete current analysis."""
        if self.current_analysis:
            self.current_analysis.update({
                'end_time': datetime.now().isoformat(),
                'status': 'completed',
                'results': results
            })
            
            self.analysis_history.append(self.current_analysis.copy())
            self.current_analysis = None
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        if not self.analysis_history:
            return {'status': 'no_analyses'}
        
        recent_analyses = self.analysis_history[-10:]  # Last 10 analyses
        
        analysis_types = [analysis['type'] for analysis in recent_analyses]
        type_counts = {atype: analysis_types.count(atype) for atype in set(analysis_types)}
        
        return {
            'active_analyses': 1 if self.current_analysis else 0,
            'analysis_history': len(self.analysis_history),
            'current_analysis': self.current_analysis,
            'total_analyses': len(self.analysis_history),
            'recent_analyses': len(recent_analyses),
            'analysis_types': type_counts,
            'most_common_type': max(type_counts, key=type_counts.get) if type_counts else None
        }

class UserContext:
    """User context management."""
    
    def __init__(self):
        self.user_id: Optional[str] = None
        self.user_session: Dict[str, Any] = {}
        self.user_goals: List[str] = []
        self.user_constraints: Dict[str, Any] = {}
    
    def get_context(self) -> Dict[str, Any]:
        """Get current user context."""
        return {
            'user_id': self.user_id,
            'user_session': self.user_session,
            'user_goals': self.user_goals,
            'user_constraints': self.user_constraints
        }
    
    def set_user(self, user_id: str, session_data: Dict[str, Any] = None):
        """Set current user."""
        self.user_id = user_id
        self.user_session = session_data or {}
    
    def add_goal(self, goal: str):
        """Add user goal."""
        if goal not in self.user_goals:
            self.user_goals.append(goal)
    
    def add_constraint(self, constraint_type: str, constraint_value: Any):
        """Add user constraint."""
        self.user_constraints[constraint_type] = constraint_value

class SystemContext:
    """System context management."""
    
    def __init__(self):
        self.system_state: Dict[str, Any] = {}
        self.resource_usage: Dict[str, float] = {}
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.system_health: Dict[str, Any] = {}
    
    def get_context(self) -> Dict[str, Any]:
        """Get current system context."""
        return {
            'system_state': self.system_state,
            'resource_usage': self.resource_usage,
            'performance_metrics': dict(self.performance_metrics),
            'system_health': self.system_health
        }
    
    def update_system_state(self, state_updates: Dict[str, Any]):
        """Update system state."""
        self.system_state.update(state_updates)
    
    def update_resource_usage(self, resource_type: str, usage: float):
        """Update resource usage."""
        self.resource_usage[resource_type] = usage
    
    def add_performance_metric(self, metric_type: str, value: float):
        """Add performance metric."""
        self.performance_metrics[metric_type].append(value)
        
        # Keep only recent metrics
        if len(self.performance_metrics[metric_type]) > 100:
            self.performance_metrics[metric_type] = self.performance_metrics[metric_type][-100:]
    
    def update_system_health(self, health_data: Dict[str, Any]):
        """Update system health."""
        self.system_health.update(health_data)

class AgentMemory:
    """Advanced agent memory system."""
    
    def __init__(self, session_id: str = "default", memory_config: Dict[str, Any] = None):
        self.session_id = session_id
        self.memory_config = memory_config or {}
        
        # Initialize memory components
        self.session_memory = SessionMemory(session_id, max_entries=self.memory_config.get('max_session_entries', 1000))
        self.learning_memory = LearningMemory(self.memory_config.get('learning_db_path', 'data/learning_memory.db'))
        self.user_profiles = UserProfiles(self.memory_config.get('profiles_db_path', 'data/user_profiles.db'))
        self.context_persistence = ContextPersistence(self.memory_config.get('context_db_path', 'data/context_persistence.db'))
        
        # Memory statistics
        self.memory_stats = {
            'total_memories': 0,
            'session_memories': 0,
            'learning_patterns': 0,
            'user_preferences': 0,
            'context_snapshots': 0
        }
        
        logger.info(f"Initialized AgentMemory for session: {session_id}")
    
    def get_relevant_memory(self, request: str, user_id: str = "default") -> Dict:
        """Get relevant memory for request."""
        try:
            # 1. Session context
            session_context = self.session_memory.get_context()
            
            # 2. Learning patterns
            learned_patterns = self.learning_memory.get_relevant_patterns(request)
            
            # 3. User preferences
            user_preferences = self.user_profiles.get_user_preferences(user_id)
            
            # 4. Historical context
            historical_context = self.context_persistence.get_historical_context(request)
            
            # 5. Recent memories
            recent_memories = self.session_memory.get_recent_memories(limit=5)
            
            # 6. Tagged memories
            request_tags = self._extract_request_tags(request)
            tagged_memories = self.session_memory.get_memories_by_tags(request_tags) if request_tags else []
            
            relevant_memory = {
                'session': session_context,
                'patterns': learned_patterns,
                'preferences': user_preferences,
                'historical': historical_context,
                'recent_memories': [asdict(memory) for memory in recent_memories],
                'tagged_memories': [asdict(memory) for memory in tagged_memories],
                'request_tags': request_tags,
                'memory_stats': self.memory_stats.copy()
            }
            
            return relevant_memory
            
        except Exception as e:
            logger.error(f"Error getting relevant memory: {e}")
            return {
                'session': {},
                'patterns': [],
                'preferences': {},
                'historical': None,
                'recent_memories': [],
                'tagged_memories': [],
                'request_tags': [],
                'memory_stats': self.memory_stats.copy(),
                'error': str(e)
            }
    
    def update_memory(self, request: str, result: Dict, user_id: str = "default", metadata: Dict = None):
        """Update memory with new information."""
        try:
            # Create memory entry
            memory_entry = MemoryEntry(
                id=f"{self.session_id}_{int(time.time() * 1000)}",
                timestamp=datetime.now(),
                request=request,
                response=str(result.get('agent_response', '')),
                context={
                    'user_id': user_id,
                    'session_id': self.session_id,
                    'metadata': metadata or {}
                },
                performance_metrics={
                    'response_time': result.get('response_time', 0),
                    'success': result.get('success', False)
                },
                tags=self._extract_request_tags(request),
                importance_score=self._calculate_importance_score(request, result)
            )
            
            # 1. Update session memory
            self.session_memory.add_memory(memory_entry)
            self.memory_stats['session_memories'] += 1
            
            # 2. Update learning memory
            self.learning_memory.update_patterns(request, result)
            self.memory_stats['learning_patterns'] += 1
            
            # 3. Update user profile
            self.user_profiles.update_preferences(user_id, request, result)
            self.memory_stats['user_preferences'] += 1
            
            # 4. Persist context
            context_data = {
                'conversation_state': {'last_request': request, 'last_response': str(result.get('agent_response', ''))},
                'user_state': {'user_id': user_id, 'session_id': self.session_id},
                'system_state': {'timestamp': datetime.now().isoformat()},
                'analysis_context': {'request_type': self._classify_request_type(request)}
            }
            self.context_persistence.save_context(request, context_data)
            self.memory_stats['context_snapshots'] += 1
            
            # Update total memory count
            self.memory_stats['total_memories'] += 1
            
            logger.info(f"Updated memory for request: {request[:50]}...")
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
    
    def _extract_request_tags(self, request: str) -> List[str]:
        """Extract relevant tags from request."""
        tags = []
        request_lower = request.lower()
        
        # Analysis type tags
        if 'district heating' in request_lower:
            tags.append('district_heating')
        if 'heat pump' in request_lower:
            tags.append('heat_pump')
        if 'compare' in request_lower:
            tags.append('comparison')
        if 'analyze' in request_lower:
            tags.append('analysis')
        if 'show' in request_lower or 'list' in request_lower:
            tags.append('exploration')
        
        # Complexity tags
        word_count = len(request.split())
        if word_count < 5:
            tags.append('simple')
        elif word_count < 15:
            tags.append('medium')
        else:
            tags.append('complex')
        
        # Street-specific tags
        import re
        street_pattern = r'\b[A-Z][a-z]+straße\b'
        streets = re.findall(street_pattern, request)
        if streets:
            tags.extend([f'street_{street.lower()}' for street in streets])
        
        return tags
    
    def _calculate_importance_score(self, request: str, result: Dict) -> float:
        """Calculate importance score for memory entry."""
        score = 0.0
        
        # Base score
        score += 0.1
        
        # Success bonus
        if result.get('success', False):
            score += 0.2
        
        # Response length bonus
        response_length = len(str(result.get('agent_response', '')))
        if response_length > 1000:
            score += 0.3
        elif response_length > 500:
            score += 0.2
        elif response_length > 100:
            score += 0.1
        
        # Request complexity bonus
        word_count = len(request.split())
        if word_count > 20:
            score += 0.2
        elif word_count > 10:
            score += 0.1
        
        # Analysis type bonus
        request_lower = request.lower()
        if any(keyword in request_lower for keyword in ['comprehensive', 'detailed', 'complete']):
            score += 0.2
        
        # Street-specific bonus
        if any(street in request for street in ['Parkstraße', 'Hauptstraße', 'Bahnhofstraße']):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _classify_request_type(self, request: str) -> str:
        """Classify request type."""
        request_lower = request.lower()
        
        if 'district heating' in request_lower:
            return 'district_heating_analysis'
        elif 'heat pump' in request_lower:
            return 'heat_pump_analysis'
        elif 'compare' in request_lower:
            return 'scenario_comparison'
        elif 'analyze' in request_lower:
            return 'general_analysis'
        elif 'show' in request_lower or 'list' in request_lower:
            return 'data_exploration'
        else:
            return 'general_interaction'
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory summary."""
        return {
            'session_id': self.session_id,
            'memory_stats': self.memory_stats.copy(),
            'session_memory_count': len(self.session_memory.memories),
            'learning_patterns_count': len(self.learning_memory.pattern_cache),
            'user_profiles_count': len(self.user_profiles.active_profiles),
            'context_snapshots_count': len(self.context_persistence.context_cache),
            'recent_activity': self._get_recent_activity(),
            'memory_health': self._assess_memory_health()
        }
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent memory activity."""
        recent_memories = self.session_memory.get_recent_memories(limit=10)
        
        if not recent_memories:
            return {'status': 'no_recent_activity'}
        
        # Analyze recent activity
        request_types = [self._classify_request_type(memory.request) for memory in recent_memories]
        type_counts = {req_type: request_types.count(req_type) for req_type in set(request_types)}
        
        avg_importance = sum(memory.importance_score for memory in recent_memories) / len(recent_memories)
        
        return {
            'total_recent_memories': len(recent_memories),
            'request_type_distribution': type_counts,
            'average_importance_score': avg_importance,
            'most_common_type': max(type_counts, key=type_counts.get) if type_counts else None,
            'recent_timestamp': recent_memories[-1].timestamp.isoformat() if recent_memories else None
        }
    
    def _assess_memory_health(self) -> Dict[str, Any]:
        """Assess memory system health."""
        health_score = 0.0
        issues = []
        
        # Check session memory
        if len(self.session_memory.memories) > 0:
            health_score += 0.3
        else:
            issues.append("No session memories")
        
        # Check learning patterns
        if len(self.learning_memory.pattern_cache) > 0:
            health_score += 0.3
        else:
            issues.append("No learning patterns")
        
        # Check user profiles
        if len(self.user_profiles.active_profiles) > 0:
            health_score += 0.2
        else:
            issues.append("No user profiles")
        
        # Check context persistence
        if len(self.context_persistence.context_cache) > 0:
            health_score += 0.2
        else:
            issues.append("No context snapshots")
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 0.7 else 'needs_attention' if health_score > 0.3 else 'unhealthy',
            'issues': issues,
            'recommendations': self._get_health_recommendations(health_score, issues)
        }
    
    def _get_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Get health improvement recommendations."""
        recommendations = []
        
        if health_score < 0.7:
            recommendations.append("Consider increasing memory usage to improve system learning")
        
        if "No session memories" in issues:
            recommendations.append("Start using the system to build session memory")
        
        if "No learning patterns" in issues:
            recommendations.append("Perform more diverse analyses to build learning patterns")
        
        if "No user profiles" in issues:
            recommendations.append("Enable user profiling for personalized experiences")
        
        if "No context snapshots" in issues:
            recommendations.append("Enable context persistence for better continuity")
        
        return recommendations
    
    def clear_memory(self, memory_type: str = "all"):
        """Clear specific type of memory."""
        try:
            if memory_type in ["all", "session"]:
                self.session_memory.memories.clear()
                self.session_memory.memory_index.clear()
                logger.info("Cleared session memory")
            
            if memory_type in ["all", "learning"]:
                # Clear learning memory cache
                self.learning_memory.pattern_cache.clear()
                logger.info("Cleared learning memory cache")
            
            if memory_type in ["all", "profiles"]:
                # Clear active user profiles
                self.user_profiles.active_profiles.clear()
                logger.info("Cleared active user profiles")
            
            if memory_type in ["all", "context"]:
                # Clear context cache
                self.context_persistence.context_cache.clear()
                logger.info("Cleared context cache")
            
            # Reset stats
            self.memory_stats = {
                'total_memories': 0,
                'session_memories': 0,
                'learning_patterns': 0,
                'user_preferences': 0,
                'context_snapshots': 0
            }
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")

class AgentContext:
    """Advanced agent context management."""
    
    def __init__(self, context_config: Dict[str, Any] = None):
        self.context_config = context_config or {}
        
        # Initialize context components
        self.conversation_context = ConversationContext(
            max_history=self.context_config.get('max_conversation_history', 50)
        )
        self.analysis_context = AnalysisContext()
        self.user_context = UserContext()
        self.system_context = SystemContext()
        
        # Context statistics
        self.context_stats = {
            'total_context_updates': 0,
            'conversation_updates': 0,
            'analysis_updates': 0,
            'user_updates': 0,
            'system_updates': 0
        }
        
        logger.info("Initialized AgentContext")
    
    def enhance_context(self, request: str, additional_context: Dict = None) -> Dict:
        """Enhance context with advanced information."""
        try:
            # Get context from all components
            conversation_context = self.conversation_context.get_context()
            analysis_context = self.analysis_context.get_context()
            user_context = self.user_context.get_context()
            system_context = self.system_context.get_context()
            
            # Create enhanced context
            enhanced_context = {
                'conversation': conversation_context,
                'analysis': analysis_context,
                'user': user_context,
                'system': system_context,
                'request': request,
                'timestamp': datetime.now().isoformat(),
                'request_analysis': self._analyze_request(request),
                'context_metadata': {
                    'context_version': '1.0',
                    'enhancement_timestamp': datetime.now().isoformat(),
                    'context_stats': self.context_stats.copy()
                }
            }
            
            # Add additional context if provided
            if additional_context:
                enhanced_context.update(additional_context)
            
            # Update context statistics
            self.context_stats['total_context_updates'] += 1
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error enhancing context: {e}")
            return {
                'conversation': {},
                'analysis': {},
                'user': {},
                'system': {},
                'request': request,
                'timestamp': datetime.now().isoformat(),
                'request_analysis': {},
                'context_metadata': {
                    'context_version': '1.0',
                    'enhancement_timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
            }
    
    def update_context(self, request: str, response: str, metadata: Dict = None, user_id: str = "default"):
        """Update context with new interaction."""
        try:
            # Update conversation context
            self.conversation_context.add_interaction(request, response, metadata)
            self.context_stats['conversation_updates'] += 1
            
            # Update analysis context if it's an analysis request
            request_analysis = self._analyze_request(request)
            if request_analysis.get('is_analysis_request', False):
                analysis_type = request_analysis.get('analysis_type', 'general')
                analysis_params = request_analysis.get('parameters', {})
                
                self.analysis_context.start_analysis(analysis_type, analysis_params)
                self.analysis_context.complete_analysis({'result': response})
                self.context_stats['analysis_updates'] += 1
            
            # Update user context
            self.user_context.set_user(user_id, {
                'last_request': request,
                'last_response': response,
                'timestamp': datetime.now().isoformat()
            })
            self.context_stats['user_updates'] += 1
            
            # Update system context
            self.system_context.update_system_state({
                'last_interaction': datetime.now().isoformat(),
                'request_type': request_analysis.get('request_type', 'general'),
                'response_length': len(response)
            })
            self.system_context.add_performance_metric('response_length', len(response))
            self.context_stats['system_updates'] += 1
            
            logger.info(f"Updated context for request: {request[:50]}...")
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    def _analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze request for context enhancement."""
        request_lower = request.lower()
        
        # Basic analysis
        analysis = {
            'request_length': len(request),
            'word_count': len(request.split()),
            'is_analysis_request': False,
            'request_type': 'general',
            'analysis_type': None,
            'parameters': {},
            'complexity_level': 'medium',
            'keywords': [],
            'entities': []
        }
        
        # Request type classification
        if any(keyword in request_lower for keyword in ['analyze', 'analysis']):
            analysis['is_analysis_request'] = True
            analysis['request_type'] = 'analysis'
        elif any(keyword in request_lower for keyword in ['compare', 'comparison']):
            analysis['request_type'] = 'comparison'
        elif any(keyword in request_lower for keyword in ['show', 'list', 'display']):
            analysis['request_type'] = 'exploration'
        elif any(keyword in request_lower for keyword in ['help', 'guide']):
            analysis['request_type'] = 'help'
        
        # Analysis type classification
        if 'district heating' in request_lower:
            analysis['analysis_type'] = 'district_heating'
            analysis['keywords'].append('district_heating')
        elif 'heat pump' in request_lower:
            analysis['analysis_type'] = 'heat_pump'
            analysis['keywords'].append('heat_pump')
        elif 'compare' in request_lower:
            analysis['analysis_type'] = 'comparison'
            analysis['keywords'].append('comparison')
        
        # Complexity assessment
        word_count = analysis['word_count']
        if word_count < 5:
            analysis['complexity_level'] = 'simple'
        elif word_count < 15:
            analysis['complexity_level'] = 'medium'
        else:
            analysis['complexity_level'] = 'complex'
        
        # Extract entities (streets, numbers, etc.)
        import re
        
        # Extract street names
        street_pattern = r'\b[A-Z][a-z]+straße\b'
        streets = re.findall(street_pattern, request)
        if streets:
            analysis['entities'].extend(streets)
            analysis['parameters']['streets'] = streets
        
        # Extract numbers
        number_pattern = r'\b\d+\b'
        numbers = re.findall(number_pattern, request)
        if numbers:
            analysis['entities'].extend(numbers)
            analysis['parameters']['numbers'] = numbers
        
        # Extract keywords
        keywords = ['district', 'heating', 'heat', 'pump', 'analyze', 'compare', 'show', 'list']
        for keyword in keywords:
            if keyword in request_lower:
                analysis['keywords'].append(keyword)
        
        return analysis
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get comprehensive context summary."""
        return {
            'context_stats': self.context_stats.copy(),
            'conversation_summary': self.conversation_context.get_context(),
            'analysis_summary': self.analysis_context.get_analysis_summary(),
            'user_summary': self.user_context.get_context(),
            'system_summary': self.system_context.get_context(),
            'context_health': self._assess_context_health()
        }
    
    def _assess_context_health(self) -> Dict[str, Any]:
        """Assess context system health."""
        health_score = 0.0
        issues = []
        
        # Check conversation context
        if len(self.conversation_context.conversation_history) > 0:
            health_score += 0.3
        else:
            issues.append("No conversation history")
        
        # Check analysis context
        if len(self.analysis_context.analysis_history) > 0:
            health_score += 0.3
        else:
            issues.append("No analysis history")
        
        # Check user context
        if self.user_context.user_id is not None:
            health_score += 0.2
        else:
            issues.append("No user context")
        
        # Check system context
        if len(self.system_context.system_state) > 0:
            health_score += 0.2
        else:
            issues.append("No system context")
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 0.7 else 'needs_attention' if health_score > 0.3 else 'unhealthy',
            'issues': issues,
            'recommendations': self._get_context_health_recommendations(health_score, issues)
        }
    
    def _get_context_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Get context health improvement recommendations."""
        recommendations = []
        
        if health_score < 0.7:
            recommendations.append("Increase context usage to improve system awareness")
        
        if "No conversation history" in issues:
            recommendations.append("Start conversations to build context history")
        
        if "No analysis history" in issues:
            recommendations.append("Perform analyses to build analysis context")
        
        if "No user context" in issues:
            recommendations.append("Set user context for personalized experiences")
        
        if "No system context" in issues:
            recommendations.append("Enable system context tracking")
        
        return recommendations
    
    def clear_context(self, context_type: str = "all"):
        """Clear specific type of context."""
        try:
            if context_type in ["all", "conversation"]:
                self.conversation_context.conversation_history.clear()
                self.conversation_context.conversation_flow.clear()
                self.conversation_context.current_topic = None
                logger.info("Cleared conversation context")
            
            if context_type in ["all", "analysis"]:
                self.analysis_context.current_analysis = None
                self.analysis_context.analysis_history.clear()
                self.analysis_context.analysis_parameters.clear()
                logger.info("Cleared analysis context")
            
            if context_type in ["all", "user"]:
                self.user_context.user_id = None
                self.user_context.user_session.clear()
                self.user_context.user_goals.clear()
                self.user_context.user_constraints.clear()
                logger.info("Cleared user context")
            
            if context_type in ["all", "system"]:
                self.system_context.system_state.clear()
                self.system_context.resource_usage.clear()
                self.system_context.performance_metrics.clear()
                self.system_context.system_health.clear()
                logger.info("Cleared system context")
            
            # Reset stats
            self.context_stats = {
                'total_context_updates': 0,
                'conversation_updates': 0,
                'analysis_updates': 0,
                'user_updates': 0,
                'system_updates': 0
            }
            
        except Exception as e:
            logger.error(f"Error clearing context: {e}")

# Export classes for use in other modules
__all__ = [
    'AgentMemory',
    'AgentContext',
    'SessionMemory',
    'LearningMemory',
    'UserProfiles',
    'ContextPersistence',
    'ConversationContext',
    'AnalysisContext',
    'UserContext',
    'SystemContext',
    'MemoryEntry',
    'ContextSnapshot'
]
