# SCNU Thesis Portal DESIGN.md

## 1. Visual Theme & Atmosphere

`scnu-thesis-portal` should feel like a **trusted academic workbench**, not a playful AI toy, flashy startup landing page, or institutional government portal.

The core visual direction is:

- **IBM for structural rigor**: calm blue-gray hierarchy, clear boundaries, high legibility, obvious information architecture
- **Notion for content tone**: readable long-form blocks, warm restraint, document-first pacing, humane whitespace
- **Apple only as ambient polish**: subtle glow, soft depth, clean surfaces, never cinematic spectacle

The emotional outcome should be:

- credible
- calm
- meticulous
- low-risk
- local-first
- reviewable

Users should feel:

- “This is safe enough for thesis work.”
- “This tool respects process and approval.”
- “This is more like a document operations console than a chatbot.”

Avoid any aesthetic that implies:

- hype
- consumer entertainment
- crypto / fintech urgency
- neon AI futurism
- excessive glassmorphism
- overly friendly SaaS playfulness

## 2. Color Palette & Roles

Use a **cool academic palette** built around slate, paper white, and disciplined blue.

### Core neutrals

- `Paper White`: `#fcfbf8` — primary page paper tone
- `Canvas`: `#f3f5f9` — application background
- `Canvas Deep`: `#e8edf4` — section contrast zones
- `Panel`: `#ffffff` — cards and panels
- `Panel Muted`: `#f7f9fc` — secondary card surfaces
- `Rule`: `#d6dde8` — baseline borders
- `Rule Strong`: `#bcc8d8` — emphasized dividers and active outlines

### Text

- `Ink 900`: `#172033` — primary heading text
- `Ink 700`: `#44526a` — body text
- `Ink 500`: `#6c7a90` — meta text
- `Ink 300`: `#98a4b8` — quiet helper text

### Accent system

- `Academic Blue`: `#244c7d` — primary action, active states, trust anchor
- `Academic Blue Strong`: `#17375e` — pressed and high-emphasis controls
- `Review Blue`: `#dfe9f7` — soft active backgrounds and info blocks
- `Approval Green`: `#3e6b55` — accepted / local-first / safe
- `Approval Green Soft`: `#ebf5ef` — positive surfaces
- `Warning Amber`: `#9a6a12` — caution without alarmism
- `Warning Amber Soft`: `#fff4df` — warning surfaces
- `Risk Red`: `#a95359` — destructive or integrity risk
- `Risk Red Soft`: `#fff0f1` — soft danger surfaces

### Usage rules

- Blue is for trust, progress, and committed actions
- Green is for confirmed-safe / accepted / local-first status
- Amber is for human review or policy boundary reminders
- Red is only for real risk, never decorative emphasis
- Backgrounds stay light; dark surfaces are reserved for code blocks only

## 3. Typography Rules

Typography should balance **tool precision** with **document readability**.

### Font families

- UI sans: `"SF Pro Display", "Inter", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif`
- Reading serif: `"Source Han Serif SC", "Noto Serif SC", "Songti SC", "STSong", serif`
- Mono: `"SFMono-Regular", "JetBrains Mono", "Menlo", monospace`

### Hierarchy

- Hero title: sans, 700-780, dense and stable, no dramatic tracking
- Section titles: serif or serif-leaning display for content-facing sections
- Workbench headings: sans, 650-720, compact, operational
- Body copy: sans for UI descriptions, serif optional for previewed thesis/document blocks
- Meta labels: sans, small, uppercase or tightly controlled small caps tone

### Tone rules

- Prefer shorter Chinese headings with strong nouns
- Never use ultra-light weights for core information
- Do not use oversized marketing typography that overwhelms workflow content
- Long descriptive text should read like product documentation, not ad copy

## 4. Component Styling

### Buttons

- Primary buttons use `Academic Blue`
- Secondary buttons are muted paper buttons with strong borders
- Buttons must feel dependable, not bubbly
- Radius should be moderate, not pill-heavy by default

### Cards and panels

- Panels should have visible borders and subtle shadow, like organized paper modules
- Use section headers and small eyebrow labels to create scan order
- Prefer crisp edges with medium radii over fully rounded consumer cards

### Inputs and upload surfaces

- Inputs should feel like structured document fields
- Use stronger resting borders than typical marketing pages
- Active state is controlled blue outline, not glowing neon halo
- Upload areas should read like “intake desk” or “submission surface”

### Status badges

- Compact, quiet, legible
- Clear semantic color usage
- Never use saturated candy colors

### Preview areas

- Thesis previews should feel closer to editorial review sheets than app dashboards
- Use serif selectively inside previewed content blocks
- Distinguish preview content from control chrome

## 5. Layout Principles

The product has two distinct layout modes:

### Public site

- Reads like a **credible product brief**
- Hero should explain value, boundary, and next action immediately
- One primary action, a few secondary routes
- Public sections should alternate between explanation, process, capability, and privacy boundary
- Marketing energy stays low; clarity stays high

### Workbench

- Reads like a **three-column review console**
- Left = project/file intake
- Center = current version / preview / timeline
- Right = agent output / proposals / provider controls
- Important summaries should surface above the fold as compact overview cards

### Spacing

- Use larger spacing between sections, tighter spacing within operational clusters
- Group by meaning, not by decoration
- Empty space should create calm, not theatrical luxury

## 6. Depth, Motion & Atmosphere

Depth should be subtle and professional.

- shadows are soft and short
- borders do most of the separation work
- blur can exist, but only lightly and only in top surfaces
- ambient gradients should sit in the far background

Motion rules:

- small hover lift
- gentle opacity/transform transitions
- no dramatic parallax
- no floating blobs or over-animated AI energy

## 7. Do

- emphasize trust, traceability, and review
- make public boundary statements visually prominent
- use blue-gray structure as the default language
- keep information density high but organized
- let headings and labels create clear scan paths
- make proposal status and privacy mode obvious at a glance

## 8. Don’t

- do not imitate chat-first AI apps
- do not rely on giant glowing input bars as the main brand device
- do not use purple as the dominant accent
- do not overuse glass cards, blur, or giant gradients
- do not make the interface look like a student side project or template marketplace
- do not make Workbench look like a generic admin dashboard

## 9. Responsive Behavior

- On mobile, public hero becomes a stacked brief: value, trust markers, quick export
- Hero imagery becomes secondary and should never dominate the first scroll
- Workbench collapses to a strong top summary followed by stacked panels
- Preserve section labels and status chips on small screens
- Maintain generous tap targets and readable field spacing

## 10. Project-Specific Guardrails

This product is **not**:

- an official university platform
- a thesis ghostwriting system
- a remote AI playground
- a flashy AI builder landing page

The UI should always reinforce:

- non-official but serious
- local-first and privacy-aware
- proposal-before-version
- format compliance before embellishment
- human confirmation before irreversible output

## 11. Agent Prompt Guide

When generating or editing UI for this project, use this framing:

> Build a light academic workbench UI for SCNU undergraduate thesis operations. Use IBM-like structural rigor, Notion-like document warmth, and only a restrained Apple-like ambient polish. The interface must feel trustworthy, review-oriented, and local-first. Favor blue-gray hierarchy, strong borders, paper-white panels, compact status badges, readable Chinese typography, and clear process framing over flashy AI aesthetics.
