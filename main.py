import pandas as pd
from fuzzywuzzy import process
from fastapi import FastAPI, Query
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


@app.get('/hospitals')
def get_nearby_hospitals_route(
        lat: float = Query(..., description="Latitude of the search location"),
        lon: float = Query(..., description="Longitude of the search location"),
        radius: Optional[float] = Query(10.0, description="Search radius in kilometers")
):
    """
    Find hospitals near the specified coordinates within the given radius.
    Returns results as JSON with hospital details and distances.
    """
    try:
        csv_file_path = "./hospital_directory.csv"

        # We're using find_hospitals_near_coordinates directly since it returns a JSON string
        # which is what we want for the API response
        result_json = find_hospitals_near_coordinates(
            csv_file_path=csv_file_path,
            target_lat=lat,
            target_lon=lon,
            radius=radius
        )

        # Since find_hospitals_near_coordinates returns a JSON string,
        # we need to convert it back to a Python object for FastAPI to handle
        import json
        return json.loads(result_json)

    except Exception as e:
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
            "/med": "Lookup medicine details by name",
            "/hospitals": "Find hospitals near specified coordinates"
        }
    }