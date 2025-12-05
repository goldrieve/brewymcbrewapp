"""
Utility functions for brewing calculations
"""

import numpy as np


def calculate_original_gravity(grain_bill, batch_size, efficiency=75):
    """
    Calculate Original Gravity (OG) based on grain bill and batch size.
    
    Args:
        grain_bill (list): List of grain dictionaries with 'weight' and 'ppg' keys
        batch_size (float): Batch size in litres
        efficiency (float): Brew house efficiency percentage (default 75%)
    
    Returns:
        float: Original Gravity (e.g., 1.055)
    """
    total_points = 0
    efficiency_factor = efficiency / 100.0
    
    for grain in grain_bill:
        # Convert ppg to metric (points per kg per litre)
        points = grain['weight'] * grain['ppg'] * 8.3454 * efficiency_factor
        total_points += points
    
    og = 1 + (total_points / batch_size) / 1000
    return round(og, 3)


def calculate_ibu_tinseth(hop_additions, og, batch_size):
    """
    Calculate IBU using the Tinseth formula.
    
    Args:
        hop_additions (list): List of hop dictionaries with 'weight', 'alpha_acid', and 'time' keys
        og (float): Original Gravity
        batch_size (float): Batch size in litres
    
    Returns:
        float: International Bitterness Units (IBU)
    """
    total_ibu = 0
    
    for hop in hop_additions:
        # Bigness factor
        bigness_factor = 1.65 * (0.000125 ** (og - 1.0))
        
        # Boil time factor
        boil_time_factor = (1 - np.exp(-0.04 * hop['time'])) / 4.15
        
        # Utilization
        utilization = bigness_factor * boil_time_factor
        
        # IBU calculation (weight in grams, batch in litres)
        ibu = (hop['alpha_acid'] / 100) * hop['weight'] * utilization * 10 / batch_size
        total_ibu += ibu
    
    return round(total_ibu, 1)


def calculate_srm_morey(grain_bill, batch_size):
    """
    Calculate SRM (beer colour) using the Morey equation.
    
    Args:
        grain_bill (list): List of grain dictionaries with 'weight' and 'lovibond' keys
        batch_size (float): Batch size in litres
    
    Returns:
        float: SRM value
    """
    # Calculate MCU (Malt Colour Units) - convert kg to lbs equivalent
    mcu = sum(grain['weight'] * 2.20462 * grain['lovibond'] for grain in grain_bill) / (batch_size * 0.264172)
    
    # Morey equation
    srm = 1.4922 * (mcu ** 0.6859)
    
    return round(srm, 1)


def calculate_abv(og, fg):
    """
    Calculate ABV (Alcohol By Volume).
    
    Args:
        og (float): Original Gravity
        fg (float): Final Gravity
    
    Returns:
        float: ABV percentage
    """
    abv = (og - fg) * 131.25
    return round(abv, 2)


def calculate_attenuation(og, fg):
    """
    Calculate apparent attenuation percentage.
    
    Args:
        og (float): Original Gravity
        fg (float): Final Gravity
    
    Returns:
        float: Attenuation percentage
    """
    attenuation = ((og - fg) / (og - 1.0)) * 100
    return round(attenuation, 1)


def calculate_calories(og, fg, volume_oz=12):
    """
    Calculate approximate calories per serving.
    
    Args:
        og (float): Original Gravity
        fg (float): Final Gravity
        volume_oz (float): Serving size in ounces (default 12 oz)
    
    Returns:
        int: Approximate calories
    """
    # Simplified formula based on alcohol and residual sugars
    abv = calculate_abv(og, fg)
    
    # Calories from alcohol
    alcohol_calories = 1881.22 * fg * (og - fg) / (1.775 - og)
    
    # Calories from carbs
    carb_calories = 3550 * fg * ((0.1808 * og) + (0.8192 * fg) - 1.0004)
    
    # Total per 12 oz serving
    total_calories = (alcohol_calories + carb_calories) * (volume_oz / 12)
    
    return int(round(total_calories))


def calculate_strike_water_temp(grain_weight, target_mash_temp, grain_temp=20, water_ratio=3.0):
    """
    Calculate strike water temperature for single infusion mashing.
    
    Args:
        grain_weight (float): Weight of grain in kilograms
        target_mash_temp (float): Target mash temperature in °C
        grain_temp (float): Initial grain temperature in °C (default 20)
        water_ratio (float): Water to grain ratio in litres per kg (default 3.0)
    
    Returns:
        dict: Dictionary with strike_temp and water_volume
    """
    # Simplified formula
    strike_temp = target_mash_temp + (0.2 * (target_mash_temp - grain_temp))
    water_volume = grain_weight * water_ratio
    
    return {
        'strike_temp': round(strike_temp, 1),
        'water_volume': round(water_volume, 1)
    }


def calculate_priming_sugar(volume_liters, co2_volumes=2.5, sugar_type='corn'):
    """
    Calculate priming sugar needed for bottle conditioning.
    
    Args:
        volume_litres (float): Beer volume in litres
        co2_volumes (float): Desired CO2 volumes (default 2.5)
        sugar_type (str): Type of sugar - 'corn', 'table', or 'dme' (default 'corn')
    
    Returns:
        float: Sugar needed in grams
    """
    # Factors for different sugar types (grams per litre per CO2 volume)
    sugar_factors = {
        'corn': 1.32,      # Corn sugar (dextrose)
        'table': 1.19,     # Table sugar (sucrose)
        'dme': 1.58        # Dry malt extract
    }
    
    factor = sugar_factors.get(sugar_type, 1.32)
    sugar_g = volume_liters * co2_volumes * factor
    
    return round(sugar_g, 1)


def convert_sg_to_plato(sg):
    """
    Convert specific gravity to degrees Plato.
    
    Args:
        sg (float): Specific gravity
    
    Returns:
        float: Degrees Plato
    """
    plato = (-1 * 616.868) + (1111.14 * sg) - (630.272 * sg**2) + (135.997 * sg**3)
    return round(plato, 2)


def convert_plato_to_sg(plato):
    """
    Convert degrees Plato to specific gravity.
    
    Args:
        plato (float): Degrees Plato
    
    Returns:
        float: Specific gravity
    """
    sg = 1 + (plato / (258.6 - ((plato / 258.2) * 227.1)))
    return round(sg, 3)
