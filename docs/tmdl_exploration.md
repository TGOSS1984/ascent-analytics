# Exploring TMDL for the Semantic Model

`docs/powerbi_lessons_learned.md` named **Tabular Editor + TMDL** as the fix for the core problem documented there: the `.pbix` is a binary blob, so the semantic model — relationships, measures, hierarchies — can't be diffed, reviewed, or rolled back with `git` the way `src/` and `sql/` can. This doc is the follow-up exploration: what TMDL actually is, what's changed in the tooling since that line was written, and a concrete recommendation for this project.

## The landscape has moved since the original note

The original note assumed **Tabular Editor** (a third-party external tool) was required to get TMDL out of a `.pbix`. That's no longer the full picture:

- **PBIP (Power BI Project format) went GA in Power BI Desktop in February 2026.** It's a folder-based, text-first save format — `File → Save As → Power BI Project (.pbip)` — that replaces the binary `.pbix` for source-controlled development, no external tool required.
- Within PBIP, the semantic model can itself be stored as **TMDL** (rather than the older single-file TMSL/`model.bim` JSON) by checking *"Store semantic model using TMDL format"* under `Options → Preview features`. This is what actually solves the diffability problem: tables, measures, relationships, and hierarchies each become their own small `.tmdl` text file instead of one opaque blob.
- **Tabular Editor is still genuinely useful on top of PBIP** — its Best Practice Analyzer (BPA) rules and bulk-editing UI are worth having for a larger model — but it's no longer the *only* way in. For a single-developer portfolio project like this one, native PBIP + TMDL support in Power BI Desktop is enough on its own.

So the practical recommendation for this project is: **native PBIP with TMDL, no external tool needed.** Tabular Editor becomes an optional later addition (see "Where Tabular Editor would still add value" below), not a prerequisite.

## What the conversion actually involves

1. `File → Options and settings → Options → Preview features` — enable **"Power BI Project (.pbip) save option"** and **"Store semantic model using TMDL format"**. Restart Power BI Desktop.
2. Open `powerbi/ascent_analytics.pbix`, then `File → Save As → Power BI Project (.pbip)`.
3. Power BI Desktop writes a folder in place of the single binary file:

   ```
   ascent_analytics.pbip
   ascent_analytics.Report/          # visuals, layout, theme wiring
   ascent_analytics.SemanticModel/
     definition/
       database.tmdl
       model.tmdl
       relationships.tmdl
       tables/
         FactBookings.tmdl
         DimRoute.tmdl
         DimDate.tmdl
         ...one file per table...
   ```
4. Everything under `.SemanticModel/definition/` is now plain text — reviewable in a pull request, diffable with `git diff`, greppable, mergeable (with the usual caveats — see below).

## What a real table's TMDL looks like, using this project's own model

This isn't hypothetical — translating a couple of real objects from `powerbi/dax_measures.md` and `powerbi/readme.md`'s relationship table into their TMDL shape:

**A measure**, from `FactBookings.tmdl` (compare to the DAX in `dax_measures.md`):

```
measure Revenue =
        CALCULATE(SUM(FactBookings[total_price]), FactBookings[status] = "confirmed")
    formatString: £#,0

measure 'Cancellation Rate' =
        DIVIDE([Cancelled Bookings], [Total Bookings])
    formatString: 0.0%
```

**A relationship**, from `relationships.tmdl` (the `DimRoute → DimRegion` link that carries region filtering onto `FactBookings`, per the "Why FactBookings → DimRegion is inactive" note in `powerbi/readme.md`):

```
relationship a1b2c3d4-...
    fromColumn: DimRoute.region_id
    toColumn: DimRegion.region_id

relationship e5f6g7h8-...
    isActive: false
    fromColumn: FactBookings.region_id
    toColumn: DimRegion.region_id
```

The second block is exactly the kind of thing that was invisible before: right now, "this relationship is deliberately inactive, and here's why" lives only in prose in `powerbi/readme.md`, disconnected from the model itself and easy to silently break on a reimport. In TMDL, `isActive: false` is a line in a reviewable file sitting next to the relationship it describes — a PR that flips it to `true` (or deletes the inactive block by accident during a merge) is now a visible, diffable change instead of a silent one.

## What this does and doesn't fix

**Fixes:**
- Code review on semantic model changes — a PR that adds a measure or relationship is now readable, not "trust me, I checked it in the app."
- A real diff when something changes, instead of the current situation (`git status` shows `ascent_analytics.pbix` as one opaque modified blob).
- The specific "which relationships are deliberately inactive and why" knowledge becomes machine-checkable rather than living only in `powerbi/readme.md` prose.

**Doesn't fix, and worth being honest about:**
- **The rebuild-cost problem in `powerbi_lessons_learned.md` is a Power Query schema-detection issue, not a file-format issue.** Reimporting a CSV with new columns still forces a table delete-and-recreate in Power BI Desktop's UI, and that still cascades to relationships/measures/hierarchies homed on that table, exactly as documented. TMDL makes the *aftermath* diffable and reviewable — it doesn't prevent the cascade from happening in the first place. The `POWERBI_REBUILD_CHECKLIST.md` this project already has is still the actual mitigation for that specific problem.
- **TMDL merge conflicts are still real.** Splitting one table per file helps (two people editing different tables won't conflict), but two people adding different measures to the *same* table's `.tmdl` file will still produce a conflict that needs manual resolution, same as any text-format merge.
- **The Report half of PBIP (`.Report/`) is much less pleasant to review than the SemanticModel half.** Visual layout/positioning is stored in a way that's technically text but not meaningfully human-diffable — this project's actual pain point (measures, relationships) lives in `.SemanticModel/`, which is the half that benefits.

## Where Tabular Editor would still add value

Not needed to get the diffability win above, but worth naming as a genuine later step if this project's model kept growing:
- **Best Practice Analyzer (BPA)** — a rules engine that flags things like unused columns, missing descriptions, or measures with inconsistent formatting, runnable in CI against the `.tmdl` files without opening Power BI Desktop at all.
- **Bulk editing** — renaming a column referenced in 15 measures, or applying a formatting convention across every measure at once, is a multi-select-and-edit operation in Tabular Editor rather than 15 individual clicks in Power BI Desktop's UI.

Neither is a blocker for this project's current size (29 measures, 12 tables) — they're the natural next step *if* the model kept growing past what one person can comfortably scan by eye.

## Recommendation

1. Enable PBIP + TMDL in Power BI Desktop and re-save `ascent_analytics.pbix` as a `.pbip` project (steps above).
2. Commit the resulting `ascent_analytics.pbip` and `ascent_analytics.SemanticModel/` folder to the repo; keep the original `.pbix` too for anyone who just wants to double-click and open it without enabling preview features.
3. Add a `.gitignore` entry for Power BI Desktop's local cache files inside the project folder (`*.pbi.cache`, `.pbi/localSettings.json`) — these are machine-local, not meant to be committed.
4. Leave Tabular Editor as a named-but-not-yet-needed next step, same honest framing as this document's predecessor — the model doesn't need BPA or bulk editing yet, but the path is clear if it grows.

This keeps the project's original claim accurate without overstating it: the semantic model *can* now live as reviewable text next to the Python and SQL, using tooling that's native to Power BI Desktop as of 2026 rather than requiring a separate download.