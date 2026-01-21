# Position Refactoring Project - Chunk 1 Assessment

## Executive Summary

⚠️ **STATUS**: BLOCKED - Missing critical player data (Age, Wage, Contract)
✅ **METRICS**: All performance metrics available and excellent for role evaluation
🔴 **BLOCKER**: Need new FM export with player information columns
⏱️ **ESTIMATED TIME**: 5-6 hours for Chunk 1 (once proper data provided)

---

## 🚨 CRITICAL ISSUE: Missing Player Data

The provided "Go Ahead - New Format.html" file contains **only performance metrics** but is missing:
- ❌ **Age** (needed for prospect/veteran evaluation)
- ❌ **Wage** (CRITICAL for value score calculation)
- ❌ **Contract Expires** (needed for transfer recommendations)

**This export appears to be from Squad View > Performance tab only.**

### Required Action Before Proceeding:

**You need to export a different view from FM that includes both:**
1. ✅ Performance metrics (per-90 stats) - already have these!
2. ❌ Player information (Age, Wage, Contract) - missing!

**How to get the correct export:**

```
Option 1: Customize Squad View
─────────────────────────────────
1. Squad > Squad View
2. Click "Customize" button
3. Add columns:
   - All current per-90 metrics (keep these!)
   - Age
   - Wage
   - Contract Expires
4. File > Export to HTML

Option 2: Use Squad Screen (easier)
───────────────────────────────────
1. Squad (main squad screen)
2. Select all players
3. Ensure columns visible: Age, Wage, Contract, + all per-90 metrics
4. Right-click > Export

Option 3: Provide both exports
──────────────────────────────────
- Keep "Go Ahead - New Format.html" (performance metrics)
- Also export "Squad Info.html" (Age, Wage, Contract)
- Parser can merge the two files
```

**Once you have the proper export, we can proceed immediately.**

---

## 📊 New Format Analysis

### Current State
- **Old Format**: 24 columns (Position, Name, Apps, basic per-90 metrics)
- **New Format**: 29 columns with comprehensive per-90 statistics
- **Parser**: Currently hardcoded for old format column positions

### New Format Columns (29 total)
```
Position Selected, Inf, Name, Position, Apps, Gls, Mins, Ast, Av Rat,
xGP/90, Con/90, Tck/90, ShT/90, Hdrs W/90, Sprints/90, xA/90, NP-xG/90,
OP-KP/90, Drb/90, Conv %, Pr passes/90, Clr/90, Pres C/90, OP-Crs C/90,
Itc, Shts Blckd/90, Hdr %, Pas %, Int/90
```

### ✅ Metrics Availability Check

ALL 17 required metrics for role evaluation are present:

| Metric                | New Format Column | Status |
|-----------------------|-------------------|--------|
| tackles_90            | Tck/90            | ✅     |
| header_win            | Hdr %             | ✅     |
| clearances_90         | Clr/90            | ✅     |
| interceptions_90      | Int/90            | ✅     |
| blocks_90             | Shts Blckd/90     | ✅     |
| prog_passes_90        | Pr passes/90      | ✅     |
| dribbles_90           | Drb/90            | ✅     |
| key_passes_90         | OP-KP/90          | ✅     |
| xassists              | xA/90             | ✅     |
| crosses_90            | OP-Crs C/90       | ✅     |
| sprints_90            | Sprints/90        | ✅     |
| shots_on_target_90    | ShT/90            | ✅     |
| conversion_pct        | Conv %            | ✅     |
| pass_pct              | Pas %             | ✅     |
| pressures_90          | Pres C/90         | ✅     |
| xg_90                 | NP-xG/90          | ✅     |
| headers_won_90        | Hdrs W/90         | ✅     |

---

## 🚧 Identified Challenges

### ⚠️ Challenge 1: CRITICAL - Missing Essential Columns
**Impact**: CRITICAL 🔴
**Effort**: Requires user action

**Problem**: New format is missing **THREE CRITICAL** columns:
- ❌ **Age** - No player age data
- ❌ **Wage** - No wage data (£X p/w)
- ❌ **Contract Expires** - No contract end date

