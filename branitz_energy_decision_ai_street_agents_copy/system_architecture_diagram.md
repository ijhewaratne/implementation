# Branitz Energy Decision AI System Architecture

## System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                               │
│  Natural Language Queries: "analyze district heating for X"    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                ENERGY PLANNER AGENT                            │
│  • Analyzes user requests                                      │
│  • Delegates to appropriate specialist agents                  │
│  • Routes: DH → CHA, HP → DHA, Compare → CA, Data → DEA       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼───┐ ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
│    CHA    │ │     DHA     │ │    CA    │ │     DEA     │
│District   │ │Heat Pump    │ │Compare   │ │Data Explorer│
│Heating    │ │Specialist   │ │Scenarios │ │Agent        │
└─────┬─────┘ └──────┬──────┘ └────┬────┘ └──────┬──────┘
      │              │              │              │
      └──────────────┼──────────────┼──────────────┘
                     │              │
┌────────────────────▼──────────────▼─────────────────────────────┐
│                    ENERGY TOOLS                                │
│  • Building extraction & validation                            │
│  • Network graph creation                                      │
│  • Energy simulation pipeline                                  │
│  • KPI calculation & analysis                                  │
│  • Visualization generation                                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                MAIN PIPELINE (main.py)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Data Prep    │ │Building     │ │Envelope &   │ │Demand       ││
│  │& Loading    │ │Attributes   │ │U-values     │ │Calculation  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Load Profile │ │Network      │ │Scenario     │ │Simulation   ││
│  │Generation   │ │Construction │ │Management   │ │Runner       ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐                                │
│  │KPI          │ │LLM          │                                │
│  │Calculator   │ │Reporter     │                                │
│  └─────────────┘ └─────────────┘                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    DATA LAYER                                  │
│  • Building geometries (GeoJSON)                               │
│  • Street networks (OSM)                                       │
│  • Demographics & attributes                                   │
│  • Weather data                                                │
│  • Energy profiles                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow
1. **Input**: User natural language query
2. **Delegation**: Planner Agent routes to specialist
3. **Execution**: Specialist Agent runs complete analysis
4. **Processing**: 10-step pipeline processes data
5. **Output**: KPI analysis, visualizations, reports

## Key Components
- **Multi-Agent System**: 4 specialized agents with specific roles
- **Energy Tools**: 9 specialized tools for analysis
- **Pipeline**: 10-step data processing workflow
- **Visualization**: Network maps and analysis charts
- **AI Analysis**: LLM-powered insights and recommendations
