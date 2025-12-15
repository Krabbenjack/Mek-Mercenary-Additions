# Menu Structure

## Main Menu Bar

```
┌─────────────────────────────────────────────────────────────┐
│ File                                                        │
└─────────────────────────────────────────────────────────────┘
  │
  ├─ Import ▶
  │           ├─ Import Personnel (JSON)...
  │           ├─ Import TO&E (JSON)...
  │           ├─ ───────────────────────
  │           └─ Set External Portrait Folder...
  │
  ├─ ───────────────────────
  │
  └─ Exit
```

## Old vs New UI Layout

### Before (Old Layout)
```
┌──────────────────────────────────────────────────────────────┐
│ [Date Label] [Nächster Tag] [Importiere Personal (JSON)]    │
│              [Importiere TO&E (JSON)]                        │
└──────────────────────────────────────────────────────────────┘
```

### After (New Layout)
```
┌──────────────────────────────────────────────────────────────┐
│ File                                              (Menu Bar)  │
├──────────────────────────────────────────────────────────────┤
│ [Date Label] [Nächster Tag]                                  │
└──────────────────────────────────────────────────────────────┘
```

**Benefits**:
- Cleaner toolbar (less cluttered)
- More professional Windows-style interface
- Easy to add more menu items in future
- Standard File menu pattern

## Portrait Search Flow

```
User selects character
         │
         ▼
    ┌────────────────┐
    │ Main Panel     │──────► resolve_portrait_path(prefer_casual=False)
    │ (Charakter)    │                  │
    └────────────────┘                  │
                                        ▼
                            Search in priority order:
                            1. Module: images/portraits/
                            2. External: (if configured)
                                        │
                                        ▼
                            Find: MW_F_4.png (default)
                                        │
                                        ▼
                            Display in main panel

User right-clicks character
         │
         ▼
    ┌────────────────┐
    │ Detail Dialog  │──────► resolve_portrait_path(prefer_casual=True)
    │ (Popup)        │                  │
    └────────────────┘                  │
                                        ▼
                            Search in priority order:
                            1. Module: images/portraits/
                            2. External: (if configured)
                                        │
                                        ▼
                            Try: MW_F_4_cas.png first
                            Fallback: MW_F_4.png
                                        │
                                        ▼
                            Display casual variant (or default)
```

## Portrait Variant Resolution Algorithm

```
resolve_portrait_path(character, prefer_casual):
    if prefer_casual:
        for search_root in [module_root, external_root]:
            if find_variant(search_root, filename, "_cas"):
                return casual_portrait_path
    
    # Fallback or default mode
    for search_root in [module_root, external_root]:
        if find_variant(search_root, filename, ""):
            return default_portrait_path
    
    return None  # Not found
```

## File Extension Priority

When searching for a portrait variant:

1. Try original extension (e.g., `.png` if original was `.png`)
2. Try other supported extensions in order:
   - `.png`
   - `.jpg`
   - `.jpeg`
   - `.gif`
   - `.bmp`

This allows flexibility if portraits have different extensions.

## Category Subdirectory Support

Portraits can be organized by category:

```
images/portraits/
├── Male/
│   ├── MW_F_4.png
│   └── MW_F_4_cas.png
├── Female/
│   ├── MW_F_5.png
│   └── MW_F_5_cas.png
└── Other/
    └── MW_F_6.png
```

The category is read from the character's portrait metadata (imported from MekHQ).
