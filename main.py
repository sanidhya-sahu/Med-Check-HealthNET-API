import pandas as pd
import json
import math
from fuzzywuzzy import process
from fastapi import FastAPI, Query, HTTPException
# from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from hosp_sort import find_hospitals_near_coordinates, get_nearby_hospitals

app = FastAPI()
# handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get('/med')
def lookup_medicine_info(query):
    data_path = "./Medicine_Details.csv"
    try:
        data = pd.read_csv(data_path)
    except FileNotFoundError:
        return {
            "error": f"Could not find the data file at {data_path}",
            "status": "error"
        }

    # Define column names
    df_name = "Medicine Name"
    df_usage = "Uses"
    df_compos = "Composition"
    df_se = "Side_effects"

    # Check if required columns exist
    required_columns = [df_name, df_usage, df_compos, df_se]
    for col in required_columns:
        if col not in data.columns:
            return {
                "error": f"Missing required column: {col}",
                "status": "error"
            }

    medicine_list = data[df_name].dropna().tolist()

    match = process.extractOne(query, medicine_list)

    if match:
        best_match, score = match

        if score < 70:
            return {
                "status": "no_match",
                "message": "No close enough match found",
                "match_score": score
            }

        matching_index = data[data[df_name] == best_match].index[0]

        return {
            "status": "success",
            "medicine_name": best_match,
            "match_score": score,
            "uses": data.loc[matching_index, df_usage],
            "composition": data.loc[matching_index, df_compos],
            "side_effects": data.loc[matching_index, df_se]
        }

    return {
        "status": "no_match",
        "message": "No match found"
    }


# Custom JSON encoder to handle non-compliant float values
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None  # Convert NaN/Infinity to None
        return super().default(obj)


def sanitize_json_data(data):
    """
    Clean a dictionary to ensure all values are JSON serializable.
    Converts NaN, Infinity, -Infinity to None.
    """
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data


@app.get('/hospitals')
async def get_nearby_hospitals_route(
        lat: float = Query(..., description="Latitude of the search location"),
        lon: float = Query(..., description="Longitude of the search location"),
        radius: float = Query(10.0, description="Search radius in kilometers")
):
    """
    Find hospitals near the specified coordinates within the given radius.
    Returns results as JSON with hospital details and distances.

    Example: /hospitals?lat=19.867141&lon=75.335294&radius=5
    """
    try:
        csv_file_path = "./hospital_directory.csv"

        # Get the JSON string from the find_hospitals_near_coordinates function
        result_json = find_hospitals_near_coordinates(
            csv_file_path=csv_file_path,
            target_lat=lat,
            target_lon=lon,
            radius=radius
        )

        # Parse the JSON string to a Python dictionary
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            # If JSON decoding fails, there might be invalid floats in the string
            # Use a more tolerant approach by loading the JSON with a custom decoder
            result = json.loads(result_json, parse_constant=lambda x: None)

        # Sanitize the result to ensure all values are JSON serializable
        result = sanitize_json_data(result)

        # Add a status field for consistency
        result["status"] = "success"
        return result

    except Exception as e:
        # Return a proper error response instead of raising an exception
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }


@app.get('/')
def root():
    """Root endpoint that provides API information"""
    return {
        "status": "success",
        "message": "Healthcare API is running",
        "endpoints": {
            "/med": "Lookup medicine details by name (e.g., /med?query=Paracetamol)",
            "/hospitals": "Find hospitals near specified coordinates (e.g., /hospitals?lat=19.867141&lon=75.335294&radius=5)"
        }
    }