**Impact on Features**:
1. **Value Score Calculation**: Cannot calculate without wage data
2. **Age-based Recommendations**: Cannot suggest "veteran" vs "prospect" strategies
3. **Contract Warnings**: Cannot flag expiring contracts or transfer list suggestions

**Root Cause**: The "Go Ahead - New Format.html" appears to be from a specific Squad View export that focuses only on performance metrics, not player information.

**Solutions**:

**Option A (RECOMMENDED): Export Different View**
```
In Football Manager:
1. Go to Squad > Squad View
2. Select "Squad Information" view (not "Performance" view)
3. Customize columns to include:
   - All per-90 metrics (Tck/90, Drb/90, etc.)
   - Age
   - Wage
   - Contract Expires
4. Export to HTML
```

**Option B: Manual Column Addition**
- User manually adds Age, Wage, Contract columns to CSV
- Import CSV instead of HTML
- More work, less automated

**Option C: Proceed Without Critical Data**
- Focus purely on role recommendations (no value scoring)
- Remove age-based logic
- Remove contract warnings
- **Major feature reduction**

**Recommendation**: ⏸️ **PAUSE** until proper export format is obtained. Role evaluation is still possible, but value scoring (the core feature) requires wage data.

### Challenge 2: Parser Update Required
**Impact**: Medium
**Effort**: 1 hour

**Problem**: Current parser (`fm_parser.py`) expects old format with different column order.

**Solution**:
```python
# Option A: Make parser flexible to detect format
def _detect_format(self, headers):
    if 'Pr passes/90' in headers:
        return 'new_format'
    else:
        return 'old_format'

# Option B: Create separate parser for new format
class FMHTMLParserV2:
    """Parser for new FM export format (2026+)"""
```

**Recommendation**: Option B (cleaner, easier to maintain)

### Challenge 3: Player Model Extension
**Impact**: Low
**Effort**: 30 minutes

**Problem**: Player dataclass needs new fields for additional metrics.

**Solution**:
```python
@dataclass
class Player:
    # ... existing fields ...

    # NEW FIELDS from new format
    mins: Optional[int] = None              # Total minutes played
    xgp_90: Optional[float] = None          # xG Prevented/90
    tck_90: Optional[float] = None          # Tackles/90 (was k_tck_90)
    shot_90: Optional[float] = None         # Shots on Target/90
    hdrs_w_90: Optional[float] = None       # Headers Won/90
    sprints_90: Optional[float] = None      # Sprints/90
    xa_90: Optional[float] = None           # xAssists/90
    np_xg_90: Optional[float] = None        # Non-Penalty xG/90
    op_kp_90: Optional[float] = None        # Open Play Key Passes/90
    conv_pct: Optional[float] = None        # Conversion %
    pr_passes_90: Optional[float] = None    # Progressive Passes/90
    clr_90: Optional[float] = None          # Clearances/90
    pres_c_90: Optional[float] = None       # Pressures Completed/90
    op_crs_c_90: Optional[float] = None     # Open Play Crosses Completed/90
    shts_blckd_90: Optional[float] = None   # Shots Blocked/90
```

---

## 📋 Revised Chunk 1 Plan

### Task 1.1: Update Parser for New Format (1.5 hours)
**Priority**: CRITICAL

1. Create `services/fm_parser_v2.py` for new format
2. Parse all 29 columns with correct mapping
3. Extract standardized metrics (tackles_90, prog_passes_90, etc.)
4. Handle missing wage/contract data gracefully

### Task 1.2: Extend Player Model (30 minutes)
**Priority**: HIGH

1. Add new metric fields to `Player` dataclass
2. Keep backward compatibility with old fields
3. Add helper methods to normalize metric names

### Task 1.3: Create Role Definition System (1 hour)
**Priority**: HIGH

1. Create `models/role_definitions.py`
2. Define 12 roles with metric requirements
3. Set thresholds (Good/OK/Poor) for each metric per role
4. Define role interchangeability

### Task 1.4: Build Role Evaluator (1.5 hours)
**Priority**: HIGH

1. Create `analyzers/role_evaluator.py`
2. Implement metric scoring logic (0-100 scale)
3. Calculate overall role score
4. Identify strengths and weaknesses

### Task 1.5: Unit Testing (30 minutes)
**Priority**: MEDIUM

1. Test parser with new format file
2. Test role evaluation with sample players
3. Verify metric extraction accuracy

