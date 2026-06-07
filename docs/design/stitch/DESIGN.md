# NexusOps AI Command Center Design System

## Design Intent

NexusOps AI should feel like a premium command center for cloud, platform, and SRE teams. The product language combines IBM Cloud density, OpenShift infrastructure clarity, Datadog observability patterns, Grafana-style dark charts, and Linear/Vercel polish.

## Atmosphere

- Dark enterprise surface with subtle blue-violet depth.
- Dense but calm dashboards.
- High-contrast data cards, clear operational hierarchy, and restrained motion.
- Status colors are vivid but contained inside badges, indicators, and chart strokes.

## Core Tokens

| Token | Value |
|---|---|
| Background | `#070A12` |
| Surface 1 | `#0D1320` |
| Surface 2 | `#121A2B` |
| Surface 3 | `#182238` |
| Border | `rgba(148, 163, 184, 0.14)` |
| Text Primary | `#F8FAFC` |
| Text Secondary | `#94A3B8` |
| Text Muted | `#64748B` |
| Brand | `#6D5DFB` |
| Cyan Accent | `#22D3EE` |
| Green | `#10B981` |
| Amber | `#F59E0B` |
| Red | `#F43F5E` |

## Typography

- Sans: Inter, system UI.
- Mono: JetBrains Mono / Fira Code for resource names, IDs, versions, and metrics.
- Page titles: 20-24px, semibold/bold.
- Card titles: 13-15px, semibold.
- Operational metadata: 10-12px, medium, uppercase only for labels.

## Layout

- 56px top bar.
- 240px expanded sidebar, 68px collapsed.
- 24px desktop page padding, 16px mobile page padding.
- 12-16px grid gaps.
- Panels use 10-12px radius with one border and no nested card stacks.

## Components

- Cards use translucent surfaces, thin borders, and optional top glow.
- Primary buttons use a blue-violet gradient and subtle shadow.
- Secondary buttons are glassy and border-led.
- Tables use compact rows, sticky mental hierarchy, hover tint, and mono resource cells.
- Drawers/panels use stronger borders and a right-side inspector pattern.
- Charts use cyan, violet, amber, rose, and emerald strokes on dark grids.

## Motion

- Page transitions: 150-220ms, small y offset, ease-out.
- Hover: border brightening, slight translate, no bounce.
- Loading: shimmer skeletons and low-contrast pulsing indicators.

## Iconography

- Lucide icons, 14-18px in navigation and cards.
- Icons sit inside 28-36px rounded tiles with low-opacity accent backgrounds.
- Avoid decorative illustrations; operational data should remain the focus.
