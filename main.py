import pandas as pd
import json
import math
from fuzzywuzzy import process
from fastapi import FastAPI, Query, HTTPException
# from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from chatbot import get_med_details
from hosp_sort import find_hospitals_near_coordinates, get_nearby_hospitals

app = FastAPI()
# handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get('/med')
async def get_medicine_details(
        query: str = Query(..., description="Medicine name to look up (e.g., Paracetamol)")
):
    """
    Lookup medicine details by name.
    Returns medicine name, composition, and AI analysis.

    Example: /med?query=Paracetamol
    """
    try:
        # Call the get_med_details function with the query parameter
        result = get_med_details(query)

        # If no result was found
        if result is None:
            return {
                "status": "error",
                "message": "Medicine details not found"
            }

        # Return the medicine details with a success status
        return {
            "status": "success",
            "data": {
                "medicine": result["med"],
                "composition": result["composition"],
                "analysis": result["analysis"]
            }
        }

    except Exception as e:
        # Return a proper error response if anything goes wrong
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
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
        csv_file_path = "./hospitals.csv"

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