---

## 🎯 Key Decisions Before Proceeding

### Decision 1: Wage Data
**Question**: How should we handle missing wage data?

**Options**:
A. Require wage to be manually added (extra column in FM export)
B. Use dummy wage (£1,000 p/w for all players)
C. Calculate value score without wage (role performance only)

**Recommendation**: Option C initially, add wage support later if needed

### Decision 2: Backward Compatibility
**Question**: Should we maintain support for old format?

**Options**:
A. Support both formats with format detection
B. Only support new format going forward

**Recommendation**: Option B (cleaner, user can always re-export from FM)

### Decision 3: Threshold Values
**Question**: How to determine "Good/OK/Poor" thresholds?

**Options**:
A. Use provided values in plan (based on your FM experience)
B. Calculate from sample squad data (percentiles)
C. Make thresholds configurable

**Recommendation**: Start with Option A, allow adjustment later

---

## ✅ Pre-Flight Checklist

- [x] New format file received and analyzed
- [x] All required **performance metrics** confirmed available
- [x] Player model structure understood
- [x] Parser architecture understood
- [x] Role taxonomy finalized (12 roles)
- [ ] Threshold values finalized for all roles
- [ ] **BLOCKER 🔴**: Age, Wage, Contract data missing from export
- [ ] **BLOCKER 🔴**: User needs to provide correct FM export with player info

---

## 🚀 Recommendation

### Option A: WAIT for Proper Export (RECOMMENDED ⭐)

**Wait until you provide:**
- New FM export with Age, Wage, Contract columns
- Keep all the current per-90 metrics
- Then proceed with full Chunk 1 implementation

**Pros:**
- ✅ Full feature set (value scoring + role recommendations)
- ✅ No technical debt or workarounds
- ✅ Clean implementation from start

**Timeline:** 5-6 hours after receiving proper data

---

### Option B: Proceed with Limited Scope (NOT RECOMMENDED)

**Implement Chunk 1 with constraints:**
- ✅ Role evaluation works
- ✅ Role recommendations work
- ❌ No value score calculation
- ❌ No age-based recommendations
- ❌ No contract warnings

**Pros:**
- Can start immediately
- Role system still valuable

**Cons:**
- Missing core value score feature
- Need to refactor later when wage data arrives
- Reduced user value

**Timeline:** 4-5 hours, but limited functionality

---

### Option C: Use Dummy Data for Development

**Use placeholder values:**
- Age: Random 18-35
- Wage: £1,000-£50,000 based on performance
- Contract: All expire 2027

**Pros:**
- Can develop and test full system
- Easy to swap with real data later

**Cons:**
- Value scores will be inaccurate
- User can't use for real analysis yet

**Timeline:** 5-6 hours for development

---

## 📝 Next Steps

### IMMEDIATE ACTION REQUIRED:

**Please provide one of the following:**

1. ✅ **New FM HTML export** with Age, Wage, Contract + all per-90 metrics
2. ✅ **Two exports**: Performance metrics (current) + Player info (new)
3. ✅ **Confirm**: Proceed with Option B or C above

### Once Data Received:

1. Merge/update parser for new format
2. Implement role definition system
3. Build role evaluator
4. Test with your squad data
5. Review results together

---

## ❓ Questions for You

**CRITICAL:**
1. Can you export Age/Wage/Contract from FM? (Should be possible in Squad screen)
2. Which option do you prefer: A (wait), B (limited), or C (dummy data)?

**PLANNING:**
3. Are you comfortable with 5-6 hour estimate for Chunk 1?
4. Do you want to see role evaluation results before proceeding to Chunk 2?

---

## 📊 Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Performance Metrics** | ✅ Perfect | All 17 required metrics available |
| **Player Info** | 🔴 Missing | Age, Wage, Contract not in export |
| **Role System Design** | ✅ Ready | 12 roles fully planned |
| **Parser Architecture** | ⚠️ Needs Update | Easy fix once format confirmed |
| **Ready to Start?** | ⏸️ **PAUSED** | Waiting for proper FM export |

**Bottom Line:** The refactoring plan is excellent and fully feasible. We just need the right data export from FM to proceed. Once you provide that, I can complete Chunk 1 in 5-6 hours.
