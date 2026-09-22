# Neo-Brutalist Technical Dashboard Design System

## 🎨 Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| **Surface (Canvas)** | `#fcf8f8` | Primary background canvas |
| **Surface Dim** | `#dcd9d9` | Disabled/low-emphasis surfaces |
| **Surface Bright** | `#fcf8f8` | Hover/active states |
| **Surface Container Lowest** | `#ffffff` | Cards, panels, modals |
| **Surface Container Low** | `#f6f3f2` | Secondary cards, sub-containers |
| **Surface Container** | `#f0edec` | Default container fills |
| **Surface Container High** | `#ebe7e7` | Highlighted areas |
| **Surface Container Highest** | `#e5e2e1` | Selected/active states |
| **On Surface** | `#1c1b1b` | Primary text color |
| **On Surface Variant** | `#444932` | Secondary text, captions |
| **Inverse Surface** | `#313030` | Highlight borders, dividers |
| **Inverse On Surface** | `#f3f0ef` | Text on inverse surfaces |
| **Outline** | `#757a60` | Form borders, disabled states |
| **Outline Variant** | `#c5c9ac` | Subtle dividers, disabled |
| **Surface Tint** | `#536600` | Accent tints, highlights |
| **Primary** | `#536600` | Primary CTA actions |
| **On Primary** | `#ffffff` | Text on primary |
| **Primary Container** | `#d4ff00` | Primary backgrounds |
| **On Primary Container** | `#5f7400` | Text on primary container |
| **Inverse Primary** | `#b0d500` | Inverted primary states |
| **Secondary** | `#00677f` | Secondary actions |
| **On Secondary** | `#ffffff` | Text on secondary |
| **Secondary Container** | `#00d2ff` | Secondary backgrounds |
| **On Secondary Container** | `#00566a` | Text on secondary container |
| **Tertiary** | `#bd0042` | Tertiary actions |
| **On Tertiary** | `#ffffff` | Text on tertiary |
| **Tertiary Container** | `#ffe9ea` | Tertiary backgrounds |
| **On Tertiary Container** | `#d6014c` | Text on tertiary container |
| **Error** | `#ba1a1a` | Error states, destructive actions |
| **On Error** | `#ffffff` | Text on error |
| **Error Container** | `#ffdad6` | Error backgrounds |
| **On Error Container** | `#93000a` | Text on error container |

## 🔤 Typography

### Type Scale

| Scale | Font Family | Size | Weight | Line Height | Letter Spacing |
|-------|-------------|------|--------|-------------|----------------|
| **Display XL** | Space Grotesk | 56px | 700 | 64px | -0.03em |
| **Display XL Mobile** | Space Grotesk | 36px | 700 | 44px | -0.02em |
| **Headline LG** | Space Grotesk | 32px | 700 | 40px | -0.02em |
| **Headline LG Mobile** | Space Grotesk | 24px | 700 | 32px | -0.01em |
| **Headline MD** | Space Grotesk | 24px | 600 | 32px | -0.01em |
| **Headline SM** | Space Grotesk | 20px | 600 | 28px | 0em |
| **Body LG** | Plus Jakarta Sans | 18px | 500 | 28px | -0.01em |
| **Body MD** | Plus Jakarta Sans | 15px | 400 | 24px | 0em |
| **Body SM** | Plus Jakarta Sans | 13px | 400 | 20px | 0.01em |
| **Label LG** | Space Mono | 14px | 700 | 20px | 0.04em |
| **Label MD** | Space Mono | 12px | 700 | 16px | 0.05em |
| **Label SM** | Space Mono | 10px | 400 | 14px | 0.06em |

### Font Families
- **Display & Headlines**: `Space Grotesk` - Geometric, editorial weight, brutalist authority
- **Body Text**: `Plus Jakarta Sans` - Balances geometric sharpness with ergonomic readability
- **Labels & Metrics**: `Space Mono` - Rigid alignment, computational legibility, technical authenticity

## 📐 Spacing & Layout

### Base Spacing Scale

| Scale | Value | Usage |
|-------|-------|-------|
| **Gutter (Desktop)** | `1.5rem` | Column gutters, panel spacing |
| **Gutter (Mobile)** | `0.75rem` | Tight spacing on narrow screens |
| **Margin (Default)** | `2rem` | Outer canvas margins |
| **Margin (Mobile)** | `1rem` | Reduced margins on mobile |
| **Space XS** | `0.25rem` | Minimal padding, tight grouping |
| **Space SM** | `0.5rem` | Small component spacing |
| **Space MD** | `1rem` | Standard component spacing |
| **Space LG** | `1.5rem` | Large section spacing |
| **Space XL** | `2.5rem` | Section dividers, major gaps |

### Grid System

- **Desktop (1024px+)**: 12-column layout, 1.5rem gutters
- **Tablet (768px - 1023px)**: 8-column layout, collapsing secondary panels
- **Mobile (<768px)**: 4-column layout, 1rem margins, 0.75rem gutters

### Responsive Breakpoints

| Breakpoint | Min Width | Max Width | Layout |
|------------|-----------|-----------|--------|
| **Mobile** | 0px | 767px | 4-column, single-column flow |
| **Tablet** | 768px | 1023px | 8-column, sliding sheets |
| **Desktop** | 1024px | ∞ | 12-column, multi-pane |

## 📏 Elevation & Depth

### Mechanical Offset Elevation System

