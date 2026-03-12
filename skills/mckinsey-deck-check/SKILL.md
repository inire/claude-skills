---
name: mckinsey-deck-check
description: >
  McKinsey-standard presentation quality checker. Use this skill whenever the user
  wants to review, audit, check, QC, or improve a PowerPoint deck — especially
  consulting decks, strategy presentations, board materials, client deliverables,
  or pitch decks. Triggers on: /mckinsey-deck-check, "check my deck",
  "review this presentation", "QC my slides", "is this McKinsey-ready",
  "audit my slides", "make this more McKinsey", or any time the user uploads
  or references a .pptx alongside a request for quality, logic, or narrative
  review. Also use proactively when a PPTX is uploaded without a specific
  task — assume a quality check is wanted.
---

# McKinsey Deck Checker

Audits a PowerPoint presentation against McKinsey's Hypothesis-Driven Framework
and Pyramid Principle across 10 dimensions. Produces a ranked, prioritized issue
plan, waits for user approval, then executes or adjusts.

---

## Step 0 — Ingest

```bash
# Check what was uploaded
ls /mnt/user-data/uploads/

# Extract all text content
python -m markitdown /mnt/user-data/uploads/<filename>.pptx

# Generate visual thumbnails for layout review
python /mnt/skills/public/pptx/scripts/thumbnail.py /mnt/user-data/uploads/<filename>.pptx
```

Read the full extracted text before proceeding. Note slide count, titles, and
rough structure.

---

## Step 1 — Run the 10-Dimension Audit

Evaluate every slide against all dimensions below. Rate each: **PASS**, **WARN**,
or **FAIL**, with a specific finding and slide reference.

### Dimension 1 — Fact Foundation
*"Start by Gathering Facts"*

- Are claims grounded in cited data, interviews, or stated research?
- Is the problem clearly framed with quantitative or qualitative evidence?
- Are sources identified? Are statistics specific (not vague: "many customers...")?
- **Red flag:** Assertions without backing. Undefined baselines. Unsourced market data.

### Dimension 2 — Initial Hypothesis
*"Generate an Initial Hypothesis"*

- Is there a clear, stated hypothesis or thesis — the one thing the deck argues?
- Is it testable/falsifiable, or just a platitude?
- Does the deck open with or anchor to this hypothesis?
- **Red flag:** Deck reports findings without a point of view. No "we believe X."

### Dimension 3 — Issue Tree Integrity (MECE)
*"Build an Issue Tree"*

- Is the central problem decomposed into sub-issues?
- Are sub-issues Mutually Exclusive, Collectively Exhaustive (MECE)?
- Do sub-issues roll up logically to support the main recommendation?
- **Red flag:** Overlapping workstreams. Gaps in logic. One giant catch-all bucket.

### Dimension 4 — Big Picture Synthesis
*"Understand the Big Picture"*

- After the detail, does the deck zoom back out?
- Is there one clear, crisp recommendation (not five hedged options)?
- Is the synthesis distinct from the detail — not just a summary slide?
- **Red flag:** Deck ends in the weeds. No single recommendation emerges.

### Dimension 5 — SPQA Stage-Setting
*"Set the Stage"*

- Does the opening follow: **Situation -> Problem -> Question -> Answer**?
- Situation: establishes context without editorializing
- Problem: why the status quo is unacceptable
- Question: what the client is trying to answer
- Answer: the recommendation, stated upfront
- **Red flag:** Deck opens with company history or agenda slide instead of SPQA.
  Answer buried at the end (reporter structure) instead of upfront.

### Dimension 6 — Pyramid Principle
*"Convince the Stakeholders"*

- Recommendation stated first, then supporting arguments, then evidence?
- Each slide title is an assertion (insight), not a topic label?
- Supporting points directly prove the slide title — not tangential?
- **Red flag:** Titles like "Market Overview" instead of "Market is growing 20% YoY,
  driven by enterprise adoption." Evidence presented before conclusion.

### Dimension 7 — Impact Clarity
*"Make the Impact Clear"*

- Is there a concrete implementation roadmap (what, who, when)?
- Is the outcome quantified (cost reduction, revenue uplift, risk mitigation)?
- Is there a "so what" — what happens if we don't act?
- **Red flag:** Deck ends at recommendation without showing path to value.

### Dimension 8 — Number Consistency
*(from IB deck QC standards)*

- Same figures appear consistently across all slides?
- Units are uniform (all $M or all $B — never mixed)?
- Time periods consistent (FY vs CY, same base year)?
- Percentages add to 100% where they should?
- **Red flag:** Revenue cited as $4.2B on slide 3 and $4B on slide 11.

### Dimension 9 — Data-Narrative Alignment
*(from IB deck QC standards)*

- Do charts and graphs actually support the claims made in adjacent text?
- No contradictions between what a chart shows and what the title claims?
- Are growth claims plausible given the data shown?
- **Red flag:** Chart shows flat growth; title says "Strong momentum."

### Dimension 10 — Language and Formatting Polish
*(consulting register)*

