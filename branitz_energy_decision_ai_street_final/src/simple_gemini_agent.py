#!/usr/bin/env python3
"""
Simple Gemini Agent Implementation
Provides a fallback agent system that can use Gemini API directly without ADK.
"""

import yaml
import os
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path


class SimpleAgent:
    """Simple agent implementation that can use Gemini API directly."""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get("name", "SimpleAgent")
        self.model = config.get("model", "gemini-1.5-flash-latest")
        self.system_prompt = config.get("system_prompt", "")
        self.tools = config.get("tools", [])
        self.api_key = None
        self.gemini_model = None
        
        # Try to initialize Gemini API
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini API connection."""
        try:
            import google.generativeai as genai
            
            # Get API key from config or environment
            config_path = Path("configs/gemini_config.yml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    gemini_config = yaml.safe_load(f)
                    self.api_key = gemini_config.get("api_key")
            
            if not self.api_key:
                self.api_key = os.environ.get("GEMINI_API_KEY")
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(self.model)
                print(f"✅ Gemini API initialized for {self.name}")
            else:
                print(f"⚠️ No Gemini API key found for {self.name}")
                
        except ImportError:
            print(f"⚠️ google-generativeai not installed for {self.name}")
        except Exception as e:
            print(f"❌ Error initializing Gemini for {self.name}: {e}")
    
    def run(self, prompt: str) -> str:
        """Run the agent with a given prompt."""
        # First, try to use Gemini API
        if self.gemini_model:
            try:
                return self._run_with_gemini(prompt)
            except Exception as e:
                print(f"⚠️ Gemini API failed for {self.name}: {e}")
        
        # Fallback to rule-based responses
        return self._run_fallback(prompt)
    
    def _run_with_gemini(self, prompt: str) -> str:
        """Run using Gemini API."""
        # Prepare tools information
        tools_info = ""
        if self.tools:
            tools_info = "\n\nAvailable tools:\n"
            for tool in self.tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    tools_info += f"- {tool.name}: {tool.description}\n"
        
        # Enhanced system prompt
        enhanced_prompt = f"{self.system_prompt}{tools_info}\n\nUser request: {prompt}"
        
        # Call Gemini API
        response = self.gemini_model.generate_content(enhanced_prompt)
        return response.text
    
    def _run_fallback(self, prompt: str) -> str:
        """Fallback to rule-based responses when Gemini is not available."""
        # Check if prompt is a tool call
        if "analyze_kpi_report(" in prompt:
            from src.enhanced_tools import analyze_kpi_report
            import re
            m = re.search(r"kpi_report_path\s*=\s*['\"](.+?)['\"]", prompt)
            if m:
                return analyze_kpi_report(m.group(1))
            return "❌ Missing kpi_report_path in prompt."
        
        # Generic fallback responses based on agent type
        if "EnergyGPT" in self.name:
            return self._energygpt_fallback(prompt)
        elif "EnergyPlanner" in self.name:
            return self._energyplanner_fallback(prompt)
        else:
            return f"🤖 {self.name} (Fallback Mode): I understand you want help with '{prompt}'. Please use specific tool calls for analysis."
    
    def _energygpt_fallback(self, prompt: str) -> str:
        """EnergyGPT-specific fallback responses."""
        return f"""🤖 EnergyGPT Analysis (Fallback Mode)

I'm currently running in fallback mode without real AI capabilities. For full analysis, please ensure:
1. Gemini API key is configured
2. google-generativeai package is installed
3. ADK framework is available

Current request: {prompt}

To get real AI analysis, please:
- Use the analyze_kpi_report tool with a specific path
- Ensure the system is properly configured for Gemini API
"""
    
    def _energyplanner_fallback(self, prompt: str) -> str:
        """EnergyPlanner-specific fallback responses."""
        return f"""🏗️ Energy Planner (Fallback Mode)

I'm currently running in fallback mode. For comprehensive energy planning, please ensure the full system is configured.

Current request: {prompt}

Available analysis options:
1. District Heating (CHA) analysis
2. Heat Pump (DHA) analysis  
3. Comparative analysis
4. KPI reporting

Please use specific tool calls for detailed analysis.
"""


def create_simple_agent(config: Dict[str, Any]) -> SimpleAgent:
    """Create a simple agent instance."""
    return SimpleAgent(config)


# Test function
def test_gemini_connection():
    """Test if Gemini API is working."""
    agent = SimpleAgent({
        "name": "TestAgent",
        "model": "gemini-1.5-flash-latest",
        "system_prompt": "You are a test agent.",
    })
    
    response = agent.run("Hello, can you respond with 'Gemini API is working'?")
    print(f"Response: {response}")
    return response


if __name__ == "__main__":
    test_gemini_connection()
