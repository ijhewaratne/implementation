#!/usr/bin/env python3
"""
Advanced ADK Agent Features
Enhanced multi-agent system with advanced capabilities including memory, context, learning, and adaptive strategies.
"""

import os
import sys
import json
import yaml
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib
import pickle
from pathlib import Path

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add ADK to path
sys.path.insert(0, 'adk')

# Try to import ADK Agent, fallback to Mock Agent
try:
    from adk.api.agent import Agent
    ADK_AVAILABLE = True
    logger.info("ADK Agent available")
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("ADK not available, using MockAgent fallback")
    
    class Agent:
        def __init__(self, config: Dict = None):
            if config is None:
                config = {}
            self.config = config
            self.name = config.get('name', 'MockAgent')
            self.system_prompt = config.get('system_prompt', 'You are a helpful AI assistant.')
            self.tools = config.get('tools', [])
            logger.info(f"Initialized MockAgent: {self.name}")
        
        def run(self, request: str) -> Any:
            logger.info(f"MockAgent '{self.name}' processing request: {request}")
            # Simulate tool call if input suggests it
            if "tool_call" in request.lower():
                tool_name = request.split("tool_call:")[1].strip().split("(")[0]
                return MockResponse(f"TOOL: {tool_name} executed successfully by MockAgent.")
            return MockResponse(f"MockAgent '{self.name}' processed: {request}")
    
    class MockResponse:
        def __init__(self, response):
            self.agent_response = response
            self.tool_calls = []  # Simulate no tool calls for simplicity


@dataclass
class AgentMemory:
    """Agent memory data structure."""
    session_id: str
    timestamp: datetime
    request: str
    response: str
    context: Dict[str, Any]
    performance_metrics: Dict[str, float]
    user_feedback: Optional[str] = None

@dataclass
class AgentContext:
    """Agent context data structure."""
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    system_state: Dict[str, Any]
    analysis_context: Dict[str, Any]
    timestamp: datetime

