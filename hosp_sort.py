# hospital_finder.py
"""
Module for finding hospitals near specified coordinates using the Haversine formula.
"""

import pandas as pd
import math
import os
import json


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the Earth (specified in decimal degrees)

    Parameters:
    ----------
    lat1, lon1 : float
        Latitude and longitude of point 1 (in decimal degrees)
    lat2, lon2 : float
        Latitude and longitude of point 2 (in decimal degrees)

    Returns:
    -------
    float
        Distance between the points in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r


def find_hospitals_near_coordinates(csv_file_path, target_lat, target_lon, radius=10):
    """
    Find hospitals within a given radius (in km) of the target coordinates
    and return results as a JSON object

    Parameters:
    ----------
    csv_file_path : str
        Path to the CSV file containing hospital data
    target_lat : float
        Target latitude in decimal degrees
    target_lon : float
        Target longitude in decimal degrees
    radius : float, optional
        Search radius in kilometers (default is 10)

    Returns:
    -------
    str
        JSON string containing the search results
    """
    # Check if file exists
    if not os.path.exists(csv_file_path):
        return json.dumps({"error": f"File '{csv_file_path}' not found."})

    # Read CSV file with low_memory=False to avoid DtypeWarning
    try:
        df = pd.read_csv(csv_file_path, low_memory=False)
    except Exception as e:
        return json.dumps({"error": f"Error reading CSV file: {e}"})

    # Clean up Location_Coordinates column and extract latitude and longitude
    hospitals_with_coords = []

    for _, row in df.iterrows():
        # Skip rows with missing coordinates
        if pd.isna(row['Location_Coordinates']):
            continue

        try:
            # Parse coordinates from string
            coords = str(row['Location_Coordinates']).strip()
            if coords:
                # Split by comma and handle potential extra spaces
                parts = [p.strip() for p in coords.split(',')]
                if len(parts) == 2:
                    lat, lon = map(float, parts)

                    # Calculate distance from target
                    distance = haversine_distance(target_lat, target_lon, lat, lon)

                    # Add hospital info with distance if within radius
                    if distance <= radius:
                        hospitals_with_coords.append({
                            'Hospital_Name': row['Hospital_Name'],
                            'Address': row['Address_Original_First_Line'],
                            'State': row['State'],
                            'District': row['District'],
                            'Pincode': row['Pincode'],
                            'Phone': row['Telephone'],
                            'Mobile': row['Mobile_Number'],
                            'Distance_km': round(distance, 2)
                        })
        except Exception as e:
            continue

    # Sort by distance
    hospitals_with_coords.sort(key=lambda x: x['Distance_km'])

    # Create result JSON
    result = {
        "count": len(hospitals_with_coords),
        "hospitals": hospitals_with_coords
    }

    # Return as formatted JSON string
    return json.dumps(result, indent=2)


def get_nearby_hospitals(csv_file_path, target_lat, target_lon, radius=10):
    """
    Find hospitals near coordinates but return Python dictionary instead of JSON string.
    Useful when you want to work with the data directly in Python.

    Parameters:
    ----------
    csv_file_path : str
        Path to the CSV file containing hospital data
    target_lat : float
        Target latitude in decimal degrees
    target_lon : float
        Target longitude in decimal degrees
    radius : float, optional
        Search radius in kilometers (default is 10)

    Returns:
    -------
    dict
        Dictionary containing the search results
    """
    json_result = find_hospitals_near_coordinates(csv_file_path, target_lat, target_lon, radius)
    return json.loads(json_result)


# Example usage
if __name__ == "__main__":
    # Replace with your actual file path
    csv_file_path = "hospital_directory.csv"

    # # Example target coordinates
    # target_lat = 19.867141
    # target_lon = 75.335294
    # search_radius = 15  # in kilometers
    #
    # # Find nearby hospitals and get JSON result
    # result_json = find_hospitals_near_coordinates(
    #     csv_file_path,
    #     target_lat,
    #     target_lon,
    #     radius=search_radius
    # )
    #
    # # Print the JSON result to console
    # print(result_json)