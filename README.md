# claude-skills

Custom Claude skills for use with Claude.ai and Claude Code.

## Skills

### [`mckinsey-deck-check`](skills/mckinsey-deck-check/SKILL.md)

Audits a PowerPoint presentation against McKinsey's Hypothesis-Driven Framework and Pyramid Principle across 10 dimensions:

1. Fact Foundation
2. Initial Hypothesis
3. Issue Tree Integrity (MECE)
4. Big Picture Synthesis
5. SPQA Stage-Setting
6. Pyramid Principle
7. Impact Clarity
8. Number Consistency
9. Data–Narrative Alignment
10. Language & Formatting Polish

Produces a ranked issue plan (Critical / Important / Polish), waits for approval, then executes fixes directly in the PPTX.

**Triggers:** `/mckinsey-deck-check`, "check my deck", "review this presentation", "QC my slides", "is this McKinsey-ready"

---

### [`storytelling-deck-checker`](skills/storytelling-deck-checker/SKILL.md)

Audits a PowerPoint presentation against the **Storyteller Tactics** framework by Steve Rawling (Pip Decks) across 10 narrative dimensions:

1. Audience Clarity
2. Story Hook
3. The Dragon & The City
4. Conflict & Stakes
5. Story Arc (Recipe Beats)
6. Hero & Guide Role
7. Movie Time (Vivid Moments)
8. Three is the Magic Number
9. Show & Tell Balance
10. Ending & Call to Action

Starts by asking you to choose a **story recipe** — the arc that gates the entire audit and shapes every fix:

| # | Recipe | Best for |
|---|--------|----------|
| 1 | Man in a Hole | Rescue / recovery / comeback |
| 2 | No Easy Way | Complex change or transformation |
| 3 | Rags to Riches | Hidden value / underdog / discovery |
| 4 | Voyage & Return | Research, exploration, lessons learned |
| 5 | Pitch Perfect POPP | Sales pitch / proposal / funding ask |
| 6 | Let Me Explain | Education, how-to, onboarding |
| 7 | Campfire Story | Culture, values, internal comms |
| 8 | Public Speaking Arc | Keynote / conference / TED-style |

Not sure which recipe fits? Say "help me choose" — the skill reads the deck and recommends one with rationale before proceeding.

Produces a ranked issue plan (Critical / Important / Polish), waits for approval, then rewrites slides directly in the PPTX — with speaker notes on every modified slide explaining which tactic was applied and why.

**Triggers:** `/storytelling-deck-checker`, "check if my deck tells a story", "review my presentation for storytelling", "does my deck hook the audience", "make my slides more compelling"

---

## Installation

Download the `.skill` file from [Releases](../../releases) or upload the skill folder via **Claude.ai → Customize → Skills**.

