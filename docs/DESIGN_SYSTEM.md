# WiseOS Health — Design System

> Canonical source: `app/shared/theme.py` (derived from
> `Wise_PMS_Design_System.pdf`). This document mirrors the tokens and component
> factories. **Last updated:** 2026-07-20.

## Color tokens

| Token | Value | Use |
| ----- | ----- | --- |
| `PRIMARY` | `#1F3F8C` | Navigation, headers, buttons, icons |
| `PRIMARY_DARK` | `#162E68` | Button overlay/pressed |
| `ACCENT` | `#D6284D` | Highlights, alerts, danger, logo accent |
| `WHITE` | `#FFFFFF` | Backgrounds, cards |
| `LIGHT_GRAY` | `#F5F7FA` | Panels, forms, tables, page background |
| `DARK_BG` | `#0B0D12` | Reserved — dark theme (future) |
| `TEXT_DARK` | `#1A2238` | Primary text |
| `TEXT_MUTED` | `#6B7280` | Secondary/label text |
| `BORDER` | `#E3E8F2` | Input/card borders |

## Typography

- Font family: **Poppins** (fallback Inter, then system).
- Minimum readable size: **14px**. Headings default 28px bold.

## Shape & elevation

| Token | Value |
| ----- | ----- |
| `RADIUS_CARD` | 16px |
| `RADIUS_BUTTON` | 12px |
| `RADIUS_INPUT` | 10px |
| `CARD_SHADOW` | blur 20, offset (0,4), `rgba(0,0,0,0.08)` |

Minimum button height: **44px**.

## Window

`apply_theme(page)` sets title, `LIGHT_GRAY` background, Poppins theme,
`ColorScheme(primary, error)`, and a **1366×768** min/default window.

## Component factories (`theme.py`)

| Factory | Produces |
| ------- | -------- |
| `primary_button(text, on_click, icon, expand)` | Filled blue `ElevatedButton`, 44px |
| `secondary_button(...)` | Outlined blue `OutlinedButton`, 44px |
| `danger_button(...)` | Filled red `ElevatedButton`, 44px |
| `text_field(label, ..., multiline, password, hint)` | Styled `TextField` (10px radius) |
| `dropdown(label, options, value, ...)` | Styled `Dropdown` |
| `card(content, padding=24, ...)` | White rounded shadowed `Container` |
| `heading(text, size=28, color)` | Bold Poppins `Text` |
| `muted(text, size=14)` | Muted-color `Text` |
| `snack(page, message, error=False)` | SnackBar (blue info / red error) |
| `logo_block(size)` | Brand mark: blue rounded square + white cross + red pixel + wordmark |

Reusable composite widgets (stat cards, empty states, info items, data tables)
live in `app/shared/widgets.py` — see [`UI_GUIDELINES.md`](./UI_GUIDELINES.md).

## Rules

1. **Never hardcode a hex in a view.** Import from `theme`.
2. **Never build a raw button/field in a view.** Use the factories, so a token
   change propagates everywhere.
3. Dark theme (`DARK_BG`) is reserved but **not implemented**; do not ship
   partial dark styling.
4. New modules must reuse these factories so the ecosystem stays visually one
   system as it grows to 20+ modules.
