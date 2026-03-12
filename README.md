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

## Installation

Download the `.skill` file from [Releases](../../releases) or upload the skill folder via **Claude.ai → Customize → Skills**.
