import pandas as pd
import json
import math
from fuzzywuzzy import process
from fastapi import FastAPI, Query, HTTPException
# from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from chatbot import get_med_details
from hosp_sort import get_nearest_hospitals_info

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
    try:
        result = get_med_details(query)
        if result is None:
            return {
                "status": "error",
                "message": "Medicine details not found"
            }

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
async def get_hospitals(
        lat: float = Query(..., description="Latitude of the search location"),
        lon: float = Query(..., description="Longitude of the search location"),
        radius: Optional[float] = Query(25.0, description="Search radius in kilometers")
):
    try:
        result = get_nearest_hospitals_info(lat, lon, radius)
        if not result or len(result) == 0:
            return {
                "status": "error",
                "message": f"No hospitals found within {radius}km radius"
            }

        # Sanitize the result to ensure all values are JSON serializable
        clean_result = sanitize_json_data(result)

        return {
            "status": "success",
            "data": clean_result
        }

    except Exception as e:
        # Return a proper error response if anything goes wrong
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }


@app.get('/nearest_hospitals')
async def get_nearest_hospitals(
        lat: float = Query(..., description="Latitude of the search location"),
        lon: float = Query(..., description="Longitude of the search location"),
        limit: Optional[int] = Query(5, description="Maximum number of hospitals to return")
):
    try:
        result = get_nearest_hospitals_info(lat, lon)
        if not result or len(result) == 0:
            return {
                "status": "error",
                "message": "No hospitals found in the area"
            }

        # Format the response based on your sample data
        hospitals = []
        for hospital in result[:limit]:
            hospitals.append({
                "Hospital Name": hospital.get("Hospital Name", "Unknown"),
                "Location": hospital.get("Location", "Address not available"),
                "Mobile Number": hospital.get("Mobile Number", "Not available"),
                "Distance (km)": hospital.get("Distance (km)", None)
            })

        return {
            "status": "success",
            "data": hospitals
        }

    except Exception as e:
        # Return a proper error response if anything goes wrong
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
            "/hospitals": "Find hospitals near specified coordinates with optional radius (e.g., /hospitals?lat=19.867141&lon=75.335294&radius=5)",
            "/nearest_hospitals": "Find nearest hospitals to specified coordinates (e.g., /nearest_hospitals?lat=19.867141&lon=75.335294&limit=5)"
        }
    }