| Elevation | Description | Shadow |
|-----------|-------------|--------|
| **Elevation 0 (Canvas)** | Flat surface with structural borders | None |
| **Elevation 1 (Cards/Panels)** | `#FFFFFF` with 2px border | `box-shadow: 4px 4px 0px #0A0A0A` |
| **Elevation 2 (Active/Modal)** | Heightened interactive state | `box-shadow: 6px 6px 0px #0A0A0A` |
| **Elevation Active/Pressed** | Mechanical toggle simulation | `transform: translate(2px, 2px)`, shadow `2px 2px 0px #0A0A0A` |

### Ghost/Inset Layers
- Border: `1px solid #0A0A0A`
- Background: `#F4F3EE`
- No drop shadow

## 📐 Shapes

- **Corner Radius**: `0px` (strictly square)
- **Forbidden**: Pills, smoothed corners, rounded rectangles
- **Geometry**: Razor-sharp rectangular geometry only
- **Reference**: Printed industrial documentation, structural blueprint matrices, mechanical computing modules

## 🧩 Components

### Buttons

#### Primary Button
- **Background**: `#D4FF00` (Electric Acid Lime)
- **Text**: `#0A0A0A` (Ink Black)
- **Border**: `2px solid #0A0A0A`
- **Shadow**: `3px 3px 0px #0A0A0A`
- **Typography**: `label-lg` uppercase
- **Hover**: Shadow expands to `5px 5px 0px #0A0A0A`
- **Active**: `translate(2px, 2px)` with `1px 1px 0px #0A0A0A`

#### Secondary Button
- **Background**: `#FFFFFF`
- **Text**: `#0A0A0A`
- **Border**: `2px solid #0A0A0A`
- **Shadow**: `3px 3px 0px #0A0A0A`

#### Destructive Button
- **Background**: `#FF3366` (Hot Punch Coral)
- **Text**: `#FFFFFF`
- **Border**: `2px solid #0A0A0A`
- **Shadow**: `3px 3px 0px #0A0A0A`

### Status Chips & Badges

- **Non-interactive**: `label-sm` font, `1.5px solid #0A0A0A` border, `2px 8px` padding
- **High-Priority States**:
  - Operational/Online: `#D4FF00` background
  - Syncing/Telemetry: `#00D2FF` background
  - Fatal/Breached: `#FF3366` background

### Form Inputs

- **Background**: `#FFFFFF`
- **Border**: `2px solid #0A0A0A`
- **Corners**: `0px` (sharp)
- **Padding**: `10px 14px`
- **Label Typography**: `label-md` uppercase, rendered above input
- **User Input**: `body-md`
- **Focus State**: No outline, inset box shadow `0 0 0 1px #0A0A0A`, background subtly shifts or outer solid shadow `3px 3px 0px #D4FF00`

### Checkboxes & Radios

- **Checkboxes**: Square `18px x 18px`, `2px solid #0A0A0A`, background `#FFFFFF`
  - **Checked**: Background `#D4FF00`, ink-black cross/block marker
- **Radios**: Square `18px x 18px` (zero roundedness), inner filled square `8px x 8px` in `#0A0A0A` when active

### Cards & Data Panels

- **Background**: `#FFFFFF`
- **Border**: `2px solid #0A0A0A`
- **Shadow**: `4px 4px 0px #0A0A0A`
- **Section Dividers**: `border-bottom: 2px solid #0A0A0A`
- **Title Accent**: Colored pill or accent bar

### Telemetry/Data Readouts

- **Metric Cards**: Large `display-xl` numbers with `label-sm` technical labels stacked above
- **Trend Indicators**: Mini solid containers for negative/positive indicators
- **Layout**: Single-column feed with full-bleed touch targets on mobile

## 🎯 Brand & Style Philosophy

### Visual Principles

1. **Unfiltered Clarity**: Zero faux-depth or ethereal blurs. Depth via mechanical line art, solid planar offsets, high-frequency stark contrast.

2. **Architectural Grid Rigor**: Every component adheres to visible frame structures. Data density as first-class citizen, balanced by intentional breathing room via warm, paper-like surfaces.

3. **High-Velocity Kinetic Feedback**: State interactions are tactile, instant, and physical. Buttons snap, cards press, focus states assert complete authority.

### Color Role Mapping

- **Canvas Base**: `#F4F3EE` (muted pale bone, eye-strain reduction for sustained monitoring)
- **Surface Elevation**: `#FFFFFF` (pure stark white for cards, panels, data tables)
- **Ink & Strokes**: `#0A0A0A` (pure pitch black for structural outlines, text, critical icons)
- **Secondary Ink**: `#18181B` (subtle internal subdivision borders)
- **Primary CTA**: `#D4FF00` (Electric Acid Lime, exclusive for high-intent actions, key metrics, active selected states)
- **Accent 1**: `#00D2FF` (Electric Sky Pop, telemetry, system pings, active network channels)
- **Accent 2**: `#FF3366` (Hot Punch Coral, critical anomalies, terminal errors, destructive triggers)

## 📦 Usage Guidelines

### When to Use This Design System

- Technical dashboards, command centers, developer tooling
- Real-time operational interfaces requiring high data density
- Applications where clarity and instant readability are critical
- Systems requiring Neo-Brutalist aesthetic with mechanical authenticity

### Avoid When

- Soft, rounded, or organic aesthetic required
- Playful or decorative interfaces needed
- Accessibility requirements conflict with strict 0px corners (provide exception paths)

### Implementation Priority

1. **Core Colors**: Establish palette variables first
2. **Typography**: Apply type scale consistently
3. **Spacing**: Apply grid and spacing system
4. **Components**: Implement button, input, chip styles
5. **Elevation**: Add mechanical shadow system
6. **Edge Cases**: Document exceptions and accessibility considerations

---
*Neo-Brutalist Technical Dashboard Design System - Version 1.0*
*Designed for high-density technical interfaces, command centers, and developer tooling*