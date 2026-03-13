# rimworld-log-check

An [Agent Skills](https://agentskills.io) skill for analyzing RimWorld HugsLib player logs. Identifies mod conflicts, exceptions, errors, warnings, and redundant/overlapping mods — and names the responsible mods by name.

Performs the same core analysis as [Orion's rw-log-check tool](https://orionFive.github.io/rw-log-check/), and goes further with mod-specific root-cause explanations, redundancy detection, and priority-ordered fix recommendations.

---

## What it does

Given a RimWorld `output_log.txt` or HugsLib Gist URL, the skill produces a structured report covering:

- **🔴 Exceptions** — code-halting errors with stack trace attribution and culprit mod identification
- **🟠 Startup errors** — broken def references, missing types, XML config issues, outdated mods
- **🟡 Runtime warnings** — NQoL patch failures, Harmony destructive prefixes, version changes, key binding conflicts
- **🔁 Redundant/overlapping mods** — pairs of mods doing the same thing, sourced from NQoL notices, mod-authored COMPAT warnings, and a curated static database
- **📋 Priority action list** — numbered, grouped, specific mod names included wherever identifiable

---

## Usage

### Trigger phrases (Claude auto-detects these)

- "Can you check my log?" + HugsLib Gist URL
- "What's wrong with my mods?"
- "My game keeps crashing"
- "I have errors after startup"
- Pasting a raw log directly into the chat

### Supported input formats

| Format | How to provide |
|---|---|
| **HugsLib Gist** | Paste the URL: `https://gist.github.com/HugsLibRecordKeeper/<id>` |
| **Pastebin / raw URL** | Paste any URL that returns raw log text |
| **Direct paste** | Paste the log content directly into the chat |

### How to generate a HugsLib Gist

1. In RimWorld, press `F12` or open the **HugsLib** menu
2. Click **Share logs** → this opens a Gist URL in your browser
3. Share that URL with Claude

---

## Configuration

No configuration is required. The skill is self-contained.

### Optional: extending the Known Redundancy Database

The static redundancy database lives in `SKILL.md` under the `#### KNOWN REDUNDANCY DATABASE` section. To add a new known mod pair:

1. Open `SKILL.md`
2. Find the `KNOWN REDUNDANCY DATABASE` table
3. Add a row following the format:

```
| Mod A display name / `packageId` | Mod B display name / `packageId` | Feature description | Recommendation |
```

Use `(settings)` at the end of the recommendation when the overlap can be resolved in mod settings rather than requiring one mod to be removed. Include the packageId where known — it enables more reliable matching in pre-1.6 logs where packageIds are available.

---

## Compatibility

| RimWorld version | Log format | Mod list available | Status |
|---|---|---|---|
| 1.4 | Pre-1.6 (Loaded mods: block) | ✅ Full (name + packageId + version) | Supported |
| 1.5 | Pre-1.6 (Loaded mods: block) | ✅ Full (name + packageId + version) | Supported |
| 1.6 | New format (no Loaded mods: block) | ⚠️ Display names only | Supported |

**Requires:** Web fetch capability in the AI client (to retrieve HugsLib Gist URLs). If the client cannot fetch URLs, paste the raw log content directly.

**HugsLib minimum:** 12.0.0

---

## Report structure

```
🛸 RimWorld Log Analysis
├── Metadata (version, mod count, truncation status)
├── 📦 Active Mods (grouped: DLC / frameworks / content)
├── 🔴 Critical — Exceptions
├── 🟠 Errors at Startup
├── 🟡 Errors & Warnings at Runtime
├── 🔁 Redundant / Overlapping Mods   ← only shown if detected
└── 📋 Summary & Priority Actions
```

The redundancy section is omitted entirely when no overlaps are detected, keeping the report clean for healthy load orders.

---

## Redundancy detection

The skill uses three signal sources, listed in descending confidence order:

**1. NQoL Notices** (requires Niilo's QoL mod to be loaded)
Developer-confirmed overlaps emitted at startup. Pattern:
```
NQoL Notice - ModA | ModB - Have overlapping functionality! - <feature>
```

**2. Mod-authored COMPAT warnings** (e.g. Job In Bar)
Mods that self-report conflicts with other mods. Pattern:
```
[ModA] [COMPAT] ModB [packageId] detected.
```

**3. Known Redundancy Database** (static, curated)
Cross-referenced against the active mod list. Covers pairs like:
- Yayo's Animation ↔ Melee Animation
- Job In Bar ↔ Useful Marks
- ResearchPal ↔ ResearchTree
- Color Coded Mood Bar ↔ RimHUD
- Simple Sidearms ↔ Dual Wield
- All NQoL feature overlaps (shelf storage, room size, minification, etc.)

---

## Known limitations

- **1.6 mod lists**: The 1.6 log format doesn't include packageIds or mod counts in the same block as earlier versions. Display names are extracted on a best-effort basis — matching against the Known Redundancy Database is less reliable for 1.6 logs when packageIds are absent.
- **Static DB drift**: The Known Redundancy Database requires manual updates as mods merge, split, or change behavior. NQoL and COMPAT signals are self-updating since they're generated at runtime by the mods themselves.
- **Log truncation**: If HugsLib hits its message limit (`Reached max messages limit`), errors after that point are invisible. The skill flags this prominently.
- **Namespace attribution**: For unknown exceptions, mod attribution is by namespace (e.g. `VanillaExpanded`), not display name. These are flagged clearly.

---

## Spec compliance

This skill follows the [agentskills.io specification](https://agentskills.io/specification):

- `name`: `rimworld-log-check` — lowercase, hyphens only, ≤64 chars ✅
- `description`: ≤1024 chars, describes what it does and when to trigger ✅
- `license`: MIT ✅
- `compatibility`: Environment requirements documented ✅
- `metadata`: Version and RimWorld version range included ✅

---

## License

MIT
