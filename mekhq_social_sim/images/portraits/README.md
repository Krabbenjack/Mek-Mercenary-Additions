# Character Portraits

This directory contains character portraits for the MekHQ Social Simulator.

## Portrait Naming Convention

- **Default portraits**: `<name>.png` (e.g., `MW_F_4.png`)
- **Casual variant**: `<name>_cas.png` (e.g., `MW_F_4_cas.png`)

## Supported Formats

The following image formats are supported:
- `.png`
- `.jpg` / `.jpeg`
- `.gif`
- `.bmp`

## Portrait Search Paths

The GUI searches for portraits in multiple locations (in priority order):

1. **Module folder**: `mekhq_social_sim/images/portraits`
2. **External folder**: User-configured folder (set via File > Import > Set External Portrait Folder...)

## Portrait Categories

Portraits can be organized in subdirectories by category (e.g., `Male/`, `Female/`, etc.). The category is stored in the MekHQ campaign data.

## Usage

- The **main character panel** displays the default portrait
- The **character detail dialog** (opened via right-click) prefers the casual variant (`_cas`) if available, otherwise shows the default portrait
