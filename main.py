import pandas as pd
from fuzzywuzzy import process
from fastapi import FastAPI
# from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware


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