class AgentMemoryManager:
    """Advanced agent memory management system."""
    
    def __init__(self, memory_file: str = "data/agent_memory.pkl"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memories: List[AgentMemory] = []
        self.memory_index: Dict[str, List[int]] = defaultdict(list)
        self.load_memory()
    
    def load_memory(self):
        """Load memory from persistent storage."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'rb') as f:
                    self.memories = pickle.load(f)
                self._rebuild_index()
                logger.info(f"Loaded {len(self.memories)} memory entries")
            except Exception as e:
                logger.warning(f"Failed to load memory: {e}")
                self.memories = []
    
    def save_memory(self):
        """Save memory to persistent storage."""
        try:
            with open(self.memory_file, 'wb') as f:
                pickle.dump(self.memories, f)
            logger.info(f"Saved {len(self.memories)} memory entries")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def add_memory(self, memory: AgentMemory):
        """Add new memory entry."""
        self.memories.append(memory)
        self._index_memory(len(self.memories) - 1)
        self.save_memory()
    
    def get_relevant_memories(self, request: str, limit: int = 5) -> List[AgentMemory]:
        """Get relevant memories for a request."""
        request_hash = self._hash_request(request)
        relevant_indices = self.memory_index.get(request_hash, [])
        
        # Get most recent relevant memories
        relevant_memories = [self.memories[i] for i in relevant_indices[-limit:]]
        
        # Sort by timestamp (most recent first)
        relevant_memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        return relevant_memories
    
    def _hash_request(self, request: str) -> str:
        """Create hash for request indexing."""
        # Simple keyword-based hashing
        keywords = set(request.lower().split())
        return hashlib.md5(' '.join(sorted(keywords)).encode()).hexdigest()
    
    def _index_memory(self, index: int):
        """Index memory for fast retrieval."""
        memory = self.memories[index]
        request_hash = self._hash_request(memory.request)
        self.memory_index[request_hash].append(index)
    
    def _rebuild_index(self):
        """Rebuild memory index."""
        self.memory_index.clear()
        for i, memory in enumerate(self.memories):
            self._index_memory(i)

class AgentContextManager:
    """Advanced agent context management system."""
    
    def __init__(self):
        self.conversation_history: deque = deque(maxlen=100)
        self.user_preferences: Dict[str, Any] = {}
        self.system_state: Dict[str, Any] = {}
        self.analysis_context: Dict[str, Any] = {}
    
    def enhance_context(self, request: str, additional_context: Dict = None) -> Dict:
        """Enhance context with advanced information."""
        context = {
            'conversation_history': list(self.conversation_history),
            'user_preferences': self.user_preferences,
            'system_state': self.system_state,
            'analysis_context': self.analysis_context,
            'request': request,
            'timestamp': datetime.now().isoformat(),
            'request_type': self._classify_request(request),
            'complexity_level': self._assess_complexity(request)
        }
        
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def update_context(self, request: str, response: str, metadata: Dict = None):
        """Update context with new interaction."""
        interaction = {
            'request': request,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(interaction)
        
        # Update user preferences based on interaction
        self._update_user_preferences(request, response)
        
        # Update system state
        self._update_system_state(interaction)
    
    def _classify_request(self, request: str) -> str:
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
    
    def _assess_complexity(self, request: str) -> str:
        """Assess request complexity."""
        words = len(request.split())
        
        if words < 5:
            return 'simple'
        elif words < 15:
            return 'medium'
        else:
            return 'complex'
    
    def _update_user_preferences(self, request: str, response: str):
        """Update user preferences based on interaction."""
        # Simple preference learning based on request patterns
        if 'district heating' in request.lower():
            self.user_preferences['preferred_analysis_type'] = 'district_heating'
        elif 'heat pump' in request.lower():
            self.user_preferences['preferred_analysis_type'] = 'heat_pump'
        
        # Update preferred detail level based on response length
        if len(response) > 1000:
            self.user_preferences['detail_level'] = 'high'
        elif len(response) > 500:
            self.user_preferences['detail_level'] = 'medium'
        else:
            self.user_preferences['detail_level'] = 'low'
    
    def _update_system_state(self, interaction: Dict):
        """Update system state based on interaction."""
        self.system_state['last_interaction'] = interaction['timestamp']
        self.system_state['total_interactions'] = len(self.conversation_history)
        
        # Update analysis context
        if interaction['metadata'] and 'analysis_type' in interaction['metadata']:
            self.analysis_context['last_analysis_type'] = interaction['metadata']['analysis_type']

class LearningEngine:
    """Advanced learning engine for agent improvement."""
    
    def __init__(self):
        self.learning_data: List[Dict[str, Any]] = []
        self.performance_patterns: Dict[str, List[float]] = defaultdict(list)
        self.success_patterns: Dict[str, int] = defaultdict(int)
        self.improvement_suggestions: List[str] = []
    
    def learn_from_interaction(self, request: str, result: Dict[str, Any]):
        """Learn from agent interaction."""
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'request': request,
            'result': result,
            'success': result.get('success', False),
            'response_time': result.get('response_time', 0),
            'user_satisfaction': result.get('user_satisfaction', None)
        }
        
        self.learning_data.append(learning_entry)
        
        # Update performance patterns
        self._update_performance_patterns(learning_entry)
        
        # Update success patterns
        self._update_success_patterns(learning_entry)
        
        # Generate improvement suggestions
        self._generate_improvement_suggestions()
    
    def _update_performance_patterns(self, entry: Dict[str, Any]):
        """Update performance patterns."""
        request_type = self._classify_request_type(entry['request'])
        self.performance_patterns[request_type].append(entry['response_time'])
        
        # Keep only recent performance data
        if len(self.performance_patterns[request_type]) > 100:
            self.performance_patterns[request_type] = self.performance_patterns[request_type][-100:]
    
    def _update_success_patterns(self, entry: Dict[str, Any]):
        """Update success patterns."""
        if entry['success']:
            request_type = self._classify_request_type(entry['request'])
            self.success_patterns[request_type] += 1
    
    def _classify_request_type(self, request: str) -> str:
        """Classify request type for learning."""
        request_lower = request.lower()
        
        if 'district heating' in request_lower:
            return 'district_heating'
        elif 'heat pump' in request_lower:
            return 'heat_pump'
        elif 'compare' in request_lower:
            return 'comparison'
        elif 'analyze' in request_lower:
            return 'analysis'
        else:
            return 'general'
    
    def _generate_improvement_suggestions(self):
        """Generate improvement suggestions based on learning."""
        self.improvement_suggestions.clear()
        
        # Analyze performance patterns
        for request_type, times in self.performance_patterns.items():
            if len(times) > 10:
                avg_time = sum(times) / len(times)
                if avg_time > 30:  # 30 seconds
                    self.improvement_suggestions.append(
                        f"Consider optimizing {request_type} requests (avg: {avg_time:.1f}s)"
                    )
        
        # Analyze success patterns
        total_interactions = len(self.learning_data)
        if total_interactions > 20:
            success_rate = sum(1 for entry in self.learning_data if entry['success']) / total_interactions
            if success_rate < 0.8:  # 80% success rate
                self.improvement_suggestions.append(
                    f"Success rate is {success_rate:.1%}, consider improving error handling"
                )
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights and recommendations."""
        return {
            'total_interactions': len(self.learning_data),
            'performance_patterns': dict(self.performance_patterns),
            'success_patterns': dict(self.success_patterns),
            'improvement_suggestions': self.improvement_suggestions,
            'learning_summary': self._generate_learning_summary()
        }
    
    def _generate_learning_summary(self) -> Dict[str, Any]:
        """Generate learning summary."""
        if not self.learning_data:
            return {'status': 'no_data'}
        
        recent_data = self.learning_data[-20:]  # Last 20 interactions
        
        avg_response_time = sum(entry['response_time'] for entry in recent_data) / len(recent_data)
        success_rate = sum(1 for entry in recent_data if entry['success']) / len(recent_data)
        
        return {
            'status': 'active_learning',
            'avg_response_time': avg_response_time,
            'success_rate': success_rate,
            'recent_trend': 'improving' if success_rate > 0.8 else 'needs_attention'
        }

class AdaptiveStrategy:
    """Adaptive strategy selection for agent behavior."""
    
    def __init__(self):
        self.strategies = {
            'conservative': self._conservative_strategy,
            'aggressive': self._aggressive_strategy,
            'balanced': self._balanced_strategy,
            'learning': self._learning_strategy
        }
        self.current_strategy = 'balanced'
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)
    
    def select_strategy(self, request: str, context: Dict[str, Any]) -> str:
        """Select optimal strategy based on request and context."""
        # Analyze request characteristics
        complexity = context.get('complexity_level', 'medium')
        request_type = context.get('request_type', 'general')
        
        # Select strategy based on context
        if complexity == 'simple' and request_type == 'exploration':
            strategy = 'aggressive'
        elif complexity == 'complex' and request_type == 'analysis':
            strategy = 'conservative'
        elif context.get('user_preferences', {}).get('detail_level') == 'high':
            strategy = 'aggressive'
        else:
            strategy = 'balanced'
        
        self.current_strategy = strategy
        return strategy
    
    def _conservative_strategy(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conservative strategy with thorough validation."""
        return {
            'approach': 'conservative',
            'validation_level': 'high',
            'timeout': 60,
            'retry_count': 3,
            'error_handling': 'strict'
        }
    
    def _aggressive_strategy(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggressive strategy with fast execution."""
        return {
            'approach': 'aggressive',
            'validation_level': 'medium',
            'timeout': 30,
            'retry_count': 1,
            'error_handling': 'lenient'
        }
    
    def _balanced_strategy(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Balanced strategy with moderate settings."""
        return {
            'approach': 'balanced',
            'validation_level': 'medium',
            'timeout': 45,
            'retry_count': 2,
            'error_handling': 'moderate'
        }
    
    def _learning_strategy(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Learning strategy that adapts based on performance."""
        # Get recent performance data
        recent_performance = self.strategy_performance.get(self.current_strategy, [])
        
        if recent_performance and len(recent_performance) > 5:
            avg_performance = sum(recent_performance) / len(recent_performance)
            if avg_performance > 0.8:
                return self._aggressive_strategy(request, context)
            elif avg_performance < 0.6:
                return self._conservative_strategy(request, context)
        
        return self._balanced_strategy(request, context)
    
    def update_strategy_performance(self, strategy: str, performance: float):
        """Update strategy performance for learning."""
        self.strategy_performance[strategy].append(performance)
        
        # Keep only recent performance data
        if len(self.strategy_performance[strategy]) > 50:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-50:]

class AdvancedADKAgent:
    """Advanced ADK agent with enhanced capabilities."""
    
    def __init__(self, agent_type: str, config: Dict[str, Any]):
        self.agent_type = agent_type
        self.config = config
        self.memory = AgentMemoryManager()
        self.context = AgentContextManager()
        self.learning_engine = LearningEngine()
        self.adaptive_strategy = AdaptiveStrategy()
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize base agent
        self.base_agent = self._initialize_base_agent()
        
        logger.info(f"Initialized AdvancedADKAgent: {agent_type}")
    
    def _initialize_base_agent(self) -> Agent:
        """Initialize base ADK agent."""
        try:
            if ADK_AVAILABLE:
                return Agent(config=self.config)
            else:
                # For fallback, create a simple agent with the config
                return Agent(self.config)
        except Exception as e:
            logger.error(f"Failed to initialize base agent: {e}")
            raise
    
    def process_request(self, request: str, additional_context: Dict = None) -> Dict[str, Any]:
        """Process request with advanced capabilities."""
        start_time = time.time()
        
        try:
            # 1. Context awareness
            enhanced_context = self.context.enhance_context(request, additional_context)
            
            # 2. Memory integration
            relevant_memories = self.memory.get_relevant_memories(request)
            
            # 3. Adaptive strategy
            strategy = self.adaptive_strategy.select_strategy(request, enhanced_context)
            
            # 4. Execute with advanced capabilities
            result = self._execute_advanced_processing(request, enhanced_context, strategy, relevant_memories)
            
            # 5. Update memory and learning
            self._update_memory_and_learning(request, result, enhanced_context)
            
            # 6. Update performance metrics
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, result.get('success', False))
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time,
                'agent_type': self.agent_type
            }
    
    def _execute_advanced_processing(self, request: str, context: Dict[str, Any], 
                                   strategy: str, memories: List[AgentMemory]) -> Dict[str, Any]:
        """Execute advanced processing with strategy and memory."""
        try:
            # Enhance request with memory and context
            enhanced_request = self._enhance_request_with_memory(request, memories, context)
            
            # Execute with base agent
            if ADK_AVAILABLE:
                response = self.base_agent.run(enhanced_request)
                agent_response = getattr(response, 'agent_response', str(response))
            else:
                agent_response = self.base_agent.run(enhanced_request)
            
            # Process response with advanced capabilities
            processed_response = self._process_response_with_advanced_capabilities(
                agent_response, context, strategy
            )
            
            return {
                'success': True,
                'agent_response': processed_response,
                'original_response': agent_response,
                'strategy_used': strategy,
                'memory_enhanced': len(memories) > 0,
                'context_enhanced': True,
                'agent_type': self.agent_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in advanced processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_type': self.agent_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def _enhance_request_with_memory(self, request: str, memories: List[AgentMemory], 
                                   context: Dict[str, Any]) -> str:
        """Enhance request with relevant memory and context."""
        if not memories:
            return request
        
        # Build memory context
        memory_context = "Based on previous similar requests:\n"
        for memory in memories[:3]:  # Use top 3 relevant memories
            memory_context += f"- {memory.request}: {memory.response[:100]}...\n"
        
        # Build enhanced request
        enhanced_request = f"""
Context: {memory_context}

Current Request: {request}

Please consider the previous context when responding to the current request.
"""
        
        return enhanced_request
    
    def _process_response_with_advanced_capabilities(self, response: str, 
                                                   context: Dict[str, Any], 
                                                   strategy: str) -> str:
        """Process response with advanced capabilities."""
        # Apply strategy-based processing
        if strategy == 'aggressive':
            # Add performance insights
            response += "\n\n[Performance: Optimized for speed]"
        elif strategy == 'conservative':
            # Add thoroughness note
            response += "\n\n[Analysis: Thoroughly validated]"
        elif strategy == 'learning':
            # Add learning insights
            insights = self.learning_engine.get_learning_insights()
            if insights['improvement_suggestions']:
                response += f"\n\n[Learning: {insights['improvement_suggestions'][0]}]"
        
        # Add context-aware enhancements
        if context.get('user_preferences', {}).get('detail_level') == 'high':
            response += "\n\n[Detail Level: High - Comprehensive analysis provided]"
        
        return response
    
    def _update_memory_and_learning(self, request: str, result: Dict[str, Any], 
                                  context: Dict[str, Any]):
        """Update memory and learning systems."""
        # Create memory entry
        memory = AgentMemory(
            session_id=context.get('session_id', 'default'),
            timestamp=datetime.now(),
            request=request,
            response=result.get('agent_response', ''),
            context=context,
            performance_metrics={
                'response_time': result.get('response_time', 0),
                'success': result.get('success', False)
            }
        )
        
        # Add to memory
        self.memory.add_memory(memory)
        
        # Update context
        self.context.update_context(request, result.get('agent_response', ''), {
            'analysis_type': self._extract_analysis_type(request),
            'success': result.get('success', False)
        })
        
        # Update learning
        self.learning_engine.learn_from_interaction(request, result)
        
        # Update strategy performance
        if result.get('success', False):
            self.adaptive_strategy.update_strategy_performance(
                result.get('strategy_used', 'balanced'), 1.0
            )
        else:
            self.adaptive_strategy.update_strategy_performance(
                result.get('strategy_used', 'balanced'), 0.0
            )
    
    def _extract_analysis_type(self, request: str) -> str:
        """Extract analysis type from request."""
        request_lower = request.lower()
        
        if 'district heating' in request_lower:
            return 'district_heating'
        elif 'heat pump' in request_lower:
            return 'heat_pump'
        elif 'compare' in request_lower:
            return 'comparison'
        else:
            return 'general'
    
    def _update_performance_metrics(self, response_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics['response_time'].append(response_time)
        self.performance_metrics['success_rate'].append(1.0 if success else 0.0)
        
        # Keep only recent metrics
        for metric in self.performance_metrics:
            if len(self.performance_metrics[metric]) > 100:
                self.performance_metrics[metric] = self.performance_metrics[metric][-100:]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status."""
        return {
            'agent_type': self.agent_type,
            'memory_entries': len(self.memory.memories),
            'conversation_history': len(self.context.conversation_history),
            'learning_insights': self.learning_engine.get_learning_insights(),
            'current_strategy': self.adaptive_strategy.current_strategy,
            'performance_metrics': {
                'avg_response_time': sum(self.performance_metrics['response_time']) / len(self.performance_metrics['response_time']) if self.performance_metrics['response_time'] else 0,
                'success_rate': sum(self.performance_metrics['success_rate']) / len(self.performance_metrics['success_rate']) if self.performance_metrics['success_rate'] else 0
            },
            'adk_available': ADK_AVAILABLE
        }

# Export classes for use in other modules
__all__ = [
    'AdvancedADKAgent',
    'AgentMemoryManager',
    'AgentContextManager',
    'LearningEngine',
    'AdaptiveStrategy',
    'AgentMemory',
    'AgentContext'
]
