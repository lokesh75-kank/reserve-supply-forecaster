"""
Data Generation Module for Reserve Supply Forecaster

This module generates synthetic historical supply data with realistic patterns:
- Time-of-day patterns (rush hours, night shifts)
- Day-of-week patterns (weekends vs weekdays)
- Weather effects
- Event effects
- Reserve bookings impact
- Random noise with autocorrelation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_base_supply(hour, day_of_week, zone):
    """
    Generate base supply based on time-of-day, day-of-week, and zone patterns.
    
    Patterns:
    - Rush hours (7-9 AM, 5-7 PM): Higher demand, moderate supply
    - Night (10 PM - 2 AM): Lower supply
    - Weekends: Different patterns
    - Zone-specific base levels
    
    Args:
        hour: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)
        zone: Zone identifier (Z1-Z5)
    
    Returns:
        Base supply value (integer)
    """
    # Zone-specific base multipliers
    zone_bases = {'Z1': 25, 'Z2': 30, 'Z3': 20, 'Z4': 35, 'Z5': 28}
    base = zone_bases.get(zone, 25)
    
    # Time-of-day pattern (sinusoidal with peaks during rush hours)
    morning_rush = 1.3 if 7 <= hour < 9 else 1.0
    evening_rush = 1.4 if 17 <= hour < 19 else 1.0
    night_reduction = 0.6 if 22 <= hour or hour < 2 else 1.0
    midday = 0.9 if 10 <= hour < 14 else 1.0
    
    time_multiplier = morning_rush * evening_rush * night_reduction * midday
    
    # Day-of-week pattern (weekends have different patterns)
    if day_of_week >= 5:  # Saturday (5) or Sunday (6)
        weekend_multiplier = 0.85  # Slightly lower supply on weekends
        if 10 <= hour < 14:  # Weekend afternoons are busier
            weekend_multiplier = 1.1
    else:
        weekend_multiplier = 1.0
    
    return int(base * time_multiplier * weekend_multiplier)


def apply_weather_effect(supply, weather_severity):
    """
    Apply weather effects to supply.
    - Clear (0): Normal supply
    - Rain (1): Supply decreases by 10-15%
    - Storm (2): Supply decreases by 25-35%
    
    Args:
        supply: Current supply value
        weather_severity: Weather severity (0=clear, 1=rain, 2=storm)
    
    Returns:
        Adjusted supply value (integer)
    """
    if weather_severity == 0:
        return supply
    elif weather_severity == 1:
        # Rain: reduce supply by 10-15%
        reduction = np.random.uniform(0.10, 0.15)
        return int(supply * (1 - reduction))
    else:  # weather_severity == 2
        # Storm: reduce supply by 25-35%
        reduction = np.random.uniform(0.25, 0.35)
        return int(supply * (1 - reduction))


def generate_weather_severity():
    """
    Generate weather severity with realistic distribution.
    Most days are clear, some rain, rare storms.
    
    Returns:
        Weather severity (0=clear, 1=rain, 2=storm)
    """
    rand = np.random.random()
    if rand < 0.7:
        return 0  # Clear
    elif rand < 0.95:
        return 1  # Rain
    else:
        return 2  # Storm


def apply_event_effect(base_demand, event_density):
    """
    Apply event effects to demand (on_demand_requests).
    - No Event (0): Normal patterns
    - Small Event (1): +30-50 requests
    - Stadium Event (2): +100-200 requests
    
    Args:
        base_demand: Base demand value
        event_density: Event density (0=none, 1=small, 2=stadium)
    
    Returns:
        Adjusted demand value (integer)
    """
    if event_density == 0:
        return base_demand
    elif event_density == 1:
        return base_demand + np.random.randint(30, 51)
    else:  # event_density == 2
        return base_demand + np.random.randint(100, 201)


def generate_event_density(hour, day_of_week):
    """
    Generate event density with higher probability during evenings/weekends.
    
    Args:
        hour: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)
    
    Returns:
        Event density (0=none, 1=small, 2=stadium)
    """
    # Events more likely in evenings (5-10 PM) and weekends
    is_evening = 17 <= hour < 22
    is_weekend = day_of_week >= 5
    
    rand = np.random.random()
    if is_evening or is_weekend:
        if rand < 0.85:
            return 0
        elif rand < 0.98:
            return 1  # Small event
        else:
            return 2  # Stadium event
    else:
        if rand < 0.95:
            return 0
        elif rand < 0.99:
            return 1
        else:
            return 2


def compute_future_supply(current_supply, reserve_bookings, weather_severity, 
                          event_density, hour, day_of_week, zone):
    """
    Compute supply 2 hours ahead (active_drivers_t_plus_120).
    
    Factors:
    - Current supply (with autocorrelation)
    - Reserve bookings reduce available supply
    - Weather effects persist
    - Time-of-day pattern shifts
    
    Args:
        current_supply: Current active drivers
        reserve_bookings: Reserve bookings in next 60 min
        weather_severity: Current weather severity
        event_density: Current event density
        hour: Current hour of day
        day_of_week: Current day of week
        zone: Zone identifier
    
    Returns:
        Predicted active drivers 2 hours ahead (integer)
    """
    # Base future supply follows time pattern 2 hours ahead
    future_hour = (hour + 2) % 24
    future_day = day_of_week if hour + 2 < 24 else (day_of_week + 1) % 7
    
    future_base = generate_base_supply(future_hour, future_day, zone)
    
    # Autocorrelation: future supply correlated with current supply
    # But also follows time pattern
    autocorr_factor = 0.6  # 60% weight on current, 40% on time pattern
    future_supply = int(current_supply * autocorr_factor + future_base * (1 - autocorr_factor))
    
    # Reserve bookings reduce available supply
    future_supply = max(0, future_supply - int(reserve_bookings * 0.8))
    
    # Weather effects persist (slightly reduced)
    if weather_severity > 0:
        weather_reduction = weather_severity * 0.05  # Reduced impact
        future_supply = int(future_supply * (1 - weather_reduction))
    
    # Add some noise
    noise = np.random.normal(0, 2)
    future_supply = int(future_supply + noise)
    
    return max(0, future_supply)  # Ensure non-negative


def generate_synthetic_data(start_date=None, days=30, zones=None, output_path=None):
    """
    Generate synthetic historical supply data.
    
    Args:
        start_date: Start date (datetime object). Defaults to 2025-01-01
        days: Number of days to generate. Defaults to 30
        zones: List of zone identifiers. Defaults to ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
        output_path: Path to save CSV file. If None, doesn't save.
    
    Returns:
        DataFrame with synthetic supply data
    """
    if start_date is None:
        start_date = datetime(2025, 1, 1, 0, 0)
    if zones is None:
        zones = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']
    
    print("Generating synthetic supply data...")
    print(f"  Start date: {start_date.date()}")
    print(f"  Days: {days}")
    print(f"  Zones: {zones}")
    
    interval_minutes = 15
    intervals_per_day = 24 * 60 // interval_minutes  # 96 intervals
    
    rows = []
    
    # Track previous supply for autocorrelation
    prev_supply = {zone: 25 for zone in zones}
    
    for day in range(days):
        for interval in range(intervals_per_day):
            timestamp = start_date + timedelta(days=day, minutes=interval * interval_minutes)
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            
            for zone in zones:
                # Generate base supply
                base_supply = generate_base_supply(hour, day_of_week, zone)
                
                # Add autocorrelation from previous timestep
                autocorr = 0.3
                supply = int(base_supply * (1 - autocorr) + prev_supply[zone] * autocorr)
                
                # Apply weather effect
                weather_severity = generate_weather_severity()
                supply = apply_weather_effect(supply, weather_severity)
                
                # Add noise
                noise = np.random.normal(0, 3)
                supply = int(supply + noise)
                supply = max(0, supply)  # Ensure non-negative
                
                # Update previous supply
                prev_supply[zone] = supply
                
                # Generate other features
                event_density = generate_event_density(hour, day_of_week)
                
                # Reserve bookings (correlated with time and events)
                base_bookings = np.random.randint(0, 10)
                if event_density > 0:
                    base_bookings += np.random.randint(5, 15)
                reserve_bookings = base_bookings
                
                # On-demand requests (correlated with supply, time, events)
                base_demand = int(supply * np.random.uniform(1.2, 2.0))
                on_demand_requests = apply_event_effect(base_demand, event_density)
                
                # Compute future supply (target variable)
                active_drivers_t_plus_120 = compute_future_supply(
                    supply, reserve_bookings, weather_severity, 
                    event_density, hour, day_of_week, zone
                )
                
                rows.append({
                    'timestamp': timestamp,
                    'zone_id': zone,
                    'active_drivers': supply,
                    'reserve_bookings_next_60min': reserve_bookings,
                    'on_demand_requests_last_60min': on_demand_requests,
                    'weather_severity': weather_severity,
                    'event_density': event_density,
                    'hour_of_day': hour,
                    'day_of_week': day_of_week,
                    'active_drivers_t_plus_120': active_drivers_t_plus_120
                })
    
    df = pd.DataFrame(rows)
    print(f"\nGenerated {len(df)} rows of data")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Zones: {sorted(df['zone_id'].unique())}")
    print(f"  Supply range: {df['active_drivers'].min()}-{df['active_drivers'].max()}")
    
    # Save to CSV if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nSaved data to {output_path}")
    
    return df


def main():
    """Main function to generate and save data."""
    # Generate data
    output_path = os.path.join('data', 'synthetic_supply.csv')
    df = generate_synthetic_data(output_path=output_path)
    
    print("\nData generation complete!")
    return df


if __name__ == '__main__':
    main()

