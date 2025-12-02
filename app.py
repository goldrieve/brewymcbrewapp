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
    page_title="Homebrew Recipe Builder",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for recipes
if 'recipes' not in st.session_state:
    st.session_state.recipes = []

if 'current_recipe' not in st.session_state:
    st.session_state.current_recipe = None


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


def main():
    st.title("🍺 Homebrew Recipe Builder")
    st.markdown("Create and save your custom beer recipes")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Create Recipe", "View Recipes", "Recipe Library", "Brewing Calculator", "Recipe Scaler"]
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.info("Design your perfect homebrew recipe with precision and ease.")
    
    if page == "Create Recipe":
        create_recipe_page()
    elif page == "View Recipes":
        view_recipes_page()
    elif page == "Recipe Library":
        recipe_library_page()
    elif page == "Brewing Calculator":
        calculator_page()
    elif page == "Recipe Scaler":
        recipe_scaler_page()


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
                'brew_date': str(brew_date),
                'grain_bill': st.session_state.grain_bill,
                'hop_schedule': st.session_state.hop_schedule,
                'yeast': yeast,
                'fermentation_temp': fermentation_temp,
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
    st.header("📚 Your Recipes")
    
    # Load recipes from file if exists
    if os.path.exists('data/recipes/recipes.json') and not st.session_state.recipes:
        with open('data/recipes/recipes.json', 'r') as f:
            st.session_state.recipes = json.load(f)
    
    if not st.session_state.recipes:
        st.info("No recipes saved yet. Create your first recipe!")
        return
    
    # Display recipes as cards
    for idx, recipe in enumerate(st.session_state.recipes):
        with st.expander(f"🍺 {recipe['name']} - {recipe['style']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Brewer:** {recipe.get('brewer', 'N/A')}")
                st.markdown(f"**Batch Size:** {recipe['batch_size']} liters")
                st.markdown(f"**Brew Date:** {recipe.get('brew_date', 'N/A')}")
                st.markdown(f"**Yeast:** {recipe.get('yeast', 'N/A')}")
            
            with col2:
                st.markdown(f"**OG:** {recipe.get('og', 'N/A')}")
                st.markdown(f"**FG:** {recipe.get('fg', 'N/A')}")
                st.markdown(f"**ABV:** {recipe.get('abv', 'N/A')}%")
                st.markdown(f"**IBU:** {recipe.get('ibu', 'N/A')}")
                st.markdown(f"**SRM:** {recipe.get('srm', 'N/A')}")
            
            if recipe.get('grain_bill'):
                st.markdown("**Grain Bill:**")
                grain_df = pd.DataFrame(recipe['grain_bill'])
                st.dataframe(grain_df[['type', 'weight']], use_container_width=True)
            
            if recipe.get('hop_schedule'):
                st.markdown("**Hop Schedule:**")
                hop_df = pd.DataFrame(recipe['hop_schedule'])
                st.dataframe(hop_df[['variety', 'weight', 'time']], use_container_width=True)
            
            if recipe.get('notes'):
                st.markdown(f"**Notes:** {recipe['notes']}")
            
            if st.button(f"Delete Recipe", key=f"delete_{idx}"):
                st.session_state.recipes.pop(idx)
                with open('data/recipes/recipes.json', 'w') as f:
                    json.dump(st.session_state.recipes, f, indent=2)
                st.rerun()


def recipe_library_page():
    st.header("📖 Recipe Library")
    st.markdown("Browse popular homebrew recipes for inspiration")
    
    st.info("Coming soon: A curated collection of classic and award-winning homebrew recipes!")


def calculator_page():
    st.header("🧮 Brewing Calculators")
    
    calc_type = st.selectbox(
        "Select Calculator",
        ["ABV Calculator", "IBU Calculator", "Priming Sugar Calculator", "Strike Water Calculator"]
    )
    
    if calc_type == "ABV Calculator":
        st.subheader("ABV Calculator")
        og = st.number_input("Original Gravity", min_value=1.000, max_value=1.200, value=1.050, step=0.001)
        fg = st.number_input("Final Gravity", min_value=1.000, max_value=1.030, value=1.010, step=0.001)
        
        abv = calculate_abv(og, fg)
        st.success(f"Estimated ABV: **{abv}%**")
    
    elif calc_type == "Priming Sugar Calculator":
        st.subheader("Priming Sugar Calculator")
        volume = st.number_input("Beer Volume (liters)", min_value=4.0, max_value=190.0, value=19.0, step=1.0)
        co2_level = st.slider("Desired CO2 Volumes", min_value=1.5, max_value=4.0, value=2.5, step=0.1)
        
        # Simplified calculation (corn sugar) - convert to grams
        sugar_g = volume * co2_level * 1.32
        st.success(f"Corn Sugar Needed: **{sugar_g:.1f} g**")
    
    elif calc_type == "Strike Water Calculator":
        st.subheader("Strike Water Calculator")
        grain_weight = st.number_input("Grain Weight (kg)", min_value=0.5, max_value=22.0, value=4.5, step=0.5)
        target_temp = st.number_input("Target Mash Temperature (°C)", min_value=60, max_value=77, value=67)
        grain_temp = st.number_input("Grain Temperature (°C)", min_value=10, max_value=27, value=20)
        
        water_ratio = 3.0  # liters per kg
        strike_temp = target_temp + (0.2 * (target_temp - grain_temp))
        water_volume = grain_weight * water_ratio
        
        st.success(f"Strike Water Temperature: **{strike_temp:.1f}°C**")
        st.success(f"Water Volume Needed: **{water_volume:.1f} liters**")


