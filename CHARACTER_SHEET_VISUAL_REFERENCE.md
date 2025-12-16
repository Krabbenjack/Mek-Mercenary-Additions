# Character Sheet UI - Visual Layout Reference

## Window Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Character Sheet: [Character Name]                                      [X]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐  ┌──────────────────────────────────────────────────┐ │
│  │  LEFT PANEL      │  │  RIGHT PANEL (Scrollable)                        │ │
│  │  (Fixed 280px)   │  │                                                  │ │
│  │                  │  │  ┌────────────────────────────────────────────┐  │ │
│  │ ┌──────────────┐ │  │  │ ▼ Overview                    #F6F4EF    │  │ │
│  │ │              │ │  │  ├────────────────────────────────────────────┤  │ │
│  │ │   PORTRAIT   │ │  │  │ [Two-column layout with summary & highlights] │
│  │ │   180x240    │ │  │  │                                            │  │ │
│  │ │              │ │  │  └────────────────────────────────────────────┘  │ │
│  │ └──────────────┘ │  │                                                  │ │
│  │ [Select...]      │  │  ┌────────────────────────────────────────────┐  │ │
│  │                  │  │  │ ▶ Attributes                  #F2F7FF     │  │ │
│  │ Name: ...        │  │  └────────────────────────────────────────────┘  │ │
│  │ Callsign: ...    │  │                                                  │ │
│  │ Rank: ...        │  │  ┌────────────────────────────────────────────┐  │ │
│  │ Unit: ...        │  │  │ ▶ Skills                      #F2FFF6     │  │ │
│  │ Force: ...       │  │  └────────────────────────────────────────────┘  │ │
│  │ Primary: ...     │  │                                                  │ │
│  │ Secondary: ...   │  │  ┌────────────────────────────────────────────┐  │ │
│  │                  │  │  │ ▶ Personality                 #F6F2FF     │  │ │
│  │ Quick Info       │  │  └────────────────────────────────────────────┘  │ │
│  │ [Gunnery: 3]     │  │                                                  │ │
│  │ [Piloting: 4]    │  │  ┌────────────────────────────────────────────┐  │ │
│  │ [5 Traits]       │  │  │ ▶ Relationships               #FFF4F2     │  │ │
│  │ [3 Quirks]       │  │  └────────────────────────────────────────────┘  │ │
│  │ [2 SPAs]         │  │                                                  │ │
│  │                  │  │  ┌────────────────────────────────────────────┐  │ │
│  └──────────────────┘  │  │ ▶ Equipment                   #F7F7F7     │  │ │
│                         │  └────────────────────────────────────────────┘  │ │
│                         │                                                  │ │
│                         └──────────────────────────────────────────────────┘ │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
   1000px wide x 700px tall
```

## Section Details

### Overview Section (Expanded)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Overview                                            #F6F4EF      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌───────────────────────┐  ┌──────────────────────────────────┐  │
│  │ Summary               │  │ Highlights                       │  │
│  │                       │  │                                  │  │
│  │ Rank: Lieutenant      │  │ Top Skills:                      │  │
│  │ Age: 32 (adult)       │  │ • Tech/Mek: 5                    │  │
│  │ Birthday: 2990-05-15  │  │ • Piloting/Mek: 4                │  │
│  │ Primary: MEKWARRIOR   │  │ • Gunnery/Mek: 3                 │  │
│  │ Secondary: TECH       │  │ • Tactics: 2                     │  │
│  │ Unit: Alpha Lance     │  │ • Leadership: 2                  │  │
│  │ Formation: Lance      │  │                                  │  │
│  │ Crew Role: pilot      │  │ Special Abilities (2):           │  │
│  │                       │  │ • Natural Aptitude/Gunnery       │  │
│  └───────────────────────┘  │ • Combat Reflexes                │  │
│                             │                                  │  │
│                             │ Quirks (3):                      │  │
│                             │ • Tech Savvy                     │  │
│                             │ • Brave                          │  │
│                             │ • Stubborn                       │  │
│                             └──────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Attributes Section (Expanded)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Attributes                                          #F2F7FF      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  BOD:     7                                                        │
│  CHA:     5                                                        │
│  DEX:     8                                                        │
│  EDG:     4                                                        │
│  INT:     9                                                        │
│  RFL:     7                                                        │
│  STR:     7                                                        │
│  WIL:     6                                                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Skills Section (Expanded)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Skills                                              #F2FFF6      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Search: [_________________]                                       │
│                                                                    │
│  Gunnery/Mek — 3                                                   │
│    supported by: DEX, RFL                                          │
│                                                                    │
│  Leadership — 2                                                    │
│    supported by: CHA, WIL                                          │
│                                                                    │
│  Piloting/Mek — 4                                                  │
│    supported by: DEX, RFL                                          │
│                                                                    │
│  Tactics — 2                                                       │
│    supported by: INT, WIL                                          │
│                                                                    │
│  Tech/Mek — 5                                                      │
│    supported by: INT, EDG                                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Personality Section (Expanded with Sub-tabs)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Personality                                         #F6F2FF      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────┬────────────┬──────────────────────┐               │
│  │ Traits     │ Quirks     │ Special Abilities   │               │
│  └────────────┴────────────┴──────────────────────┘               │
│                                                                    │
│  [Traits Tab Content]                                             │
│                                                                    │
│  Aggression:   AGGRESSIVE                                          │
│  Ambition:     AMBITIOUS                                           │
│  Greed:        NONE                                                │
│  Social:       SOCIABLE                                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

[Quirks Tab]
┌────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Tech Savvy  │  │    Brave     │  │   Stubborn   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

[Special Abilities Tab]
┌────────────────────────────────────────────────────────────────────┐
│  Natural Aptitude/Gunnery                                          │
│    Bonus to gunnery rolls                                          │
│                                                                    │
│  Combat Reflexes                                                   │
│    Bonus to initiative                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Relationships Section (Expanded)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Relationships                                       #FFF4F2      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ◉ All    ○ Allies    ○ Rivals    ○ Family                        │
│                                                                    │
│  ID: char-002...     Ally        +45                               │
│  ID: char-003...     Ally        +32                               │
│  ID: char-004...     Neutral      0                                │
│  ID: char-005...     Rival       -15                               │
│  ID: char-006...     Rival       -28                               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Equipment Section (Disabled Placeholder)

```
┌────────────────────────────────────────────────────────────────────┐
│ ▼ Equipment                                           #F7F7F7      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Equipment will be implemented later.                              │
│                                                                    │
│  ┌──────────────┬─────┬──────────────────────────────────┐        │
│  │ Item         │ Qty │ Notes                            │        │
│  ├──────────────┼─────┼──────────────────────────────────┤        │
│  │ —            │ —   │ —                                │        │
│  └──────────────┴─────┴──────────────────────────────────┘        │
│                                                                    │
│  [ Add ] [ Remove ] [ Import ]  (all disabled)                     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Color Reference

