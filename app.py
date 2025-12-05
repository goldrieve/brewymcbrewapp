#!/usr/bin/env python

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(
    page_title="Joe's Homebrew Recipe Builder",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for recipes
if 'recipes' not in st.session_state:
    st.session_state.recipes = []

if 'current_recipe' not in st.session_state:
    st.session_state.current_recipe = None

if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Initialize entry gate state
if 'entered_app' not in st.session_state:
    st.session_state.entered_app = False


def calculate_og(grain_bill, batch_size):
    """Calculate Original Gravity based on grain bill and batch size"""
    total_points = 0
    for grain in grain_bill:
        # Points per kg per liter (typical extract efficiency ~70%)
        # Convert from metric: ppg * 8.3454 for kg/L basis
        points = grain['weight'] * grain['ppg'] * 8.3454 * 0.70
        total_points += points
    
    og = 1 + (total_points / batch_size) / 1000
    return round(og, 3)


def calculate_ibu(hop_additions, og, batch_size):
    """Calculate IBU (International Bitterness Units)"""
    total_ibu = 0
    for hop in hop_additions:
        # Tinseth formula approximation
        utilization = 1.65 * (0.000125 ** (og - 1.0))
        utilization *= (1 - np.exp(-0.04 * hop['time'])) / 4.15
        
        ibu = (hop['alpha_acid'] * hop['weight'] * utilization * 7490) / batch_size
        total_ibu += ibu
    
    return round(total_ibu, 1)


def calculate_srm(grain_bill, batch_size):
    """Calculate SRM (beer color)"""
    mcu = sum(grain['weight'] * grain['lovibond'] for grain in grain_bill) / batch_size
    srm = 1.4922 * (mcu ** 0.6859)
    return round(srm, 1)


def calculate_abv(og, fg):
    """Calculate ABV (Alcohol By Volume)"""
    abv = (og - fg) * 131.25
    return round(abv, 2)


def import_recipe_to_builder(recipe):
    """Import a recipe into the Recipe Builder for scaling"""
    # Clear existing data
    st.session_state.import_grain_bill = []
    st.session_state.import_hop_schedule = []
    st.session_state.import_other_ingredients = []
    
    # Import grain bill
    if recipe.get('grain_bill'):
        for grain in recipe['grain_bill']:
            st.session_state.import_grain_bill.append({
                'name': grain.get('type', grain.get('name', 'Unknown Grain')),
                'original_amount': grain.get('weight', 0),
                'scaled_amount': grain.get('weight', 0)
            })
    
    # Import hop schedule
    if recipe.get('hop_schedule'):
        for hop in recipe['hop_schedule']:
            st.session_state.import_hop_schedule.append({
                'variety': hop.get('variety', 'Unknown Hop'),
                'original_amount': hop.get('weight', 0),
                'scaled_amount': hop.get('weight', 0),
                'time': hop.get('time', 0)
            })
    
    # Import other ingredients if present
    if recipe.get('other_ingredients'):
        for ingredient in recipe['other_ingredients']:
            st.session_state.import_other_ingredients.append({
                'name': ingredient.get('name', 'Unknown'),
                'original_amount': ingredient.get('amount', 0),
                'unit': ingredient.get('unit', 'g'),
                'should_scale': True
            })
    
    # Store recipe metadata for pre-filling form fields
    # Handle both standard and Guy's recipe formats
    stats = recipe.get('statistics', {})
    batch_size = recipe.get('batch_size') or stats.get('volume', 19.0)
    og = recipe.get('og') or stats.get('og', 0)
    fg = recipe.get('fg') or stats.get('fg', 0)
    
    # Handle yeast format (can be string or dict)
    yeast_data = recipe.get('yeast', '')
    if isinstance(yeast_data, dict):
        yeast_str = yeast_data.get('name', '')
    else:
        yeast_str = yeast_data if yeast_data else ''
    
    st.session_state.imported_recipe_data = {
        'name': recipe.get('name') or recipe.get('beer', ''),
        'style': recipe.get('style', ''),
        'batch_size': batch_size,
        'brewer': recipe.get('brewer', ''),
        'og': og,
        'fg': fg,
        'mash_temp': recipe.get('mash_temp'),
        'mash_time': recipe.get('mash_time'),
        'boil_temp': recipe.get('boil_temp'),
        'boil_time': recipe.get('boil_time'),
        'yeast': yeast_str,
        'fermentation_temp': recipe.get('fermentation_temp'),
        'fermentation_days': recipe.get('fermentation_days'),
        'notes': recipe.get('notes', '')
    }


def export_recipe_to_csv(recipe):
    """Convert a recipe to CSV format"""
    import io
    csv_data = []
    
    # Add header info
    csv_data.append(["Recipe Name", recipe['name']])
    csv_data.append(["Style", recipe.get('style', 'N/A')])
    csv_data.append(["Batch Size (L)", recipe.get('batch_size', 'N/A')])
    csv_data.append(["Brewer", recipe.get('brewer', 'N/A')])
    csv_data.append(["Brew Date", recipe.get('brew_date', 'N/A')])
    csv_data.append([])  # Empty row
    
    # Add statistics
    csv_data.append(["RECIPE STATISTICS"])
    csv_data.append(["Original Gravity", recipe.get('og', 'N/A')])
    csv_data.append(["Final Gravity", recipe.get('fg', 'N/A')])
    csv_data.append(["ABV (%)", recipe.get('abv', 'N/A')])
    csv_data.append([])  # Empty row
    
    # Add grain bill
    if recipe.get('grain_bill'):
        csv_data.append(["GRAIN BILL"])
        csv_data.append(["Grain Type", "Weight (kg)", "Lovibond"])
        for grain in recipe['grain_bill']:
            csv_data.append([grain.get('type', grain.get('name', 'N/A')), 
                           grain.get('weight', grain.get('scaled_amount', 'N/A')), 
                           grain.get('lovibond', '')])
        csv_data.append([])  # Empty row
    
    # Add hop schedule
    if recipe.get('hop_schedule'):
        csv_data.append(["HOP SCHEDULE"])
        csv_data.append(["Variety", "Weight (g)", "Time (min)", "Alpha Acid (%)"])
        for hop in recipe['hop_schedule']:
            csv_data.append([hop.get('variety', 'N/A'), 
                           hop.get('weight', hop.get('scaled_amount', 'N/A')), 
                           hop.get('time', 'N/A'),
                           hop.get('alpha_acid', '')])
        csv_data.append([])  # Empty row
    
    # Add other ingredients if present
    if recipe.get('other_ingredients'):
        csv_data.append(["OTHER INGREDIENTS"])
        csv_data.append(["Ingredient", "Amount", "Unit"])
        for ingredient in recipe['other_ingredients']:
            csv_data.append([ingredient['name'], ingredient['amount'], ingredient['unit']])
        csv_data.append([])  # Empty row
    
    # Add yeast and fermentation
    csv_data.append(["YEAST & FERMENTATION"])
    csv_data.append(["Yeast", recipe.get('yeast', 'N/A')])
    csv_data.append(["Fermentation Temperature", recipe.get('fermentation_temp', recipe.get('fermentation_info', 'N/A'))])
    if recipe.get('mash_temp'):
        csv_data.append(["Mash Temperature", recipe.get('mash_temp', 'N/A')])
    csv_data.append([])  # Empty row
    
    # Add water volumes
    if recipe.get('mash_volume') or recipe.get('sparge_volume') or recipe.get('pre_boil_volume') or recipe.get('final_volume'):
        csv_data.append(["WATER VOLUMES"])
        csv_data.append(["Mash Volume (L)", recipe.get('mash_volume', 'N/A')])
        csv_data.append(["Sparge Volume (L)", recipe.get('sparge_volume', 'N/A')])
        if recipe.get('pre_boil_volume'):
            csv_data.append(["Pre-boil Volume (L)", recipe.get('pre_boil_volume', 'N/A')])
        csv_data.append(["Final Expected Volume (L)", recipe.get('final_volume', 'N/A')])
        if recipe.get('mash_volume') and recipe.get('sparge_volume') and recipe.get('final_volume'):
            total = recipe['mash_volume'] + recipe['sparge_volume']
            csv_data.append(["Total Water (L)", total])
            csv_data.append(["Expected Loss (L)", total - recipe['final_volume']])
        csv_data.append([])  # Empty row
    
    # Add notes
    if recipe.get('notes'):
        csv_data.append(["NOTES"])
        csv_data.append([recipe['notes']])
    
    # Convert to CSV string
    csv_buffer = io.StringIO()
    for row in csv_data:
        csv_buffer.write(','.join(str(cell) for cell in row) + '\n')
    return csv_buffer.getvalue()


def entry_gate():
    """Entry gate page with a question to verify user"""
    st.markdown("<div style='text-align: center; padding: 3rem 0;'>", unsafe_allow_html=True)
    st.title("🍺 Welcome to Joe's Homebrew Recipe Builder")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center; padding: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("### To enter, please answer this question:")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Center the question
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### Where be that blackbird to?")
        
        with st.form(key="entry_form", clear_on_submit=False):
            answer = st.text_input("Your answer:", key="entry_answer", placeholder="Type your answer here...")
            
            st.markdown("")  # Spacer
            
            submit_button = st.form_submit_button("Enter", type="primary", use_container_width=True)
            
            if submit_button:
                # Accept various correct answers
                correct_answers = ["wurzel tree"]
                if answer.lower().strip() in correct_answers:
                    st.session_state.entered_app = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect answer.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    # Check if user has entered the app
    if not st.session_state.entered_app:
        entry_gate()
        return
    
    st.title("🍺 Joe's Homebrew Recipe Builder")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        
        # Initialize page_selector if not present
        if 'page_selector' not in st.session_state:
            st.session_state.page_selector = "Home"
        
        # Track previous page to detect navigation changes
        if 'previous_page' not in st.session_state:
            st.session_state.previous_page = "Home"
        
        # Check if we need to navigate to a specific page programmatically
        if st.session_state.navigate_to_page:
            st.session_state.page_selector = st.session_state.navigate_to_page
            st.session_state.navigate_to_page = None
        
        page = st.radio(
            "Select Page",
            ["Home", "Recipe Builder", "View Recipes", "Brewing Calculator"],
            key="page_selector"
        )
        
        st.markdown("---")
    
    # Scroll to top when page changes
    if page != st.session_state.previous_page:
        st.session_state.previous_page = page
        # Use JavaScript to scroll to top
        st.components.v1.html(
            """
            <script>
                window.parent.document.querySelector('section.main').scrollTo(0, 0);
            </script>
            """,
            height=0
        )
    
    if page == "Home":
        home_page()
    elif page == "Recipe Builder":
        recipe_scaler_page()
    elif page == "View Recipes":
        view_recipes_page()
    elif page == "Brewing Calculator":
        calculator_page()


def home_page():
    """Landing page with app description and page overview"""
    
    # Hero Section
    st.markdown("<div style='text-align: center; padding: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    
    # Recipe Builder
    st.markdown("### 📏 Recipe Builder")
    st.markdown("""
    Build and scale beer recipes to your desired batch size.
    Load a recipe from 'View Recipes', enter ingredients from existing recipes and the app will scale the amounts to your needs, or create new recipes from scratch.
    """)
    
    # View Recipes
    st.markdown("### 📚 View Recipes")
    st.markdown("""
    Browse and manage all your saved recipes, a collection of the top 10 rated recipes for each beer style on brewer's friend or recipes from the OG recipe excel. You can load any of the recipes back into the recipe builder to scale it to your needs. Export any recipe as a CSV file 
    """)
    
    # Brewing Calculator
    st.markdown("### 🧮 Brewing Calculator")
    st.markdown("""
    Essential brewing calculators for recipe planning and brew day calculations:
    - **ABV Calculator** - Estimate alcohol content from gravity readings
    - **Priming Sugar Calculator** - Calculate priming sugar accounting for dissolved CO2
    - **Gravity Temperature Correction** - Adjust hydrometer readings for temperature
    """)
    
    # Call to Action
    st.markdown("<div style='text-align: center; padding: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("### Select a page from the sidebar to get started! 🍻")
    st.markdown("</div>", unsafe_allow_html=True)


def create_recipe_page():
    st.header("Create New Recipe")
    
    # Recipe basics
    col1, col2 = st.columns(2)
    
    with col1:
        recipe_name = st.text_input("Recipe Name", placeholder="My Awesome IPA")
        style = st.selectbox(
            "Beer Style",
            ["American IPA", "Pale Ale", "Stout", "Porter", "Wheat Beer", 
             "Lager", "Belgian Ale", "Brown Ale", "Amber Ale", "Other"]
        )
        batch_size = st.number_input("Batch Size (liters)", min_value=4.0, max_value=190.0, value=19.0, step=1.0)
    
    with col2:
        brewer = st.text_input("Brewer Name", placeholder="Your Name")
        brew_date = st.date_input("Planned Brew Date", datetime.now())
        efficiency = st.slider("Expected Efficiency (%)", min_value=60, max_value=90, value=75)
    
    st.markdown("---")
    
    # Grain Bill Section
    st.subheader("🌾 Grain Bill")
    
    grain_types = {
        "2-Row Pale Malt": {"ppg": 37, "lovibond": 2},
        "Pilsner Malt": {"ppg": 37, "lovibond": 1.5},
        "Munich Malt": {"ppg": 35, "lovibond": 9},
        "Vienna Malt": {"ppg": 36, "lovibond": 4},
        "Crystal 40L": {"ppg": 34, "lovibond": 40},
        "Crystal 60L": {"ppg": 34, "lovibond": 60},
        "Chocolate Malt": {"ppg": 34, "lovibond": 350},
        "Roasted Barley": {"ppg": 28, "lovibond": 500},
        "Wheat Malt": {"ppg": 38, "lovibond": 2},
        "Flaked Oats": {"ppg": 33, "lovibond": 1}
    }
    
    if 'grain_bill' not in st.session_state:
        st.session_state.grain_bill = []
    
    with st.expander("Add Grain", expanded=True):
        gcol1, gcol2, gcol3 = st.columns(3)
        
        with gcol1:
            grain_type = st.selectbox("Grain Type", list(grain_types.keys()), key="grain_select")
        
        with gcol2:
            grain_weight = st.number_input("Weight (kg)", min_value=0.0, max_value=22.0, value=0.5, step=0.1, key="grain_weight")
        
        with gcol3:
            st.write("")
            st.write("")
            if st.button("Add Grain"):
                grain_info = grain_types[grain_type]
                st.session_state.grain_bill.append({
                    'type': grain_type,
                    'weight': grain_weight,
                    'ppg': grain_info['ppg'],
                    'lovibond': grain_info['lovibond']
                })
                st.rerun()
    
    if st.session_state.grain_bill:
        grain_df = pd.DataFrame(st.session_state.grain_bill)
        st.dataframe(grain_df[['type', 'weight', 'lovibond']], use_container_width=True)
        
        if st.button("Clear Grain Bill"):
            st.session_state.grain_bill = []
            st.rerun()
    
    st.markdown("---")
    
    # Hop Schedule Section
    st.subheader("🌿 Hop Schedule")
    
    hop_varieties = {
        "Cascade": 5.5,
        "Centennial": 10.0,
        "Chinook": 13.0,
        "Citra": 12.0,
        "Mosaic": 12.5,
        "Amarillo": 9.0,
        "Simcoe": 13.0,
        "Columbus": 15.0,
        "Hallertau": 4.0,
        "Saaz": 3.5
    }
    
    if 'hop_schedule' not in st.session_state:
        st.session_state.hop_schedule = []
    
    with st.expander("Add Hop Addition", expanded=True):
        hcol1, hcol2, hcol3, hcol4 = st.columns(4)
        
        with hcol1:
            hop_variety = st.selectbox("Hop Variety", list(hop_varieties.keys()), key="hop_select")
        
        with hcol2:
            hop_weight = st.number_input("Weight (g)", min_value=0.0, max_value=280.0, value=28.0, step=5.0, key="hop_weight")
        
        with hcol3:
            hop_time = st.number_input("Boil Time (min)", min_value=0, max_value=90, value=60, step=5, key="hop_time")
        
        with hcol4:
            st.write("")
            st.write("")
            if st.button("Add Hop"):
                st.session_state.hop_schedule.append({
                    'variety': hop_variety,
                    'weight': hop_weight,
                    'time': hop_time,
                    'alpha_acid': hop_varieties[hop_variety]
                })
                st.rerun()
    
    if st.session_state.hop_schedule:
        hop_df = pd.DataFrame(st.session_state.hop_schedule)
        st.dataframe(hop_df[['variety', 'weight', 'time', 'alpha_acid']], use_container_width=True)
        
        if st.button("Clear Hop Schedule"):
            st.session_state.hop_schedule = []
            st.rerun()
    
    st.markdown("---")
    
    # Yeast Section
    st.subheader("🧫 Yeast")
    
    yeast_strains = [
        "US-05 (American Ale)",
        "S-04 (English Ale)",
        "WLP001 (California Ale)",
        "WLP002 (English Ale)",
        "WLP007 (Dry English Ale)",
        "Safale S-33 (General Purpose)",
        "Wyeast 1056 (American Ale)",
        "Wyeast 1968 (London ESB)"
    ]
    
    ycol1, ycol2 = st.columns(2)
    
    with ycol1:
        yeast = st.selectbox("Yeast Strain", yeast_strains)
    
    with ycol2:
        fermentation_temp = st.slider("Fermentation Temperature (°C)", min_value=15, max_value=24, value=20)
    
    st.markdown("---")
    
    # Water Volumes Section
    st.subheader("💧 Water Volumes")
    
    wcol1, wcol2, wcol3 = st.columns(3)
    
    with wcol1:
        mash_volume = st.number_input("Mash Volume (liters)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
    
    with wcol2:
        sparge_volume = st.number_input("Sparge Volume (liters)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
    
    with wcol3:
        final_volume = st.number_input("Final Expected Volume (liters)", min_value=0.0, max_value=100.0, value=batch_size, step=0.5)
    
    total_water = mash_volume + sparge_volume
    st.info(f"💧 Total Water: **{total_water:.1f} liters** | Expected Loss: **{total_water - final_volume:.1f} liters**")
    
    st.markdown("---")
    
    # Recipe Calculations
    if st.session_state.grain_bill:
        st.subheader("📊 Recipe Statistics")
        
        og = calculate_og(st.session_state.grain_bill, batch_size)
        srm = calculate_srm(st.session_state.grain_bill, batch_size)
        
        fg = st.number_input("Expected Final Gravity", min_value=1.000, max_value=1.030, value=1.010, step=0.001)
        abv = calculate_abv(og, fg)
        
        if st.session_state.hop_schedule:
            ibu = calculate_ibu(st.session_state.hop_schedule, og, batch_size)
        else:
            ibu = 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Original Gravity", f"{og:.3f}")
        
        with col2:
            st.metric("Final Gravity", f"{fg:.3f}")
        
        with col3:
            st.metric("ABV", f"{abv}%")
        
        with col4:
            st.metric("IBU", f"{ibu}")
        
        with col5:
            st.metric("SRM (Color)", f"{srm}")
    
    st.markdown("---")
    
    # Notes Section
    st.subheader("📝 Brewing Notes")
    notes = st.text_area("Additional Notes", placeholder="Add any special instructions or notes about this recipe...")
    
    # Save Recipe
    st.markdown("---")
    
    if st.button("💾 Save Recipe", type="primary"):
        if not recipe_name:
            st.error("Please enter a recipe name")
        elif not st.session_state.grain_bill:
            st.error("Please add at least one grain to the grain bill")
        else:
            recipe = {
                'name': recipe_name,
                'style': style,
                'brewer': brewer,
                'batch_size': batch_size,
                'efficiency': efficiency,
                'brew_date': brew_date.strftime('%d/%m/%Y'),
                'grain_bill': st.session_state.grain_bill,
                'hop_schedule': st.session_state.hop_schedule,
                'yeast': yeast,
                'fermentation_temp': fermentation_temp,
                'mash_volume': mash_volume,
                'sparge_volume': sparge_volume,
                'final_volume': final_volume,
                'og': og if st.session_state.grain_bill else 0,
                'fg': fg,
                'abv': abv if st.session_state.grain_bill else 0,
                'ibu': ibu if st.session_state.hop_schedule else 0,
                'srm': srm if st.session_state.grain_bill else 0,
                'notes': notes,
                'created_at': datetime.now().isoformat()
            }
            
            st.session_state.recipes.append(recipe)
            
            # Save to file
            os.makedirs('data/recipes', exist_ok=True)
            with open('data/recipes/recipes.json', 'w') as f:
                json.dump(st.session_state.recipes, f, indent=2)
            
            st.success(f"✅ Recipe '{recipe_name}' saved successfully!")
            
            # Clear form
            st.session_state.grain_bill = []
            st.session_state.hop_schedule = []


def view_recipes_page():
    st.header("📚 Recipes")
    
    # Toggle between user recipes and precompiled recipes
    recipe_view = st.radio(
        "Select Recipe Collection",
        ["My Recipes", "Forum Recipes", "Guy's Recipes"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if recipe_view == "My Recipes":
        # Load user recipes from file if exists
        if os.path.exists('data/recipes/recipes.json') and not st.session_state.recipes:
            with open('data/recipes/recipes.json', 'r') as f:
                st.session_state.recipes = json.load(f)
        
        if not st.session_state.recipes:
            st.info("No recipes saved yet. Create your first recipe in the Recipe Builder!")
            return
        
        recipes_to_display = st.session_state.recipes
        is_user_recipes = True
    elif recipe_view == "Forum Recipes":
        # Load precompiled recipes
        if os.path.exists('data/recipes/precompiled_recipes.json'):
            with open('data/recipes/precompiled_recipes.json', 'r') as f:
                all_forum_recipes = json.load(f)
        else:
            st.error("Precompiled recipes file not found!")
            return
        is_user_recipes = False
        
        # Search and filter interface for Forum Recipes
        st.subheader("🔍 Search Forum Recipes")
        
        # Extract unique styles
        unique_styles = sorted(list(set(r.get('style', 'Unknown') for r in all_forum_recipes)))
        
        # Search options
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            search_by = st.radio("Search by:", ["Style", "Recipe Name"], horizontal=True, key="forum_search_type")
        
        with search_col2:
            if search_by == "Style":
                selected_style = st.selectbox("Select Beer Style", [""] + unique_styles, key="forum_style_select")
            else:
                recipe_name_search = st.text_input("Enter recipe name", placeholder="e.g., IPA, Stout, Pale Ale", key="forum_name_search")
        
        # Filter recipes based on search
        if search_by == "Style" and selected_style:
            recipes_to_display = [r for r in all_forum_recipes if r.get('style') == selected_style]
            st.info(f"Found **{len(recipes_to_display)}** recipes in style: **{selected_style}**")
        elif search_by == "Recipe Name" and recipe_name_search:
            search_term = recipe_name_search.lower()
            recipes_to_display = [r for r in all_forum_recipes if search_term in r.get('name', '').lower()]
            st.info(f"Found **{len(recipes_to_display)}** recipes matching: **{recipe_name_search}**")
        else:
            recipes_to_display = []
            st.info("👆 Select a style or enter a recipe name to view recipes")
        
        st.markdown("---")
    else:  # Guy's Recipes
        # Load Guy's recipes
        if os.path.exists('data/recipes/guys.json'):
            with open('data/recipes/guys.json', 'r') as f:
                guys_recipes = json.load(f)
        else:
            st.error("Guy's recipes file not found!")
            return
        
        recipes_to_display = guys_recipes
        is_user_recipes = False
        
        st.info(f"Displaying **{len(recipes_to_display)}** recipes from Guy's collection")
        st.markdown("---")
    
    # Display recipes as cards (only if there are recipes to display)
    for idx, recipe in enumerate(recipes_to_display):
        # Handle different recipe structures
        recipe_name = recipe.get('name') or recipe.get('beer', 'Unknown')
        recipe_style = recipe.get('style', 'N/A')
        
        with st.expander(f"🍺 {recipe_name} - {recipe_style}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # Display basic info
                if recipe.get('brewer'):
                    st.markdown(f"**Brewer:** {recipe.get('brewer')}")
                if recipe.get('acronym'):
                    st.markdown(f"**Acronym:** {recipe.get('acronym')}")
                if recipe.get('recipe_source'):
                    st.markdown(f"**Recipe Source:** {recipe.get('recipe_source')}")
                    
                # Batch size
                batch_size = recipe.get('batch_size') or recipe.get('statistics', {}).get('volume')
                if batch_size:
                    st.markdown(f"**Batch Size:** {batch_size} liters")
                    
                # Brew date
                brew_date = recipe.get('brew_date') or recipe.get('date')
                if brew_date:
                    st.markdown(f"**Brew Date:** {brew_date}")
                    
                # Yeast
                yeast = recipe.get('yeast')
                if isinstance(yeast, dict):
                    yeast_str = f"{yeast.get('name', 'N/A')} - {yeast.get('amount', '')}"
                    st.markdown(f"**Yeast:** {yeast_str}")
                elif yeast:
                    st.markdown(f"**Yeast:** {yeast}")
            
            with col2:
                # Statistics
                stats = recipe.get('statistics', {})
                og = recipe.get('og') or stats.get('og')
                fg = recipe.get('fg') or stats.get('fg')
                abv = recipe.get('abv') or stats.get('abv')
                ibu = recipe.get('ibu') or stats.get('ibu')
                
                if og:
                    st.markdown(f"**OG:** {og}")
                if fg:
                    st.markdown(f"**FG:** {fg}")
                if abv:
                    st.markdown(f"**ABV:** {abv}%")
                if ibu:
                    st.markdown(f"**IBU:** {ibu}")
            
            # Grain Bill - handle both formats
            grain_bill = recipe.get('grain_bill') or recipe.get('malts')
            if grain_bill:
                st.markdown("**Grain Bill:**")
                grain_data = []
                for grain in grain_bill:
                    grain_type = grain.get('type') or grain.get('name', 'Unknown')
                    grain_weight = grain.get('weight', 0)
                    grain_data.append({'Grain Type': grain_type, 'Weight (kg)': grain_weight})
                grain_df = pd.DataFrame(grain_data)
                st.dataframe(grain_df, use_container_width=True, hide_index=True)
            
            # Hop Schedule - handle both formats
            hop_schedule = recipe.get('hop_schedule') or recipe.get('hops')
            if hop_schedule:
                st.markdown("**Hop Schedule:**")
                hop_data = []
                for hop in hop_schedule:
                    variety = hop.get('variety') or hop.get('name', 'Unknown')
                    weight = hop.get('weight', 0)
                    time = hop.get('time') or hop.get('timing', 'N/A')
                    hop_data.append({'Variety': variety, 'Weight (g)': weight, 'Time (min)': time})
                hop_df = pd.DataFrame(hop_data)
                st.dataframe(hop_df, use_container_width=True, hide_index=True)
            
            # Water Volumes Table
            if recipe.get('mash_volume') or recipe.get('sparge_volume') or recipe.get('pre_boil_volume') or recipe.get('final_volume'):
                st.markdown("**Water Volumes:**")
                water_data = []
                if recipe.get('mash_volume'):
                    mash_vol = recipe.get('mash_volume')
                    water_data.append({"Parameter": "Mash Volume", "Volume (L)": f"{mash_vol:.1f}" if isinstance(mash_vol, (int, float)) else str(mash_vol)})
                if recipe.get('sparge_volume'):
                    sparge_vol = recipe.get('sparge_volume')
                    water_data.append({"Parameter": "Sparge Volume", "Volume (L)": f"{sparge_vol:.1f}" if isinstance(sparge_vol, (int, float)) else str(sparge_vol)})
                if recipe.get('pre_boil_volume'):
                    pre_boil_vol = recipe.get('pre_boil_volume')
                    water_data.append({"Parameter": "Pre-boil Volume", "Volume (L)": f"{pre_boil_vol:.1f}" if isinstance(pre_boil_vol, (int, float)) else str(pre_boil_vol)})
                if recipe.get('final_volume'):
                    final_vol = recipe.get('final_volume')
                    water_data.append({"Parameter": "Final Volume", "Volume (L)": f"{final_vol:.1f}" if isinstance(final_vol, (int, float)) else str(final_vol)})
                if water_data:
                    water_df = pd.DataFrame(water_data)
                    st.dataframe(water_df, use_container_width=True, hide_index=True)
            
            # Protocol (Mash & Boil) - handle Guy's format
            protocol = recipe.get('protocol', {})
            if protocol or recipe.get('mash_temp') or recipe.get('mash_time') or recipe.get('boil_temp') or recipe.get('boil_time'):
                st.markdown("**Protocol:**")
                protocol_data = []
                
                # From Guy's format
                if protocol:
                    for step_name, step_data in protocol.items():
                        if isinstance(step_data, dict):
                            temp = step_data.get('temperature', 'N/A')
                            time = step_data.get('time', 'N/A')
                            protocol_data.append({
                                "Step": step_name.title(),
                                "Temperature (°C)": str(temp),
                                "Time (min)": str(time)
                            })
                # From standard format
                else:
                    mash_temp = recipe.get('mash_temp')
                    mash_time = recipe.get('mash_time')
                    if mash_temp or mash_time:
                        mash_temp_str = f"{mash_temp:.1f}" if isinstance(mash_temp, (int, float)) else (str(mash_temp) if mash_temp else "N/A")
                        mash_time_str = str(mash_time) if mash_time else "N/A"
                        protocol_data.append({"Step": "Mash", "Temperature (°C)": mash_temp_str, "Time (min)": mash_time_str})
                    
                    boil_temp = recipe.get('boil_temp')
                    boil_time = recipe.get('boil_time')
                    if boil_temp or boil_time:
                        boil_temp_str = f"{boil_temp:.1f}" if isinstance(boil_temp, (int, float)) else (str(boil_temp) if boil_temp else "N/A")
                        boil_time_str = str(boil_time) if boil_time else "N/A"
                        protocol_data.append({"Step": "Boil", "Temperature (°C)": boil_temp_str, "Time (min)": boil_time_str})
                
                if protocol_data:
                    protocol_df = pd.DataFrame(protocol_data)
                    st.dataframe(protocol_df, use_container_width=True, hide_index=True)
            
            # Fermentation - handle both formats
            fermentation = recipe.get('fermentation', [])
            if fermentation or recipe.get('fermentation_temp') or recipe.get('fermentation_days'):
                st.markdown("**Fermentation:**")
                
                # From Guy's format (list of stages)
                if isinstance(fermentation, list) and fermentation:
                    ferm_data = []
                    for stage in fermentation:
                        stage_name = stage.get('stage', 'Unknown')
                        stage_time = stage.get('time', 'N/A')
                        stage_temp = stage.get('temperature', 'N/A')
                        ferm_data.append({
                            "Stage": stage_name,
                            "Time": str(stage_time),
                            "Temperature (°C)": str(stage_temp)
                        })
                    ferm_df = pd.DataFrame(ferm_data)
                    st.dataframe(ferm_df, use_container_width=True, hide_index=True)
                # From standard format
                else:
                    ferm_temp = recipe.get('fermentation_temp')
                    ferm_days = recipe.get('fermentation_days')
                    ferm_temp_str = f"{ferm_temp:.1f}" if isinstance(ferm_temp, (int, float)) else (str(ferm_temp) if ferm_temp else "N/A")
                    ferm_days_str = str(ferm_days) if ferm_days else "N/A"
                    
                    fermentation_data = [{"Temperature (°C)": ferm_temp_str, "Duration (days)": ferm_days_str}]
                    fermentation_df = pd.DataFrame(fermentation_data)
                    st.dataframe(fermentation_df, use_container_width=True, hide_index=True)
            
            if recipe.get('notes'):
                st.markdown(f"**Notes:** {recipe['notes']}")
            
            st.markdown("---")
            
            # Action buttons
            if is_user_recipes:
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    csv_string = export_recipe_to_csv(recipe)
                    st.download_button(
                        label="📥 Export as CSV",
                        data=csv_string,
                        file_name=f"{recipe['name'].replace(' ', '_').lower()}.csv",
                        mime="text/csv",
                        key=f"export_{idx}"
                    )
                
                with btn_col2:
                    if st.button(f"🗑️ Delete Recipe", key=f"delete_{idx}"):
                        st.session_state.recipes.pop(idx)
                        with open('data/recipes/recipes.json', 'w') as f:
                            json.dump(st.session_state.recipes, f, indent=2)
                        st.rerun()
            else:
                # For precompiled recipes, show export and import buttons
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    csv_string = export_recipe_to_csv(recipe)
                    st.download_button(
                        label="📥 Export as CSV",
                        data=csv_string,
                        file_name=f"{recipe['name'].replace(' ', '_').lower()}.csv",
                        mime="text/csv",
                        key=f"export_{idx}"
                    )
                
                with btn_col2:
                    if st.button(f"📋 Import to Recipe Builder", key=f"import_{idx}"):
                        import_recipe_to_builder(recipe)
                        st.session_state.navigate_to_page = "Recipe Builder"
                        st.rerun()


def calculator_page():
    st.header("🧮 Brewing Calculators")
    
    calc_type = st.selectbox(
        "Select Calculator",
        ["ABV Calculator", "Priming Sugar Calculator", "Gravity Temperature Correction"]
    )
    
    if calc_type == "ABV Calculator":
        st.subheader("ABV Calculator")
        og = st.number_input("Original Gravity", min_value=1.000, max_value=1.200, value=1.050, step=0.001)
        fg = st.number_input("Final Gravity", min_value=1.000, max_value=1.030, value=1.010, step=0.001)
        
        abv = calculate_abv(og, fg)
        st.success(f"Estimated ABV: **{abv}%**")
    
    elif calc_type == "Priming Sugar Calculator":
        st.subheader("Priming Sugar Calculator")
        
        st.markdown("""
        Calculate the amount of priming sugar needed to carbonate your beer. This calculator accounts for 
        the CO2 already dissolved in your beer based on temperature.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            volume = st.number_input("Beer Volume (liters)", min_value=4.0, max_value=190.0, value=19.0, step=1.0)
            beer_temp = st.number_input("Beer Temperature (°C)", min_value=0.0, max_value=30.0, value=20.0, step=0.5, 
                                       help="Usually the fermentation temperature or current temperature if cold crashed")
        
        with col2:
            co2_level = st.number_input("Desired CO2 Volumes", min_value=1.5, max_value=4.5, value=2.5, step=0.1,
                                       help="Typical: Lager 2.5, Ale 2.0-2.5, Wheat 3.0-4.0")
            sugar_type = st.selectbox("Sugar Type", ["Corn Sugar (Dextrose)", "Table Sugar (Sucrose)"])
        
        # Calculate dissolved CO2 already in beer based on temperature (Celsius)
        # Polynomial approximation for CO2 solubility in beer (gives 0.86 at 20°C)
        dissolved_co2 = -0.000316 * (beer_temp ** 2) + 0.0052 * beer_temp + 0.876
        
        # Calculate additional CO2 needed
        co2_needed = co2_level - dissolved_co2
        
        # Calculate sugar needed based on type
        # Corn sugar: 4.39g per liter to produce 1 volume of CO2 (accounting for 91% fermentability)
        # Table sugar: 4.0g per liter to produce 1 volume of CO2 (100% fermentable)
        if sugar_type == "Corn Sugar (Dextrose)":
            sugar_g = volume * co2_needed * 4.39
        else:  # Table sugar
            sugar_g = volume * co2_needed * 4.0
        
        st.success(f"**{sugar_type}** Needed: **{sugar_g:.1f} g**")
        
        # Additional information
        st.info(f"📊 Dissolved CO2 in beer at {beer_temp}°C: **{dissolved_co2:.2f} volumes**")
        st.info(f"📊 Additional CO2 needed: **{co2_needed:.2f} volumes**")
        
        if co2_needed < 0:
            st.warning("⚠️ Your beer already has more CO2 than desired. Consider venting or serving at a warmer temperature.")
        
        # Carbonation guidelines
        st.markdown("---")
        st.markdown("### Carbonation Guidelines by Style")
        
        guidelines_data = {
            "Style": [
                "British Style Ales",
                "Belgian Ales",
                "American Ales and Lager",
                "Fruit Lambic",
                "Porter, Stout",
                "European Lagers",
                "Lambic",
                "German Wheat Beer"
            ],
            "CO2 Volumes": [
                "1.5 - 2.0",
                "1.9 - 2.4",
                "2.2 - 2.7",
                "3.0 - 4.5",
                "1.7 - 2.3",
                "2.2 - 2.7",
                "2.4 - 2.8",
                "3.3 - 4.5"
            ]
        }
        
        guidelines_df = pd.DataFrame(guidelines_data)
        st.dataframe(guidelines_df, use_container_width=True, hide_index=True)
    
    elif calc_type == "Gravity Temperature Correction":
        st.subheader("Gravity Temperature Correction")
        st.markdown("Hydrometers are typically calibrated at 20°C (68°F). Use this calculator to correct readings taken at other temperatures.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            measured_gravity = st.number_input("Measured Gravity", min_value=1.000, max_value=1.200, value=1.050, step=0.001)
            measured_temp = st.number_input("Sample Temperature (°C)", min_value=0.0, max_value=100.0, value=25.0, step=0.5)
        
        with col2:
            calibration_temp = st.number_input("Hydrometer Calibration Temp (°C)", min_value=0.0, max_value=30.0, value=20.0, step=0.5)
        
        # Temperature correction formula
        # Standard hydrometer correction accounting for thermal expansion of liquid
        # Formula: CG = MG + (T - Tcal) * 0.000325
        # This is the linear approximation used by most brewing calculators
        temp_difference = measured_temp - calibration_temp
        
        # Apply correction: add 0.000325 per degree C above calibration temp
        correction_amount = temp_difference * 0.000325
        corrected_gravity = measured_gravity + correction_amount
        
        st.success(f"Corrected Gravity: **{corrected_gravity:.3f}**")
        
        if temp_difference > 0:
            st.info(f"📊 Sample is {temp_difference:.1f}°C warmer than calibration temperature. Correction: +{correction_amount:.3f}")
        elif temp_difference < 0:
            st.info(f"📊 Sample is {abs(temp_difference):.1f}°C cooler than calibration temperature. Correction: {correction_amount:.3f}")
        else:
            st.info("📊 Sample is at calibration temperature. No correction needed.")


def recipe_scaler_page():
    # Initialise session state for scaled recipe
    if 'scaled_recipe' not in st.session_state:
        st.session_state.scaled_recipe = None
    
    st.subheader("📋 Recipe Details")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Check for imported recipe data to pre-fill form
    imported_data = st.session_state.get('imported_recipe_data', {})
    
    with col1:
        recipe_name_import = st.text_input("Recipe Name", placeholder="e.g., Clone IPA", 
                                          value=imported_data.get('name', ''))
    
    with col2:
        recipe_style = st.text_input("Beer Style", placeholder="e.g., American IPA",
                                    value=imported_data.get('style', ''))
    
    with col3:
        brewer_name_import = st.text_input("Brewer Name", placeholder="Your Name", key="import_brewer",
                                          value=imported_data.get('brewer', ''))

    with col4:
        planned_brew_date = st.date_input("Planned Brew Date", datetime.now(), key="import_brew_date")

    st.markdown("---")

    st.subheader("⚖️ Scaling factor")

    col1, col2 = st.columns(2)
    
    # Use imported batch size if available
    default_batch_size = imported_data.get('batch_size', 19.0)

    with col1:
        original_batch_size = st.number_input("Original Batch Size (liters)", min_value=1.0, max_value=500.0, 
                                             value=float(default_batch_size), step=1.0)
     
    with col2:
        target_batch_size = st.number_input("Target Batch Size (liters)", min_value=1.0, max_value=500.0, 
                                           value=float(default_batch_size), step=1.0)
    
    # Calculate scaling factor
    if original_batch_size > 0:
        scale_factor = target_batch_size / original_batch_size
        if scale_factor != 1.0:
            st.info(f"📊 Scaling factor: **{scale_factor:.2f}x** (from {original_batch_size}L to {target_batch_size}L)")
    else:
        scale_factor = 1.0
    
    st.markdown("---")
    
    # Grain Bill Input
    st.subheader("🌾 Grain Bill")
    st.markdown("Enter each grain ingredient from the recipe:")
    
    if 'import_grain_bill' not in st.session_state:
        st.session_state.import_grain_bill = []
    
    with st.expander("Add Grain", expanded=True):
        gcol1, gcol2, gcol3, gcol4 = st.columns([2, 1, 1, 1])
        
        with gcol1:
            grain_name = st.text_input("Grain Name", placeholder="e.g., Pale Malt", key="import_grain_name")
        
        with gcol2:
            grain_amount = st.number_input("Amount (kg)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, key="import_grain_amount")
        
        with gcol3:
            st.write("")
            st.write("")
            if st.button("Add Grain", key="add_import_grain"):
                if grain_name:
                    scaled_amount = grain_amount * scale_factor
                    st.session_state.import_grain_bill.append({
                        'name': grain_name,
                        'original_amount': grain_amount,
                        'scaled_amount': round(scaled_amount, 2)
                    })
                    st.rerun()
        
        with gcol4:
            st.write("")
            st.write("")
            if st.button("Remove Last", key="remove_last_grain"):
                if st.session_state.import_grain_bill:
                    st.session_state.import_grain_bill.pop()
                    st.rerun()
    
    if st.session_state.import_grain_bill:
        st.markdown("**Grain Bill:**")
        grain_data = []
        for grain in st.session_state.import_grain_bill:
            # Recalculate scaled amount based on current scale factor
            current_scaled_amount = grain['original_amount'] * scale_factor
            grain_data.append({
                'Grain': grain['name'],
                'Original (kg)': grain['original_amount'],
                'Scaled (kg)': round(current_scaled_amount, 2)
            })
        grain_df = pd.DataFrame(grain_data)
        st.dataframe(grain_df, use_container_width=True)
        
        if st.button("Clear Grain Bill", key="clear_import_grain"):
            st.session_state.import_grain_bill = []
            st.rerun()
    
    st.markdown("---")
    
    # Hop Schedule Input
    st.subheader("🌿 Hop Schedule")
    st.markdown("Enter each hop addition from the recipe:")
    
    if 'import_hop_schedule' not in st.session_state:
        st.session_state.import_hop_schedule = []
    
    with st.expander("Add Hop Addition", expanded=True):
        hcol1, hcol2, hcol3, hcol4 = st.columns([2, 1, 1, 1])
        
        with hcol1:
            hop_name = st.text_input("Hop Variety", placeholder="e.g., Cascade", key="import_hop_name")
        
        with hcol2:
            hop_amount = st.number_input("Amount (g)", min_value=0.0, max_value=1000.0, value=28.0, step=5.0, key="import_hop_amount")
        
        with hcol3:
            hop_timing = st.number_input("Time (min)", min_value=0, max_value=120, value=60, step=5, key="import_hop_time")
        
        with hcol4:
            st.write("")
            st.write("")
            if st.button("Add Hop", key="add_import_hop"):
                if hop_name:
                    scaled_amount = hop_amount * scale_factor
                    st.session_state.import_hop_schedule.append({
                        'variety': hop_name,
                        'original_amount': hop_amount,
                        'scaled_amount': round(scaled_amount, 1),
                        'time': hop_timing
                    })
                    st.rerun()
    
    if st.session_state.import_hop_schedule:
        st.markdown("**Hop Schedule:**")
        hop_data = []
        for hop in st.session_state.import_hop_schedule:
            # Recalculate scaled amount based on current scale factor
            current_scaled_amount = hop['original_amount'] * scale_factor
            hop_data.append({
                'Variety': hop['variety'],
                'Original (g)': hop['original_amount'],
                'Scaled (g)': round(current_scaled_amount, 1),
                'Time (min)': hop['time']
            })
        hop_df = pd.DataFrame(hop_data)
        st.dataframe(hop_df, use_container_width=True)
        
        if st.button("Clear Hop Schedule", key="clear_import_hop"):
            st.session_state.import_hop_schedule = []
            st.rerun()
    
    st.markdown("---")
    
    # Other Ingredients
    st.subheader("🧪 Other Ingredients (Optional)")
    
    if 'import_other_ingredients' not in st.session_state:
        st.session_state.import_other_ingredients = []
    
    with st.expander("Add Other Ingredient", expanded=False):
        ocol1, ocol2, ocol3, ocol4, ocol5 = st.columns([2, 1, 1, 1, 1])
        
        with ocol1:
            other_name = st.text_input("Ingredient", placeholder="e.g., Irish Moss, Yeast Nutrient", key="import_other_name")
        
        with ocol2:
            other_amount = st.number_input("Amount", min_value=0.0, max_value=10000.0, value=10.0, step=1.0, key="import_other_amount")
        
        with ocol3:
            other_unit = st.selectbox("Unit", ["g", "kg", "ml", "L", "tsp", "tbsp", "packet"], key="import_other_unit")
        
        with ocol4:
            other_scale = st.checkbox("Scale", value=True, key="import_other_scale", help="Scale this ingredient with batch size")
        
        with ocol5:
            st.write("")
            st.write("")
            if st.button("Add", key="add_import_other"):
                if other_name:
                    st.session_state.import_other_ingredients.append({
                        'name': other_name,
                        'original_amount': other_amount,
                        'unit': other_unit,
                        'should_scale': other_scale and other_unit in ["g", "kg", "ml", "L"]
                    })
                    st.rerun()
    
    if st.session_state.import_other_ingredients:
        st.markdown("**Other Ingredients:**")
        other_data = []
        for ingredient in st.session_state.import_other_ingredients:
            # Recalculate scaled amount based on current scale factor and should_scale flag
            should_scale = ingredient.get('should_scale', True)
            if should_scale:
                current_scaled_amount = ingredient['original_amount'] * scale_factor
            else:
                current_scaled_amount = ingredient['original_amount']
            
            other_data.append({
                'Ingredient': ingredient['name'],
                'Original': f"{ingredient['original_amount']} {ingredient['unit']}",
                'Scaled': f"{round(current_scaled_amount, 3)} {ingredient['unit']}"
            })
        other_df = pd.DataFrame(other_data)
        st.dataframe(other_df, use_container_width=True)
        
        if st.button("Clear Other Ingredients", key="clear_import_other"):
            st.session_state.import_other_ingredients = []
            st.rerun()
    
    st.markdown("---")
    
    # Water Volumes Section
    st.subheader("💧 Water Volumes")
    
    # Calculate total grain weight for water calculations (recalculate based on current scale factor)
    total_grain_weight = sum(g['original_amount'] * scale_factor for g in st.session_state.import_grain_bill) if st.session_state.import_grain_bill else 0
    
    wcol1, wcol2 = st.columns(2)
    
    with wcol1:
        import_final_volume = st.number_input("Final Expected Volume (liters)", min_value=0.0, max_value=200.0, value=target_batch_size, step=0.5, key="import_final_volume")
    
    with wcol2:
        water_to_grist_ratio = st.number_input("Water-to-Grist Ratio (L/kg)", min_value=2.0, max_value=4.0, value=2.5, step=0.1, key="water_grist_ratio", help="Typical range: 2.5-3.5 L/kg")
    
    # Calculate water volumes based on grain bill and final volume
    if total_grain_weight > 0 and import_final_volume > 0:
        # Mash water calculation based on water-to-grist ratio
        calculated_mash_volume = total_grain_weight * water_to_grist_ratio
        
        # Account for water absorbed by grain (approximately 1L per kg)
        grain_absorption = total_grain_weight * 1.0
        
        # Account for boil-off (20% loss during boil)
        boil_off_volume = import_final_volume * 0.2
        pre_boil_volume = import_final_volume + boil_off_volume
        
        # Sparge water needed = pre-boil volume - (mash water - grain absorption)
        mash_runoff = calculated_mash_volume - grain_absorption
        calculated_sparge_volume = max(0, pre_boil_volume - mash_runoff)
        
        st.markdown("**Calculated Water Volumes (for scaled recipe):**")
        calc_wcol1, calc_wcol2, calc_wcol3, calc_wcol4 = st.columns(4)
        
        with calc_wcol1:
            st.metric("Mash Volume", f"{calculated_mash_volume:.1f} L", help=f"Based on {water_to_grist_ratio:.1f} L/kg ratio")
        
        with calc_wcol2:
            st.metric("Sparge Volume", f"{calculated_sparge_volume:.1f} L", help="Calculated to reach pre-boil volume")
        
        with calc_wcol3:
            st.metric("Pre-boil Volume", f"{pre_boil_volume:.1f} L", help="Volume before boiling")
        
        with calc_wcol4:
            st.metric("Total Water", f"{calculated_mash_volume + calculated_sparge_volume:.1f} L", help="Mash + Sparge volumes")
        
        st.info(f"📊 Grain Absorption: {grain_absorption:.1f} L | Boil-off: {pre_boil_volume - import_final_volume:.1f} L | Pre-boil Volume: {pre_boil_volume:.1f} L")
        
        # Use calculated values
        scaled_mash_volume = calculated_mash_volume
        scaled_sparge_volume = calculated_sparge_volume
        scaled_final_volume = import_final_volume
        scaled_pre_boil_volume = pre_boil_volume
    else:
        scaled_mash_volume = 0
        scaled_sparge_volume = 0
        scaled_final_volume = import_final_volume if import_final_volume > 0 else 0
        scaled_pre_boil_volume = 0
        
        if total_grain_weight == 0:
            st.warning("⚠️ Add grains to calculate water volumes automatically")
    
    st.markdown("---")
    
    # Gravity and ABV Section
    st.subheader("📊 Gravity & ABV")
    
    gcol1, gcol2, gcol3 = st.columns(3)
    
    # Use imported gravity values if available
    default_og = imported_data.get('og', 1.050)
    default_fg = imported_data.get('fg', 1.010)
    
    with gcol1:
        target_og = st.number_input("Target OG", min_value=1.000, max_value=1.200, 
                                   value=float(default_og) if default_og else 1.050, step=0.001, key="import_og")
    
    with gcol2:
        target_fg = st.number_input("Final Gravity (FG)", min_value=1.000, max_value=1.030, 
                                   value=float(default_fg) if default_fg else 1.010, step=0.001, key="import_fg")
    
    with gcol3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if target_og and target_fg:
            calculated_abv = calculate_abv(target_og, target_fg)
            st.metric("ABV", f"{calculated_abv}%")
    
    st.markdown("---")
    
    # Mash and Boil Section
    st.subheader("🔥 Mash & Boil")
    
    # Use imported mash/boil values if available
    default_mash_temp = imported_data.get('mash_temp', 67.0)
    default_mash_time = imported_data.get('mash_time', 60)
    default_boil_temp = imported_data.get('boil_temp', 100.0)
    default_boil_time = imported_data.get('boil_time', 60)
    
    mcol1, mcol2 = st.columns(2)
    
    with mcol1:
        mash_temp = st.number_input("Mash Temperature (°C)", min_value=60.0, max_value=77.0, 
                                   value=float(default_mash_temp) if default_mash_temp else 67.0, step=0.5, key="import_mash_temp")
    
    with mcol2:
        mash_time = st.number_input("Mash Time (minutes)", min_value=30, max_value=120, 
                                   value=int(default_mash_time) if default_mash_time else 60, step=5, key="import_mash_time")
    
    bcol1, bcol2 = st.columns(2)
    
    with bcol1:
        boil_temp = st.number_input("Boil Temperature (°C)", min_value=95.0, max_value=105.0, 
                                   value=float(default_boil_temp) if default_boil_temp else 100.0, step=0.5, key="import_boil_temp")
    
    with bcol2:
        boil_time = st.number_input("Boil Time (minutes)", min_value=30, max_value=120, 
                                   value=int(default_boil_time) if default_boil_time else 60, step=5, key="import_boil_time")
    
    st.markdown("---")
    
    # Fermentation
    st.subheader("🦠 Fermentation")
    
    fcol1, fcol2 = st.columns(2)
    
    # Use imported fermentation values if available
    default_yeast = imported_data.get('yeast', '')
    default_ferm_temp = imported_data.get('fermentation_temp', 20.0)
    default_ferm_days = imported_data.get('fermentation_days', 14)
    
    with fcol1:
        yeast_info = st.text_input("Yeast", placeholder="e.g., US-05", key="import_yeast",
                                  value=default_yeast if default_yeast else '')
    
    with fcol2:
        fermentation_temp = st.number_input("Fermentation Temperature (°C)", min_value=10.0, max_value=30.0, 
                                           value=float(default_ferm_temp) if default_ferm_temp else 20.0, step=0.5, key="import_ferm_temp")
    
    fcol3, fcol4 = st.columns(2)
    
    with fcol3:
        fermentation_days = st.number_input("Fermentation Duration (days)", min_value=1, max_value=60, 
                                          value=int(default_ferm_days) if default_ferm_days else 14, step=1, key="import_ferm_days")
    
    with fcol4:
        st.write("")  # Spacer for alignment
    
    st.markdown("---")
    
    # Notes
    st.subheader("📝 Notes")
    default_notes = imported_data.get('notes', '')
    recipe_notes = st.text_area("Recipe Notes & Instructions", 
                                placeholder="Enter any additional notes, brewing instructions, or special techniques...",
                                key="import_notes",
                                value=default_notes if default_notes else '')
    
    st.markdown("---")
    
    # Save Scaled Recipe
    if st.button("💾 Save Scaled Recipe", type="primary"):
        if not recipe_name_import:
            st.error("Please enter a recipe name")
        elif not st.session_state.import_grain_bill and not st.session_state.import_hop_schedule:
            st.error("Please add at least some ingredients")
        else:
            # Convert grain bill to recipe format (recalculate with current scale factor)
            grain_bill_converted = []
            for grain in st.session_state.import_grain_bill:
                grain_bill_converted.append({
                    'type': grain['name'],
                    'weight': round(grain['original_amount'] * scale_factor, 2),
                    'ppg': 35,  # Default value
                    'lovibond': 0  # Default value
                })
            
            # Convert hop schedule to recipe format (recalculate with current scale factor)
            hop_schedule_converted = []
            for hop in st.session_state.import_hop_schedule:
                hop_schedule_converted.append({
                    'variety': hop['variety'],
                    'weight': round(hop['original_amount'] * scale_factor, 1),
                    'time': hop['time'],
                    'alpha_acid': 0  # Default value
                })
            
            # Convert other ingredients (recalculate with current scale factor)
            other_ingredients_converted = []
            if st.session_state.import_other_ingredients:
                for ingredient in st.session_state.import_other_ingredients:
                    should_scale = ingredient.get('should_scale', True)
                    if should_scale:
                        scaled_amt = ingredient['original_amount'] * scale_factor
                    else:
                        scaled_amt = ingredient['original_amount']
                    other_ingredients_converted.append({
                        'name': ingredient['name'],
                        'amount': round(scaled_amt, 3),
                        'unit': ingredient['unit']
                    })
            
            # Use gravity values from inputs
            og_value = target_og if target_og else 0
            fg_value = target_fg if target_fg else 0
            abv_value = calculate_abv(og_value, fg_value) if og_value and fg_value else 0
            
            # Create recipe notes with scaling info
            scaled_notes = f"Scaled from {original_batch_size}L to {target_batch_size}L (factor: {scale_factor:.2f}x)\n\n"
            if recipe_notes:
                scaled_notes += f"\n{recipe_notes}"
            
            # Create recipe object
            recipe = {
                'name': recipe_name_import,
                'style': recipe_style if recipe_style else "Imported Recipe",
                'brewer': brewer_name_import if brewer_name_import else 'Imported',
                'batch_size': target_batch_size,
                'efficiency': 75,
                'brew_date': planned_brew_date.strftime('%d/%m/%Y'),
                'grain_bill': grain_bill_converted,
                'hop_schedule': hop_schedule_converted,
                'other_ingredients': other_ingredients_converted if other_ingredients_converted else None,
                'yeast': yeast_info if yeast_info else 'N/A',
                'fermentation_temp': fermentation_temp if fermentation_temp else None,
                'fermentation_days': fermentation_days if fermentation_days else None,
                'mash_temp': mash_temp if mash_temp else None,
                'mash_time': mash_time if mash_time else None,
                'boil_temp': boil_temp if boil_temp else None,
                'boil_time': boil_time if boil_time else None,
                'mash_volume': scaled_mash_volume if scaled_mash_volume > 0 else None,
                'sparge_volume': scaled_sparge_volume if scaled_sparge_volume > 0 else None,
                'pre_boil_volume': scaled_pre_boil_volume if scaled_pre_boil_volume > 0 else None,
                'final_volume': scaled_final_volume if scaled_final_volume > 0 else None,
                'og': og_value,
                'fg': fg_value,
                'abv': abv_value,
                'notes': scaled_notes.strip(),
                'created_at': datetime.now().isoformat()
            }
            
            st.session_state.recipes.append(recipe)
            
            # Save to file
            os.makedirs('data/recipes', exist_ok=True)
            with open('data/recipes/recipes.json', 'w') as f:
                json.dump(st.session_state.recipes, f, indent=2)
            
            st.success(f"✅ Recipe '{recipe_name_import}' saved successfully!")
            st.info("📚 View your recipe in the 'View Recipes' page")
            
            # Clear form
            st.session_state.import_grain_bill = []
            st.session_state.import_hop_schedule = []
            st.session_state.import_other_ingredients = []
    
    # Clear all button
    if st.button("🗑️ Clear All", key="clear_all_import"):
        st.session_state.import_grain_bill = []
        st.session_state.import_hop_schedule = []
        st.session_state.import_other_ingredients = []
        st.rerun()


if __name__ == "__main__":
    main()
