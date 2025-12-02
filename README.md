# Homebrew Recipe Builder 🍺

A Streamlit web application for creating, managing, and calculating homebrew beer recipes.

## Features

- **Recipe Creation**: Build complete beer recipes with grain bills, hop schedules, and yeast selection
- **Automatic Calculations**: 
  - Original Gravity (OG)
  - Final Gravity (FG)
  - Alcohol By Volume (ABV)
  - International Bitterness Units (IBU)
  - Standard Reference Method (SRM) for color
- **Recipe Management**: Save and view your recipes
- **Brewing Calculators**: 
  - ABV Calculator
  - Priming Sugar Calculator
  - Strike Water Temperature Calculator
- **Recipe Library**: Browse popular homebrew recipes (coming soon)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or navigate to the project directory:
```bash
cd homebrew-recipe-app
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically `http://localhost:8501`)

3. Use the sidebar to navigate between:
   - **Create Recipe**: Build a new homebrew recipe
   - **View Recipes**: Browse and manage your saved recipes
   - **Recipe Library**: Explore popular recipes
   - **Brewing Calculator**: Use various brewing calculators

## Project Structure

```
homebrew-recipe-app/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/
│   └── recipes/           # Saved recipes (created automatically)
│       └── recipes.json
└── assets/                # Images and other assets
```

## Recipe Components

### Grain Bill
- Support for 10+ common grain types
- Automatic point per pound per gallon (PPG) calculations
- Lovibond values for color calculation

### Hop Schedule
- 10+ popular hop varieties
- Alpha acid percentages
- Boil time tracking
- IBU calculations using Tinseth formula

### Yeast Selection
- Common ale and lager strains
- Fermentation temperature recommendations

## Calculations

The app uses industry-standard formulas:

- **OG Calculation**: Based on grain bill, efficiency, and batch size
- **IBU Calculation**: Tinseth formula for hop utilization
- **SRM Calculation**: Morey equation for beer color
- **ABV Calculation**: Standard formula based on OG and FG

## Data Storage

Recipes are stored locally in JSON format at `data/recipes/recipes.json`. The file is created automatically when you save your first recipe.

## Contributing

Feel free to fork this project and add your own features! Some ideas:
- Water chemistry calculator
- Recipe scaling tool
- Brew day timer
- Integration with brewing equipment APIs
- Recipe sharing capabilities

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Brewing calculations based on standard homebrewing formulas
- Inspired by the homebrewing community

## Support

For issues or questions, please open an issue on the project repository.

Happy brewing! 🍺