| Section       | Hex Color | Description      |
|---------------|-----------|------------------|
| Overview      | #F6F4EF   | Warm sand        |
| Attributes    | #F2F7FF   | Pale blue        |
| Skills        | #F2FFF6   | Pale mint        |
| Personality   | #F6F2FF   | Pale lavender    |
| Relationships | #FFF4F2   | Pale peach       |
| Equipment     | #F7F7F7   | Neutral gray     |
| Text          | #1E1E1E   | Dark (readable)  |
| Background    | #FFFFFF   | White            |

## Chip Styles

Quick Info Chips (Left Panel):
```
┌─────────────┐
│ Gunnery: 3  │  Background: #D4E6F1 (light blue)
└─────────────┘

┌──────────────┐
│ Piloting: 4  │  Background: #D5F4E6 (light green)
└──────────────┘

┌──────────┐
│ 5 Traits │  Background: #E8DAEF (light purple)
└──────────┘

┌───────────┐
│ 3 Quirks  │  Background: #FADBD8 (light red)
└───────────┘

┌──────────┐
│ 2 SPAs   │  Background: #FCF3CF (light yellow)
└──────────┘
```

Quirk Chips (Personality Tab):
```
┌──────────────┐
│  Tech Savvy  │  Background: #FADBD8, Relief: RAISED
└──────────────┘
```

## Accordion Indicators

Closed: ▶ (right-pointing triangle)
Open:   ▼ (down-pointing triangle)

## Typography

- Section Headers: TkDefaultFont, 11pt, bold
- Body Text: TkDefaultFont, 9pt, regular
- Labels: TkDefaultFont, 9pt, bold
- Italic Hints: TkDefaultFont, 8pt, italic
- Chip Text: TkDefaultFont, 8pt, regular

## Interaction Behaviors

1. **Accordion Sections**:
   - Click anywhere on header to toggle
   - Only one section open at a time (single-open mode)
   - Overview open by default

2. **Skills Search**:
   - Type to filter skills in real-time
   - Case-insensitive matching
   - Shows/hides skill entries dynamically

3. **Relationship Filters**:
   - Radio buttons change displayed relationships
   - All: Shows all relationships
   - Allies: Shows only positive values
   - Rivals: Shows only negative values
   - Family: Placeholder (requires relationship type metadata)

4. **Portrait Selection**:
   - Click "Select Portrait..." button
   - Opens file dialog
   - Supports PNG, JPG, JPEG, GIF, BMP
   - Scales to 180x240 maintaining aspect ratio

## Data Handling

- **Missing Data**: Display "—" or "None"
- **Empty Collections**: Show explanatory text ("No [type] available.")
- **Unknown Skills**: Show without attribute hint
- **Null Values**: Gracefully handled, no crashes
- **Unknown Professions**: Display verbatim (no whitelist)