- Titles are assertions, not nouns ("Revenue is declining" not "Revenue")
- No hedging language ("it seems," "perhaps," "might")
- Active voice. Tight bullets. No orphan words.
- Numbers formatted consistently (1,234 not 1234; $4.2M not $4.2m)
- No Lorem Ipsum, brackets [TBD], or placeholder text remaining
- Font sizes consistent at same hierarchy level
- **Red flag:** Passive voice throughout. Topic-label titles. Inconsistent number formats.

---

## Step 2 — Build and Present the Issue Plan

After completing all 10 dimensions, produce this exact output and **stop**. Do
not make any changes yet. Wait for user response.

```
## McKinsey Deck Check -- Issue Plan

**Deck:** [filename]
**Slides reviewed:** [n]
**Overall readiness:** [CLIENT-READY / NEEDS WORK / SIGNIFICANT REWORK]

---

### Critical Issues  (must fix before any client delivery)
| # | Slide(s) | Dimension | Issue | Recommended Fix |
|---|----------|-----------|-------|-----------------|
| 1 | [n]      | [dim name]| [specific finding] | [action] |

### Important Issues  (strongly recommended)
| # | Slide(s) | Dimension | Issue | Recommended Fix |
|---|----------|-----------|-------|-----------------|

### Polish Items  (nice to have)
| # | Slide(s) | Dimension | Issue | Recommended Fix |
|---|----------|-----------|-------|-----------------|

---

**Assessment:** [2-3 sentence narrative on the deck's biggest structural or
narrative weaknesses and overall argument quality]

---
Respond with one of:
- Execute -- apply all fixes
- Execute critical only -- fix Critical issues only
- Skip [#] -- drop an item before executing
- Change [#]: [new direction] -- modify a recommendation
- Explain [#] -- walk through reasoning on a specific issue
- Reprioritize -- re-rank the list based on your input
```

---

## Step 3 — Execute Approved Fixes

Once the user approves (fully or partially), read editing.md from the pptx
skill before making any edits:

```
Read /mnt/skills/public/pptx/editing.md
```

Then for each approved fix:

1. **Unpack the PPTX** using the pptx skill's unpack workflow
2. **Make targeted edits** — slide titles, body text, number alignment, structure
3. **Repack and validate** using markitdown extraction
4. **Convert to images** for visual QA:
   ```bash
   python scripts/office/soffice.py --headless --convert-to pdf output.pptx
   pdftoppm -jpeg -r 150 output.pdf slide
   ```
5. Visually confirm each edited slide looks correct

After execution, deliver a **Fix Summary**:

```
## Fix Summary

Applied [n] of [n] approved fixes.

| # | Slide(s) | Fix Applied | Notes |
|---|----------|-------------|-------|
| 1 | [n]      | [description] | |

Skipped: [list any skipped items with reason]

Note: Validated using LibreOffice. Please review in PowerPoint before
client distribution -- rendering differences may exist.
```

---

## McKinsey Quick-Reference Standards

### Slide Title Conventions
| Topic Label (bad) | Assertion Title (good) |
|-------------------|------------------------|
| Market Overview | Enterprise SaaS market growing 23% YoY, outpacing legacy spend |
| Competitive Landscape | Three competitors hold 60% share; all lack AI-native architecture |
| Financials | Revenue declining 8% YoY driven by customer churn, not price |
| Recommendations | Acquire in-market vs. build: 3-year NPV favors acquisition by $40M |

### SPQA Template
```
Situation:  [Factual, uncontested context -- 1-2 sentences]
Problem:    [Why status quo is unacceptable -- specific, quantified]
Question:   [What the client needs to decide or understand]
Answer:     [Your recommendation -- stated directly, upfront]
```

### Pyramid Principle Structure
```
Recommendation (Governing Thought)
+-- Supporting Argument 1
|   +-- Evidence A (data, case, benchmark)
|   +-- Evidence B
+-- Supporting Argument 2
|   +-- Evidence C
+-- Supporting Argument 3
    +-- Evidence D
```

### Number Consistency Check Pattern
When scanning for number issues, look specifically for:
- Same KPI cited on multiple slides (revenue, market size, headcount, dates)
- Unit mismatches ($M vs $B vs billions)
- Period mismatches (Q3 2024 vs FY2024 vs YTD)
- Percentages that should sum to 100% but do not
- Growth rates that do not reconcile with base and end values

---

## Error Handling

**If markitdown extraction fails:**
```bash
pip install "markitdown[pptx]" --break-system-packages
python -m markitdown /mnt/user-data/uploads/<file>.pptx
```

**If thumbnail generation fails:**
```bash
python scripts/office/soffice.py --headless --convert-to pdf <file>.pptx
pdftoppm -jpeg -r 150 <file>.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

**If the deck is very large (20+ slides):** Audit in batches of 10,
then consolidate findings into a single Issue Plan.

**If the deck has no clear narrative thread:** Flag this as a Critical Issue
under Dimension 2 (no hypothesis) and Dimension 5 (no SPQA) before proceeding
to other checks.
