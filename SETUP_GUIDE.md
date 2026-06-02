# Household Energy Requirement Calculator & Advisor
## LangGraph Multi-Agent System - Setup Complete

### Project Overview
A multi-agent AI system built with LangGraph that collects, analyzes, and optimizes household electricity consumption data. The system uses state management to maintain context across agents and integrates with OpenAI for LLM-powered insights.

---

## Current Implementation

### ✅ Completed - Agent 1: Collect Household Profile
**File**: `src/agents/collect_household_profile_agent.py`

**Capabilities**:
- Loads household profiles from CSV dataset (1,000 households across 5 climate zones)
- Accepts custom household profiles
- Collects core profile information:
  - House type, bedrooms, floor area, number of floors
  - Occupancy (adults, children)
  - Climate zone, city tier
  - Building envelope (insulation, window type, roof type)
  - Appliance inventory
  - Renewable energy assets (solar panels, battery storage)
- Validates required fields
- Optional LLM analysis (when OpenAI API configured)
- Maintains state throughout workflow

**Input Methods**:
1. Load from dataset using `household_id`
2. Provide custom profile data

---

## Architecture

### State Management
**File**: `src/state.py`

`HouseholdProfileState` (TypedDict): Maintains complete household data across all agents
- 47+ fields covering all household aspects
- Messages and error tracking
- Benchmarking and recommendation storage

### Utilities
**File**: `src/utils.py`

Functions for:
- Loading CSV data (`load_household_data()`)
- Retrieving household profiles (`get_household_by_id()`)
- Finding similar households (`get_similar_households()`)
- Dataset statistics (`get_dataset_stats()`)
- Profile validation (`validate_household_profile()`)

### Main Workflow
**File**: `src/main.py`

LangGraph workflow setup with:
- StateGraph initialization
- Node definitions
- Edge connections
- Three execution examples:
  1. Dataset household #0 (Apartment, Hot & Dry)
  2. Dataset household #5 (Apartment, Temperate)
  3. Custom profile (Villa, Hot & Humid)

---

## Configuration

### Environment Setup
Create `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

If not configured, LLM analysis is skipped but workflow continues.

### Dependencies (Installed)
- `langgraph`: Multi-agent workflow orchestration
- `langchain`: LLM integration framework
- `openai`: GPT API client
- `pandas`: CSV data handling
- `python-dotenv`: Environment variables

---

## How to Run

### From project root (`agenticai-phase2-assignment/`):
```bash
python src/main.py
```

### Example Output
The system processes three households and displays:
1. Collected household profile data
2. Agent messages (loading, validation, analysis)
3. Full state in JSON format for debugging

---

## Next Steps - Planned Agents

2. **Capture Occupancy Details Agent** - Specialized occupancy profiling
3. **Inventory Appliances Agent** - Detailed appliance energy modeling
4. **Assess Building Envelope Agent** - Climate adjustment factors
5. **Estimate Gross Energy Consumption Agent** - Appliance-level calculations
6. **Apply Climate & Insulation Adjustments Agent** - Real-world normalization
7. **Calculate Net Grid Draw Agent** - Solar generation offsets
8. **Project Monthly Bill Agent** - Cost estimation
9. **Benchmark Against Dataset Agent** - Peer comparison
10. **Run Solar ROI Analysis Agent** - Scenario evaluation
11. **Generate Recommendations Agent** - Prioritized improvements
12. **Comprehensive Advisor Agent** - Final synthesis & reporting

---

## File Structure
```
agenticai-phase2-assignment/
├── src/
│   ├── main.py                                    # Entry point, LangGraph workflow
│   ├── state.py                                   # State management (TypedDict)
│   ├── utils.py                                   # Data utilities
│   └── agents/
│       ├── __init__.py
│       └── collect_household_profile_agent.py    # Agent 1
├── household_energy_requirement.csv               # Dataset (1,000 records)
├── requirements.txt                               # Dependencies
├── .env                                           # API configuration
└── README.md
```

---

## Key Features

✅ **State Management**: Full context maintained across agents
✅ **CSV Data Integration**: 1,000 household profiles with 47 attributes
✅ **Flexible Input**: Load from dataset or custom profiles
✅ **Validation**: Profile completeness checking
✅ **LLM Ready**: Optional OpenAI integration for insights
✅ **Extensible**: Easy to add new agent nodes
✅ **Error Handling**: Graceful degradation without API key

---

## Testing Results

Successfully processed three households:
- ✅ Dataset household (Hot & Dry, Tier 3 apartment with solar)
- ✅ Dataset household (Temperate, Tier 2 apartment without solar)
- ✅ Custom profile (Hot & Humid, Tier 2 villa)

All profiles collected, validated, and state maintained correctly.
