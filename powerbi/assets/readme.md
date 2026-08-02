# Branding Assets

Beyond the colour theme (`ascent_analytics_theme.json`, see step 6 of `README.md`), this folder carries the rest of the UK Summit Guides visual identity across into the Power BI report. Two of these are pulled directly from the live site's own asset folder — reused, not recreated. One is newly built, because it didn't exist as a file.

| File | Source | What it is |
|---|---|---|
| `logo.png` / `logo.svg` | **Newly built** | The site's mountain mark is drawn with pure CSS (two overlapping clip-path triangles + a skewed "crevasse" cut — see `frontend/src/components/ui/BrandLogo.jsx` and `.brand-logo__*` rules in `frontend/src/styles/layout.css`), so no image file of it exists anywhere. This SVG replicates that exact geometry, paired with an "ASCENT ANALYTICS / DATA & BI PLATFORM" wordmark rather than the site's own name — same visual identity, correct product name. |
| `cover_hero_winter.jpg` | `frontend/public/images/winter/hero-winter.jpg` (UK Summit Guides repo) | Real mountain photography from the live site. Good for a report cover page, too visually busy to sit behind actual charts. |
| `topography_texture.jpg` | `frontend/public/images/patterns/topography-winter.jpg` (UK Summit Guides repo) | A subtle dark contour-line pattern used as a background texture on the live site. Optional — only use it if you want extra texture; the theme's solid dark background already works well on its own. |

## How to use each one

### 1. Logo on every page (recommended)

Insert tab → **Image** → select `logo.png` → drag it to the top-left corner of the page, roughly matching the site's header position. Resize to about 180×36px so it doesn't compete with the page title. Once placed on one page, **copy and paste it onto every other page** (Ctrl+C / Ctrl+V) rather than re-inserting — keeps positioning identical across pages.

`logo.png` has a transparent background, so it sits directly on the dark theme without a visible box around it. If you ever need it as a vector instead (e.g. for a print export), `logo.svg` is the same mark at any size without quality loss — Power BI's Image visual may or may not render SVG depending on your version; PNG is the safe default.

### 2. Cover page (optional, but a nice touch)

Add a new page, name it "Cover" or "Home", drag it to be the first tab. Format the page → Canvas background → browse for `cover_hero_winter.jpg` → set image fit to "Fit" or "Fill" → **increase transparency to around 60-70%** so it reads as a moody backdrop rather than a distracting photo. Add a text box with the report title ("Ascent Analytics") and a one-line subtitle over the top. Don't put any actual charts on this page — it's a title screen, not a dashboard.

If you want a summer-toned alternative, the same photo exists as `hero-summer.jpg` in the UK Summit Guides repo at `frontend/public/images/summer/` — not copied here, but grab it the same way if you'd rather the cover lean warm instead of cold.

### 3. Topography texture (optional, use sparingly)

Only apply this if the solid dark background feels too flat once you've got real dashboards built — it's easy to overdo. Same mechanism as the cover page (Format page → Canvas background → browse for `topography_texture.jpg`), but keep transparency very high (85-90%+) on actual dashboard pages, so it reads as a faint texture, not a pattern that competes with your data. If in doubt, leave it off — the theme's solid background is already doing the branding work through colour and typography alone.