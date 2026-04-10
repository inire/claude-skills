---
name: storytelling-deck-checker
description: >
  Audits a PowerPoint presentation against the Storyteller Tactics framework (Steve Rawling / Pip Decks).
  Use this skill whenever the user runs /storytelling-deck-checker, uploads a .pptx file for story review,
  or asks phrases like "check if my deck tells a story", "review my presentation for storytelling",
  "is my deck story-driven", "does my presentation hook the audience", or "make my deck more compelling".
  Asks the user to select a story recipe FIRST, then audits and scores the deck against that specific arc,
  produces a ranked issue plan (Critical / Important / Polish), waits for approval, then executes
  fixes directly in the PPTX. Always use for any deck audit framed around narrative, story,
  engagement, persuasion, or audience connection — even if "storytelling" isn't said explicitly.
---

# Storyteller Tactics Deck Checker

Audits a PowerPoint deck against the **Storyteller Tactics** framework by Steve Rawling (Pip Decks).
Multi-stage workflow: recipe selection → ingest → audit → plan → approve → fix → deliver.

---

## Stage Map

There are two valid execution paths depending on whether the user knows their recipe upfront.

### Path A — User knows their recipe

```
0A. Present recipe menu → wait for selection
1.  Ingest deck
2.  Audit (scored against chosen recipe)
3.  Issue plan → wait for approval
4.  Fix
5.  Deliver
```

### Path B — User says "help me choose"

```
0B-i.  Acknowledge; ingest deck immediately (need content to recommend)
0B-ii. Analyse deck and recommend a recipe with a one-paragraph rationale
0B-iii. Wait for user to confirm or override
1.     Audit (scored against confirmed recipe)
2.     Issue plan → wait for approval
3.     Fix
4.     Deliver
```

**The recipe must be confirmed by the user before the audit begins — in both paths.**

---

## Stage 0 — Recipe Selection

### 0A — Standard path (user picks upfront)

Present this menu before touching the file. Wait for the user's reply before proceeding.

```
┌────┬───────────────────────┬──────────────────────────────────────┐
│  # │  Recipe               │  Best for                            │
├────┼───────────────────────┼──────────────────────────────────────┤
│  1 │  Man in a Hole        │  Rescue / recovery / comeback        │
│  2 │  No Easy Way          │  Complex change or transformation    │
│  3 │  Rags to Riches       │  Hidden value / underdog / discovery │
│  4 │  Voyage & Return      │  Research, exploration, lessons      │
│  5 │  Pitch Perfect POPP   │  Sales pitch / proposal / funding    │
│  6 │  Let Me Explain       │  Education, how-to, onboarding       │
│  7 │  Campfire Story       │  Culture, values, internal comms     │
│  8 │  Public Speaking Arc  │  Keynote / conference / TED-style    │
└────┴───────────────────────┴──────────────────────────────────────┘

Reply with a number or name.
Not sure? Say "help me choose" and I'll read the deck and recommend one.
```

---

### 0B — "Help me choose" path

If the user says "help me choose", "not sure", "you decide", or similar:

