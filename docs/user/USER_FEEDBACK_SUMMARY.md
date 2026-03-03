# User Feedback Analysis - Summary

**Period**: September - December 2025
**Source**: Email support exchanges (ETH IDP course + international users)
**Total Issues Analyzed**: ~25 unique issue patterns from 15+ user groups

---

## Quick Access

- **For Users**: [FAQ_TROUBLESHOOTING.md](FAQ_TROUBLESHOOTING.md) - Searchable Q&A knowledge base
- **For Developers**: [SOFTWARE_IMPROVEMENTS_FROM_USER_FEEDBACK.md](SOFTWARE_IMPROVEMENTS_FROM_USER_FEEDBACK.md) - Prioritized improvement roadmap

---

## Issue Distribution

### By Category
```
Database/Input Issues          ████████████████ 35%
Error Message Clarity          ████████████ 25%
Cloud Platform UX              ████████ 20%
Documentation Gaps             ██████ 15%
Workflow Integration           ██ 5%
```

### By User Impact (Time Lost)
```
Long simulation failures       ████████████████████ 40%
  (hours wasted before error discovered)

Database definition errors     ████████████ 25%
  (trial-and-error cycles)

File download issues           ████████ 15%
  (network instability)

Documentation search time      ██████ 10%
  (finding solutions)

Other                          ████ 10%
```

### By Resolution Difficulty
```
Easy (user self-solvable with FAQ)     ██████████ 30%
Medium (support guidance needed)        ████████████████ 45%
Hard (requires expert intervention)     ██████████ 25%
```

---

## Top 10 Most Frequent Issues

1. **Missing/Invalid Database References** (12 occurrences)
   - ASSEMBLIES reference non-existent COMPONENTS
   - Missing temperature parameters in HVAC systems
   - Fix: Database validator + better error messages

2. **Geometry Validation Errors** (10 occurrences)
   - Duplicate building names
   - Unclosed polygons
   - Self-intersecting shapes
   - Fix: Pre-flight geometry validator

3. **Schedule Configuration Errors** (8 occurrences)
   - Heating/cooling schedules turned OFF
   - No space heating demand despite valid system
   - Fix: Schedule validator + default checks

4. **Street Network Connectivity** (7 occurrences)
   - Disconnected building clusters
   - Arc/curve geometries not supported
   - Fix: Better Rhino/GH import validation

5. **Large File Download Failures** (6 occurrences)
   - Network timeout on >5GB files
   - No resume capability
   - Fix: Chunked downloads + selective export

6. **Supply System Component Capacity** (6 occurrences)
   - Capacity exceeds component limits
   - Wrong component type for load size
   - Fix: Capacity range hints in UI

7. **Cloud Input Editing Issues** (5 occurrences)
   - Changes not persisting
   - No confirmation of save
   - Fix: Change tracking + explicit save confirmation

8. **Long Simulation Runtimes** (5 occurrences)
   - Appears stuck but actually failing silently
   - Non-fatal warnings prevent exit
   - Fix: Progress tracking + warning visibility

9. **Year Field Type Errors** (4 occurrences)
   - Float vs integer (1960.0 vs 1960)
   - CSV formatting inconsistencies
   - Fix: Type coercion + validation

10. **Empty Use Type Fields** (3 occurrences)
    - Blank use_type2/3 cells cause issues
    - Fix: Auto-fill with "NONE"/0 + validator

---

## User Quotes (Representative Feedback)

> "We spent 6 hours debugging before realizing we had duplicate building names."
> — Matteo & Gino, Oct 2025

> "The error message said 'KeyError: name' but didn't tell me what to fix."
> — Multiple users

> "I tried downloading my results 5 times. Each time it stopped at ~80% after 30 minutes."
> — Yuyao (Tongji), Dec 2025

> "I changed the database in the cloud, but when I ran the simulation, it used the old values."
> — Bianca, Oct 2025

> "CEA is powerful but has a steep learning curve. Better error messages would help a lot."
> — Ana, Nov 2025

---

## Success Patterns (What Worked Well)

### Positive Feedback:
1. **Teaching Assistant Support**
   - Fast response times (usually <24h)
   - Detailed troubleshooting guidance
   - Willingness to debug on user's behalf

2. **Documentation (when found)**
   - City Energy Analyst docs comprehensive
   - How-to guides valuable
   - Need better discoverability

3. **Grasshopper Integration**
   - Visual workflow appreciated
   - Iteration speed for geometry changes

4. **CEA-4 Format Helper**
   - Catches many database errors
   - Could be more comprehensive

### User Workarounds (Organic Solutions):
- "Run 1-2 test buildings before full scenario" (emerged independently)
- "Download-edit-reupload instead of cloud editing" (reliability)
- "Keep Zurich database as reference" (copy-paste-modify pattern)
- "Duplicate base scenario for variants" (workflow optimization)

---

## Geographic & Context Insights

### User Profiles:
- **ETH IDP Students** (60% of issues)
  - First-time CEA users
  - Tight deadlines (semester project)
  - Complex scenarios (200+ buildings)

- **International Students** (30%)
  - Language barriers (Chinese, Greek, etc.)
  - Different architectural standards (Singapore, China)
  - Limited access to on-site support

