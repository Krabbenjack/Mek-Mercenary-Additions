# Relationship System UI - Visual Guide

This document shows how the new relationship system appears in the UI.

## 1. Character Sheet - Relationships Section (Collapsed)

```
┌─────────────────────────────────────────────────────────┐
│  ▶ Relationships                                        │
└─────────────────────────────────────────────────────────┘
```

## 2. Character Sheet - Relationships Section (Expanded, No Relationships)

```
┌─────────────────────────────────────────────────────────┐
│  ▼ Relationships                                        │
│                                                           │
│         No relationships yet.                            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 3. Character Sheet - Relationships Section (Expanded, With Relationships)

```
┌─────────────────────────────────────────────────────────────────┐
│  ▼ Relationships                                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ John Doe          [F:+45][R:+10][E:+30]  Friends            ││
│  │                                         [Details...]         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Jane Smith        [F:-35][R:0][E:-20]   Rivals              ││
│  │                                         [Details...]         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Bob Johnson       [F:+75][R:+60][E:+55] Close Friends       ││
│  │                                         [Details...]         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Legend:**
- `F` = Friendship axis
- `R` = Romance axis  
- `E` = Respect (Esteem) axis
- Green background for positive values (>20)
- Gray background for neutral values (-20 to +20)
- Red background for negative values (<-20)

## 4. Relationship Detail Dialog - Full Example

```
╔═══════════════════════════════════════════════════════════════════╗
║  Relationship: Alex "Maverick" Carter ↔ Sarah "Phoenix" Lee     ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Relationship Axes                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Friendship:    [████████████████████░░░░░░░░░░]  +75           ║
║                                                                   ║
║  Romance:       [████████████░░░░░░░░░░░░░░░░░░]  +60           ║
║                                                                   ║
║  Respect:       [████████████░░░░░░░░░░░░░░░░░░]  +55           ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Derived Information                                             ║
║  (Read-only, derived from current relationship values)          ║
║                                                                   ║
║  Relationship States:                                            ║
║    • Friendship: close_friends                                   ║
║    • Romance: attraction                                         ║
║    • Respect: esteemed                                           ║
║                                                                   ║
║  Relationship Dynamic:                                           ║
║    • Stable                                                      ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Sentiments                                                      ║
║                                                                   ║
║    • TRUSTING         Strength: 3                                ║
║    • ADMIRING         Strength: 2                                ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Relationship Roles                                              ║
║                                                                   ║
║    • MENTOR: Sarah "Phoenix" Lee                                 ║
║    • APPRENTICE: Alex "Maverick" Carter                          ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  ▶ Recent Events                                                 ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║                          [Close]                                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## 5. Relationship Detail Dialog - With Flags

```
╔═══════════════════════════════════════════════════════════════════╗
║  Relationship: Alex "Maverick" Carter ↔ John "Hawk" Williams    ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Relationship Axes                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Friendship:    [████████████░░░░░░░░░░░░░░░░░░]  +45           ║
║                                                                   ║
║  Romance:       [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  +10           ║
║                                                                   ║
║  Respect:       [███████░░░░░░░░░░░░░░░░░░░░░░░]  +30           ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Derived Information                                             ║
║  (Read-only, derived from current relationship values)          ║
║                                                                   ║
║  Relationship States:                                            ║
║    • Friendship: friends                                         ║
║    • Romance: curiosity                                          ║
║    • Respect: acknowledged                                       ║
║                                                                   ║
║  Relationship Dynamic:                                           ║
║    • Stable                                                      ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Sentiments                                                      ║
║                                                                   ║
║    • TRUSTING         Strength: 2                                ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Flags (Temporary States)                                        ║
║                                                                   ║
║    ⚑ AWKWARD          2 days remaining                           ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  ▶ Recent Events                                                 ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║                          [Close]                                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## 6. Relationship Detail Dialog - Negative Relationship

```
╔═══════════════════════════════════════════════════════════════════╗
║  Relationship: Alex "Maverick" Carter ↔ Marcus "Viper" Drake    ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Relationship Axes                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Friendship:    [░░░░░░░░░░░░░░░░░░██████████░░]  -35           ║
║                                                                   ║
║  Romance:       [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]   0            ║
║                                                                   ║
║  Respect:       [░░░░░░░░░░░░░░░░░░░████░░░░░░░]  -20           ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Derived Information                                             ║
║  (Read-only, derived from current relationship values)          ║
║                                                                   ║
║  Relationship States:                                            ║
║    • Friendship: rivals                                          ║
║    • Romance: neutral                                            ║
║    • Respect: tolerated                                          ║
║                                                                   ║
║  Relationship Dynamic:                                           ║
║    • Strained                                                    ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  Sentiments                                                      ║
║                                                                   ║
║    • HURT             Strength: 1                                ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║  ▼ Recent Events                                                 ║
║                                                                   ║
║    • Argument over tactics — 3 days ago                          ║
║                                                                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                   ║
║                          [Close]                                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Color Coding Summary

### Axis Chips (in relationship overview)
- **Dark Green** (#C8E6C9 bg, #2E7D32 fg): Value > 50
- **Light Green** (#E8F5E9 bg, #66BB6A fg): Value 20-50
- **Gray** (#F5F5F5 bg, #757575 fg): Value -20 to +20
- **Light Red** (#FFCDD2 bg, #EF5350 fg): Value -50 to -20
- **Dark Red** (#FFCDD2 bg, #C62828 fg): Value < -50

### Progress Bars (in detail dialog)
- **Positive** (Green gradient): Based on value 0-100
  - 70-100: #2E7D32 (Dark green)
  - 40-69: #66BB6A (Light green)
  - 0-39: #A5D6A7 (Pale green)
  
- **Negative** (Red gradient): Based on value 0 to -100
  - -70 to -100: #C62828 (Dark red)
  - -40 to -69: #EF5350 (Light red)
  - 0 to -39: #EF9A9A (Pale red)

### Section Backgrounds (in detail dialog)
- **Header**: #E8F5E9 (Pale green)
- **Axes**: #FFFFFF (White)
- **Derived Info**: #F5F5F5 (Light gray)
- **Sentiments**: #FFF9E6 (Pale yellow)
- **Flags**: #FFE6E6 (Pale red)
- **Roles**: #E8EAF6 (Pale blue)
- **Events**: #F0F0F0 (Gray)

## Implementation Notes

1. **No Nested Scrollbars**: Each section flows naturally, the entire dialog is scrollable
2. **Read-Only Display**: No edit buttons, no input fields, purely informational
3. **Conditional Sections**: Sections only appear if data exists
4. **Color Coordination**: Consistent color scheme across overview and details
5. **Clear Hierarchy**: Visual separation between factual data and derived states