**Step 0B-i — Ingest the deck immediately** (don't ask any more questions first):

```bash
cp /mnt/user-data/uploads/*.pptx /home/claude/deck-input.pptx
python -m markitdown /home/claude/deck-input.pptx
```

**Step 0B-ii — Recommend a recipe.** Output in this format:

```
I've read the deck. Here's my recommendation:

Recommended recipe: [NAME]

Why: [2–3 sentences explaining what in the deck points to this arc —
cite specific slides, topics, or language patterns. Be concrete.]

Alternative: [NAME] — [one sentence on why this could also work and
what would need to be true for it to be the better choice.]

Confirm this recipe and I'll run the full audit.
Or say "use [alternative]" to switch.
```

**Step 0B-iii — Wait for confirmation.** Do not begin the audit until the user explicitly confirms or redirects. "Sounds good", "yes", "go ahead", or naming the recipe all count as confirmation.

---

### Recipe Definitions

The eight recipes and their beat sequences live in [references/recipes.md](references/recipes.md). Load that file when:

- Running Stage 0B ("help me choose") — to read the beats before recommending
- Running Stage 2 Dimension 5 — to check beats present vs. missing for the chosen recipe
- Running Stage 5 rewrites — to confirm every change reinforces the recipe's arc

---

## Stage 1 — Ingest the Deck

> **Path B note:** If the user said "help me choose", ingestion already happened in Stage 0B-i. Skip the bash commands below and proceed directly to Stage 2 using the content already extracted.

```bash
cp /mnt/user-data/uploads/*.pptx /home/claude/deck-input.pptx
python -m markitdown /home/claude/deck-input.pptx
python /mnt/skills/public/pptx/scripts/thumbnail.py /home/claude/deck-input.pptx
```

Capture: slide count, titles, body text, speaker notes, image-only slides.
Build a slide-by-slide content map before scoring.

---

## Stage 2 — Audit Against the 10 Storyteller Dimensions

Score each dimension ✅ Pass / ⚠️ Weak / ❌ Fail. Cite specific slide numbers. Be direct.

**All 10 dimensions apply to every deck.**
The chosen recipe controls: which dimensions are weighted Critical vs Polish, what "good" looks like for each dimension, and which specific beats to check for in Dimension 5.

---

### Dimension 1 — Audience Clarity
Does the deck show it knows who it's for and what they care about?
- Named or clearly implied audience?
- Deck speaks to their problem / fear / aspiration?
- Language uses "you/your" rather than "we/our"?

Recipe weighting — Critical: POPP, Let Me Explain | Important: all others

---

### Dimension 2 — Story Hook
Does the opening earn attention before explaining anything?
- Does slide 1–3 use a question, paradox, unexpected claim, vivid scenario, or surprising stat?
- Is there a reason to keep watching before the presenter introduces themselves?

Recipe weighting — Critical: Public Speaking Arc, Man in a Hole, POPP | Important: all others

---

### Dimension 3 — The Dragon & The City
Is there a named threat or opportunity (Dragon) and something worth protecting or achieving (City)?
- Dragon = threat, problem, competitor, risk, or inertia
- City = what is at stake: customers, mission, market, the team
- Both must be explicit, not merely implied

Recipe weighting — Critical: Man in a Hole, No Easy Way, Rags to Riches, POPP | Important: all others

---

### Dimension 4 — Conflict & Stakes
Is there a real, felt conflict? Are the stakes high enough to care?
- Conflict drawn from: Hero vs. Nature / Society / Self
- Stakes explicit: what happens if this fails?
- Conflict feels genuine, not manufactured

Recipe weighting — Critical: Man in a Hole, No Easy Way | Important: all others

---

### Dimension 5 — Story Arc (Recipe Beats)
Does the deck follow the chosen recipe's specific beat sequence?
- Name which beats are present, which are missing, which are out of order
- Reference the beat list from the selected recipe in Stage 0

Recipe weighting — **Critical for all recipes.** This is the structural spine.

---

### Dimension 6 — Hero & Guide Role
Is the audience the Hero? Is the presenter positioned as Expert Guide, not the star?
- Audience = protagonist on a journey
- Presenter / product = guide who provides the tool, map, or insight
- Red flag: deck is primarily about the presenter's achievements

Recipe weighting — Critical: POPP, Let Me Explain, Public Speaking Arc | Important: all others

---

### Dimension 7 — Movie Time (Vivid Moments)
Does the deck create scenes the audience can see, not just understand?
- At least one specific, sensory, human-scale story moment
- Abstract claims replaced with concrete examples
- One "Rolls Royce Moment" — the single vivid detail that stands for the whole

Recipe weighting — Critical: Campfire Story, Public Speaking Arc | Important: all others

---

### Dimension 8 — Three is the Magic Number
Is the deck's structure memorable? Are key messages grouped in threes?
- One core message expressible in one sentence
- Supporting points in groups of three where possible
- No cognitive overload (too many bullets, too many sub-points)

Recipe weighting — Critical: Public Speaking Arc | Important: Let Me Explain, POPP | Polish: all others

---

### Dimension 9 — Show & Tell Balance
Do slides and narration complement each other, or duplicate?
- Slides show one thing; spoken layer adds something the image doesn't
- No slide is a wall of text that reads itself aloud
- "Washing line" structure: visual hooks carry the narrative

Recipe weighting — Critical: Public Speaking Arc | Important: all others

---

### Dimension 10 — Ending & Call to Action
Does the deck land? Is the ask specific, earned, and story-grounded?
- Ending resolves the conflict introduced at the start
- Happy Ever After or POPP Promise is vivid and felt
- CTA is specific and follows naturally from the story

Recipe weighting — **Critical for all recipes.**

---

## Stage 3 — Issue Plan

Output the issue plan in this exact format. **Do NOT begin fixing.**

```
═══════════════════════════════════════════════════════════
  STORYTELLER TACTICS AUDIT — [DECK TITLE]
  Recipe: [CHOSEN RECIPE NAME]
  [X] slides  |  Story Score: [X]/10  |  [X] issues found
═══════════════════════════════════════════════════════════

DIMENSION SCORES
──────────────────────────────────────────────────────────
 1. Audience Clarity        [✅/⚠️/❌]  [one-line verdict]
 2. Story Hook              [✅/⚠️/❌]  [one-line verdict]
 3. Dragon & The City       [✅/⚠️/❌]  [one-line verdict]
 4. Conflict & Stakes       [✅/⚠️/❌]  [one-line verdict]
 5. Story Arc — [Recipe]    [✅/⚠️/❌]  [beats present vs. missing]
 6. Hero & Guide Role       [✅/⚠️/❌]  [one-line verdict]
 7. Movie Time              [✅/⚠️/❌]  [one-line verdict]
 8. Three is Magic Number   [✅/⚠️/❌]  [one-line verdict]
 9. Show & Tell Balance     [✅/⚠️/❌]  [one-line verdict]
10. Ending & CTA            [✅/⚠️/❌]  [one-line verdict]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CRITICAL — Story breaks without these
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[C1] Slide X — [Issue title]
     Problem: [What's wrong and why it breaks the chosen recipe]
     Fix: [Specific rewrite or structural change]
     Tactic: [Storyteller Tactic name]
     Recipe beat: [Which beat this fixes]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 IMPORTANT — Significantly weakens engagement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[I1] Slide X — [Issue title]
     Problem: [What's weak]
     Fix: [Specific suggestion]
     Tactic: [Storyteller Tactic name]
     Recipe beat: [Which beat this supports]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵 POLISH — Sharpens and elevates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[P1] Slide X — [Issue title]
     Fix: [Quick improvement]
     Tactic: [Storyteller Tactic name]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Critical: [X]  |  Important: [X]  |  Polish: [X]

[One sentence on the biggest structural gap vs. the chosen recipe.]
[One sentence on what the deck already does well.]

Reply with:
  "fix all"                    → apply every issue
  "fix critical"               → Critical issues only
  "fix critical + important"   → skip Polish
  "fix [C1, C2, I1]"          → specific items only
  "just show me"               → no changes, audit report only
  "change recipe to [X]"       → re-audit against a different arc
```

---

## Stage 4 — Wait for Approval

**DO NOT touch the file until the user replies with an explicit instruction.**

- "just show me" → skip to Stage 6, deliver audit report only, no edits
- "change recipe to [X]" → re-run Stages 2 and 3 using the new recipe

---

## Stage 5 — Fix

Read **/mnt/skills/public/pptx/SKILL.md** and its editing references before making changes.

### Editing Principles

- **Stay in the recipe.** Every rewrite must reinforce the chosen arc's beat sequence. When in doubt, ask: does this change move the story forward along the recipe's beats?
- **Preserve the presenter's voice.** Sharpen, don't replace with generic consulting language.
- **Add speaker notes** to every modified slide: what tactic was applied, which recipe beat it serves, what the presenter should say aloud.
- **Don't over-fix.** If an issue wasn't approved, leave the slide alone.

### Per-Dimension Rewrite Guidance

| Dimension | What to do |
|-----------|-----------|
| Audience Clarity | Rewrite opening to name the audience's specific problem in their own language |
| Story Hook | Replace intro/agenda with a question, surprising stat, or vivid scenario |
| Dragon & City | Add or sharpen a "threat frame" slide in the first third of the deck |
| Conflict & Stakes | Add explicit stakes: "If we don't act, [X] happens by [date/scale]" |
| Story Arc | Reorder or add slides to complete missing beats; add transition language between beats |
| Hero & Guide | Rewrite "we" to "you"; reframe product/service as the tool, not the hero |
| Movie Time | Replace abstract nouns with specific scenes: name a person, a place, a moment |
| Three is Magic Number | Consolidate bullets to three; add a three-part framework slide if appropriate |
| Show & Tell | Strip text from visual slides; move detail to speaker notes |
| Ending & CTA | Rewrite final slide as a vivid Better Place + one specific, earned ask |

### PPTX Edit Process

```bash
# 1. Unpack
python /mnt/skills/public/pptx/scripts/office/unpack.py \
  /home/claude/deck-input.pptx /home/claude/deck-unpacked/

# 2. Edit XML for each affected slide
# (see pptx skill editing.md for element-level guidance)

# 3. Repack
python /mnt/skills/public/pptx/scripts/office/pack.py \
  /home/claude/deck-unpacked/ /home/claude/deck-output.pptx

# 4. Verify
python -m markitdown /home/claude/deck-output.pptx
```

---

## Stage 6 — Deliver

```bash
cp /home/claude/deck-output.pptx \
  /mnt/user-data/outputs/deck-storytelling-checked.pptx
```

Call `present_files` with the output path.

End with a short delivery note:

```
✅ [X] issues fixed  |  Recipe: [NAME]
Story Score: [before]/10 → [after]/10 (estimated)

Strongest element now: [one sentence]
Next step if you want to go further: [one sentence]
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| No file uploaded | Ask user to upload their .pptx file before proceeding |
| File corrupted or unreadable | Report error; offer audit-only mode using pasted text |
| Image-only slides | Note which slides are text-free; flag as Show & Tell gap; audit available text |
| Deck < 5 slides | Run full audit; note which dimensions can't be fully evaluated at this length |
| User unsure which recipe | Ingest the deck first, then recommend a recipe with a one-paragraph rationale, then confirm before proceeding |
| User wants a recipe not on the list | Ask them to describe the arc; map it to the nearest recipe or treat as custom and name the beats explicitly |
