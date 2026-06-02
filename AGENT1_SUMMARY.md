# Agent 1: Collect & Validate Household Profile
## Simplified, Focused Implementation

### Core Responsibilities

#### 1. Collect & Validate Inputs
Captures 6 core fields (match dataset columns):
- `house_type` - Apartment, Villa, Bungalow, Townhouse, Penthouse
- `num_bedrooms` - Integer > 0
- `climate_zone` - Hot & Dry, Hot & Humid, Composite, Temperate, Cold
- `city_tier` - Tier 1, Tier 2, Tier 3
- `num_occupants` - Integer > 0
- `floor_area_sqft` - Optional initially

#### 2. Normalize Inputs
Maps user input to dataset format:
```
"apt" → "Apartment"
"hot dry" → "Hot & Dry"
"tier 2" → "Tier 2"
```

#### 3. Basic Validation
- Bedroom count > 0
- Occupants > 0
- Climate zone in valid list
- House type in valid list
- City tier in valid list

#### 4. Read Dataset (Pandas)
- Loads 1,000 household records
- 47 columns available for future agents
- Started immediately in __init__

#### 5. Lightweight Initial Analysis
- Filter similar households (by house_type, climate_zone, city_tier)
- Count matches
- Show sample comparable data (daily consumption, monthly cost estimate)

---

## State (Simplified)

Only 11 fields now:
```python
HouseholdProfileState = {
    # Core inputs
    'house_type',
    'num_bedrooms',
    'floor_area_sqft',  # Optional
    'climate_zone',
    'city_tier',
    'num_occupants',
    
    # Agent tracking
    'messages',
    'errors',
    'current_agent',
    'workflow_stage',
    
    # Analysis results
    'similar_households',
    'similar_households_count',
}
```

---

## Processing Flow

```
INPUT → NORMALIZE → VALIDATE → ANALYZE → OUTPUT

1. Normalize inputs to dataset format
   ✓ house_type, climate_zone, city_tier
   
2. Validate normalized inputs
   ✓ All required fields present
   ✓ Values within valid ranges
   
3. If valid: Find similar households
   → Filter by house_type + climate_zone + city_tier
   → Return top 5 matches
   
4. If invalid: Return error messages
```

---

## Usage Example

```python
profile = {
    'house_type': 'apt',  # Will normalize to "Apartment"
    'num_bedrooms': 2,
    'climate_zone': 'hot dry',  # Will normalize to "Hot & Dry"
    'city_tier': 'tier 2',  # Will normalize to "Tier 2"
    'num_occupants': 3,
}

state = run_with_custom_profile(profile)
```

### Output Structure
```
[PROFILE COLLECTION RESULTS]
- Collected Profile (6 fields)
- Validation Status (PASSED/FAILED)
- Initial Analysis (similar households count)
- Similar Households Samples (top 3 matches)
- Agent Messages (step-by-step log)
- Validation Errors (if any)
```

---

## Code Structure

**Files Modified**:
- `src/state.py` - Simplified to 11 fields
- `src/utils.py` - Validation, normalization, dataset filtering
- `src/agents/collect_household_profile_agent.py` - Focused agent logic
- `src/main.py` - 4 test examples (valid, valid, normalization, invalid)

**Test Cases**:
1. ✓ Valid apartment (Hot & Dry, Tier 3)
2. ✓ Valid villa (Hot & Humid, Tier 2)
3. ✓ Input normalization ("apt" → "Apartment", "cold" → "Cold")
4. ✓ Invalid profile (missing required field)

---

## Benefits of This Approach

✅ **Clear & Focused** - One agent, clear responsibility
✅ **Testable** - Easy to validate each step
✅ **Extensible** - Ready to add Agent 2 without refactoring
✅ **Maintainable** - No unnecessary complexity
✅ **Benchmarking Ready** - Uses dataset filtering for comparisons
✅ **Error Handling** - Graceful validation failures

---

## Next Steps

Ready to implement **Agent 2: Capture Occupancy Details** when needed.
This will expand the state with occupancy-specific fields and analysis.