- **Advanced Users** (10%)
  - Requesting API/automation features
  - Pushing CEA to limits (district-scale optimization)

### Common Scenarios:
- **Urban regeneration projects** (most common)
- **Retrofit analysis** (baseline vs intervention)
- **District heating/cooling networks**
- **Emission reduction pathways**

---

## Knowledge Gaps (Where Documentation Fails)

### Topics with Highest Support Request Rate:
1. **HVAC system definition** (especially temperature parameters)
2. **Supply system vs HVAC system** (conceptual confusion)
3. **Street network requirements** (geometry types, connectivity)
4. **Archetype vs Assembly vs Component** (hierarchy)
5. **When to re-run Archetype Mapper** (workflow)

### Documentation That Would Help Most:
- ✅ **Video tutorials** for common workflows
- ✅ **Decision trees** ("Which heating system should I use?")
- ✅ **Annotated examples** (real project walkthrough)
- ✅ **Troubleshooting flowcharts** (visual debugging)
- ✅ **Database cheat sheet** (quick reference for definitions)

---

## Recommendations

### Immediate Actions (No Code Changes Needed)
1. ✅ Publish FAQ/Troubleshooting doc (created: `FAQ_TROUBLESHOOTING.md`)
2. ✅ Link FAQ from common error messages
3. ✅ Create "Common Pitfalls" video series (5-10 min each)
4. ✅ Add "Validation Checklist" to documentation
5. ✅ Improve Moodle/course materials with FAQ links

### Short-term Development (3-6 months)
1. ✅ Enhanced error messages (Priority 1.2)
2. ✅ Pre-flight input validator (Priority 1.1)
3. ✅ Database reference checker (Priority 1.3)
4. ✅ Improved download UI (Priority 2.1)

### Medium-term Development (6-12 months)
1. ✅ Smart database editor (Priority 3.2)
2. ✅ Simulation progress tracking (Priority 2.3)
3. ✅ Change tracking system (Priority 2.2)
4. ✅ Contextual help system (Priority 3.1)

### Long-term Vision (12+ months)
1. ✅ Scenario branching & comparison (Priority 4.1)
2. ✅ Automated test suite (Priority 4.2)
3. ✅ Custom validation rules (Priority 5.1)
4. ✅ Enhanced API for automation (Priority 5.2)

---

## ROI Estimation

### Current Support Load:
- ~3-5 support emails per student group per semester
- ~15 active groups = 45-75 support interactions
- Average resolution time: 2-4 hours per issue
- **Total: ~100-200 hours of TA time per semester**

### Expected Impact of Improvements:

#### Phase 1 (Quick Wins)
- FAQ doc → **-30% support emails** (users self-solve)
- Better error messages → **-20% resolution time** (faster debugging)
- Input validator → **-40% preventable errors**
- **Net savings: ~80-120 hours per semester**

#### Phase 2 (UX Improvements)
- Smart database editor → **-60% database errors**
- Progress tracking → **-30% "is it stuck?" emails**
- Change tracking → **-100% "changes not saving" issues**
- **Additional savings: ~40-60 hours per semester**

#### Phase 3 (Advanced Features)
- Enables **new user segments** (consulting, enterprise)
- Reduces **learning curve** (faster onboarding)
- Enables **research workflows** (automated experiments)
- **Strategic value**: Expand CEA adoption beyond academia

---

## Files Generated

1. **FAQ_TROUBLESHOOTING.md** (~8000 words)
   - Comprehensive Q&A knowledge base
   - Organized by error category
   - Searchable, linkable sections
   - Real examples from user issues

2. **SOFTWARE_IMPROVEMENTS_FROM_USER_FEEDBACK.md** (~6000 words)
   - Prioritized improvement roadmap
   - Technical implementation suggestions
   - ROI analysis for each improvement
   - 3-phase development plan

3. **USER_FEEDBACK_SUMMARY.md** (this file)
   - Executive summary
   - Issue statistics
   - Key insights & recommendations

---

## Next Steps

### For Teaching/Support Team:
1. Review FAQ doc for accuracy
2. Add FAQ link to Moodle course materials
3. Update email templates to reference FAQ sections
4. Collect additional issues for FAQ expansion

### For Development Team:
1. Review SOFTWARE_IMPROVEMENTS doc
2. Prioritize Phase 1 features for next release
3. Estimate development effort
4. Set up metrics tracking (support email volume, error rates)

### For Documentation Team:
1. Integrate FAQ into official CEA docs
2. Create video tutorials for top 5 issues
3. Add troubleshooting flowcharts
4. Update error message text with FAQ links

---

## Conclusion

The user feedback reveals that **CEA is powerful but has usability barriers**:

✅ **Strengths**:
- Comprehensive simulation capabilities
- Active support community
- Good documentation (when found)

⚠️ **Opportunities**:
- Shift-left error detection (catch issues early)
- Improve error message clarity (actionable guidance)
- Better cloud platform UX (downloads, editing, visibility)
- Enhanced discoverability of help resources

**The path forward**: Address these systematically through the 3-phase roadmap. Phase 1 alone (3 months effort) can reduce support burden by 40%, paying for itself in one semester.

**User retention insight**: Most frustrated users encountered **3+ consecutive failures** before seeking help. Preventing that first failure is critical for building user confidence.
