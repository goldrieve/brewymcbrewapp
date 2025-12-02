# Homebrew Recipe App - Data Directory

This directory stores application data.

## Structure

- `recipes/` - Saved user recipes (JSON format)
- `examples/` - Example recipes for reference
- `exports/` - Exported recipes (future feature)

## recipes.json Format

Recipes are stored in the following JSON structure:

```json
[
  {
    "name": "My IPA",
    "style": "American IPA",
    "brewer": "John Doe",
    "batch_size": 5.0,
    "efficiency": 75,
    "brew_date": "2025-12-02",
    "grain_bill": [
      {
        "type": "2-Row Pale Malt",
        "weight": 10.0,
        "ppg": 37,
        "lovibond": 2
      }
    ],
    "hop_schedule": [
      {
        "variety": "Cascade",
        "weight": 1.0,
        "time": 60,
        "alpha_acid": 5.5
      }
    ],
    "yeast": "US-05 (American Ale)",
    "fermentation_temp": 68,
    "og": 1.055,
    "fg": 1.012,
    "abv": 5.6,
    "ibu": 45,
    "srm": 6,
    "notes": "First batch of 2025",
    "created_at": "2025-12-02T10:30:00"
  }
]
```

## Notes

- The `recipes/` directory and `recipes.json` file are created automatically when you save your first recipe
- Backup your `recipes.json` file regularly if you want to preserve your recipes