def recipe_scaler_page():
    st.header("📏 Recipe Scaler & Importer")
    st.markdown("Import a recipe from online and scale it to your desired batch size")
    
    # Initialize session state for scaled recipe
    if 'scaled_recipe' not in st.session_state:
        st.session_state.scaled_recipe = None
    
    st.subheader("📋 Import Recipe")
    
    col1, col2 = st.columns(2)
    
    with col1:
        recipe_name_import = st.text_input("Recipe Name", placeholder="e.g., Clone IPA")
        original_batch_size = st.number_input("Original Batch Size (liters)", min_value=1.0, max_value=500.0, value=19.0, step=1.0)
    
    with col2:
        target_batch_size = st.number_input("Target Batch Size (liters)", min_value=1.0, max_value=500.0, value=19.0, step=1.0)
        recipe_style = st.text_input("Beer Style", placeholder="e.g., American IPA")
    
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
            grain_data.append({
                'Grain': grain['name'],
                'Original (kg)': grain['original_amount'],
                'Scaled (kg)': grain['scaled_amount']
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
            hop_data.append({
                'Variety': hop['variety'],
                'Original (g)': hop['original_amount'],
                'Scaled (g)': hop['scaled_amount'],
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
        ocol1, ocol2, ocol3, ocol4 = st.columns([2, 1, 1, 1])
        
        with ocol1:
            other_name = st.text_input("Ingredient", placeholder="e.g., Irish Moss, Yeast Nutrient", key="import_other_name")
        
        with ocol2:
            other_amount = st.number_input("Amount", min_value=0.0, max_value=1000.0, value=10.0, step=1.0, key="import_other_amount")
        
        with ocol3:
            other_unit = st.selectbox("Unit", ["g", "ml", "tsp", "tbsp", "packet"], key="import_other_unit")
        
        with ocol4:
            st.write("")
            st.write("")
            if st.button("Add", key="add_import_other"):
                if other_name:
                    # Only scale measurable units
                    if other_unit in ["g", "ml"]:
                        scaled_amount = other_amount * scale_factor
                    else:
                        scaled_amount = other_amount
                    
                    st.session_state.import_other_ingredients.append({
                        'name': other_name,
                        'original_amount': other_amount,
                        'scaled_amount': round(scaled_amount, 1),
                        'unit': other_unit
                    })
                    st.rerun()
    
    if st.session_state.import_other_ingredients:
        st.markdown("**Other Ingredients:**")
        other_data = []
        for ingredient in st.session_state.import_other_ingredients:
            other_data.append({
                'Ingredient': ingredient['name'],
                'Original': f"{ingredient['original_amount']} {ingredient['unit']}",
                'Scaled': f"{ingredient['scaled_amount']} {ingredient['unit']}"
            })
        other_df = pd.DataFrame(other_data)
        st.dataframe(other_df, use_container_width=True)
        
        if st.button("Clear Other Ingredients", key="clear_import_other"):
            st.session_state.import_other_ingredients = []
            st.rerun()
    
    st.markdown("---")
    
    # Additional Information
    st.subheader("📝 Additional Information")
    
    acol1, acol2 = st.columns(2)
    
    with acol1:
        yeast_info = st.text_input("Yeast", placeholder="e.g., US-05", key="import_yeast")
        mash_temp = st.text_input("Mash Temperature", placeholder="e.g., 67°C for 60 min", key="import_mash")
    
    with acol2:
        fermentation_info = st.text_input("Fermentation", placeholder="e.g., 20°C for 14 days", key="import_fermentation")
        target_og = st.text_input("Target OG", placeholder="e.g., 1.055", key="import_og")
    
    recipe_notes = st.text_area("Recipe Notes & Instructions", 
                                placeholder="Enter any additional notes, brewing instructions, or special techniques...",
                                key="import_notes")
    
    st.markdown("---")
    
    # Generate Scaled Recipe Summary
    if st.button("📊 Generate Scaled Recipe", type="primary"):
        if not recipe_name_import:
            st.error("Please enter a recipe name")
        elif not st.session_state.import_grain_bill and not st.session_state.import_hop_schedule:
            st.error("Please add at least some ingredients")
        else:
            st.success("✅ Recipe scaled successfully!")
            
            # Display summary
            st.markdown("---")
            st.subheader(f"📄 {recipe_name_import}")
            if recipe_style:
                st.markdown(f"**Style:** {recipe_style}")
            st.markdown(f"**Batch Size:** {target_batch_size} L")
            
            if scale_factor != 1.0:
                st.info(f"🔄 Scaled from {original_batch_size}L to {target_batch_size}L (factor: {scale_factor:.2f}x)")
            
            # Display scaled grain bill
            if st.session_state.import_grain_bill:
                st.markdown("### 🌾 Grain Bill")
                for grain in st.session_state.import_grain_bill:
                    st.markdown(f"- **{grain['scaled_amount']} kg** {grain['name']}")
                
                total_grain = sum(g['scaled_amount'] for g in st.session_state.import_grain_bill)
                st.markdown(f"**Total Grain:** {total_grain:.2f} kg")
            
            # Display scaled hop schedule
            if st.session_state.import_hop_schedule:
                st.markdown("### 🌿 Hop Schedule")
                for hop in st.session_state.import_hop_schedule:
                    st.markdown(f"- **{hop['scaled_amount']} g** {hop['variety']} @ {hop['time']} min")
            
            # Display other ingredients
            if st.session_state.import_other_ingredients:
                st.markdown("### 🧪 Other Ingredients")
                for ingredient in st.session_state.import_other_ingredients:
                    st.markdown(f"- **{ingredient['scaled_amount']} {ingredient['unit']}** {ingredient['name']}")
            
            # Display additional info
            if yeast_info or mash_temp or fermentation_info or target_og:
                st.markdown("### 📋 Brewing Information")
                if yeast_info:
                    st.markdown(f"**Yeast:** {yeast_info}")
                if mash_temp:
                    st.markdown(f"**Mash:** {mash_temp}")
                if fermentation_info:
                    st.markdown(f"**Fermentation:** {fermentation_info}")
                if target_og:
                    st.markdown(f"**Target OG:** {target_og}")
            
            if recipe_notes:
                st.markdown("### 📝 Notes")
                st.markdown(recipe_notes)
            
            # Option to export
            st.markdown("---")
            
            # Create CSV data for export
            csv_data = []
            
            # Add header info
            csv_data.append(["Recipe Name", recipe_name_import])
            if recipe_style:
                csv_data.append(["Style", recipe_style])
            csv_data.append(["Batch Size (L)", target_batch_size])
            csv_data.append(["Scaled From (L)", original_batch_size])
            csv_data.append(["Scale Factor", f"{scale_factor:.2f}x"])
            csv_data.append([])  # Empty row
            
            # Add grain bill
            if st.session_state.import_grain_bill:
                csv_data.append(["GRAIN BILL"])
                csv_data.append(["Ingredient", "Amount", "Unit"])
                for grain in st.session_state.import_grain_bill:
                    csv_data.append([grain['name'], grain['scaled_amount'], "kg"])
                csv_data.append(["Total Grain", sum(g['scaled_amount'] for g in st.session_state.import_grain_bill), "kg"])
                csv_data.append([])  # Empty row
            
            # Add hop schedule
            if st.session_state.import_hop_schedule:
                csv_data.append(["HOP SCHEDULE"])
                csv_data.append(["Variety", "Amount", "Unit", "Time (min)"])
                for hop in st.session_state.import_hop_schedule:
                    csv_data.append([hop['variety'], hop['scaled_amount'], "g", hop['time']])
                csv_data.append([])  # Empty row
            
            # Add other ingredients
            if st.session_state.import_other_ingredients:
                csv_data.append(["OTHER INGREDIENTS"])
                csv_data.append(["Ingredient", "Amount", "Unit"])
                for ingredient in st.session_state.import_other_ingredients:
                    csv_data.append([ingredient['name'], ingredient['scaled_amount'], ingredient['unit']])
                csv_data.append([])  # Empty row
            
            # Add brewing information
            csv_data.append(["BREWING INFORMATION"])
            if yeast_info:
                csv_data.append(["Yeast", yeast_info])
            if mash_temp:
                csv_data.append(["Mash", mash_temp])
            if fermentation_info:
                csv_data.append(["Fermentation", fermentation_info])
            if target_og:
                csv_data.append(["Target OG", target_og])
            
            if recipe_notes:
                csv_data.append([])  # Empty row
                csv_data.append(["NOTES"])
                csv_data.append([recipe_notes])
            
            # Convert to CSV string
            import io
            csv_buffer = io.StringIO()
            for row in csv_data:
                csv_buffer.write(','.join(str(cell) for cell in row) + '\n')
            csv_string = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Scaled Recipe (CSV)",
                data=csv_string,
                file_name=f"{recipe_name_import.replace(' ', '_').lower()}_scaled.csv",
                mime="text/csv"
            )
    
    # Clear all button
    if st.button("🗑️ Clear All", key="clear_all_import"):
        st.session_state.import_grain_bill = []
        st.session_state.import_hop_schedule = []
        st.session_state.import_other_ingredients = []
        st.rerun()


if __name__ == "__main__":
    main()
