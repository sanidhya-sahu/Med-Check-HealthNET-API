import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from groq import Groq

def load_medicine_data(file_path):
    """Load medicine data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def get_medicine_match(user_entry, medicine_names, threshold=70):
    """Find best matching medicine name"""
    user_entry_lower = user_entry.lower()

    # Step 1: Try exact match
    for med in medicine_names:
        if med.lower() == user_entry_lower:
            return med

    # Step 2: Try prefix match
    for med in medicine_names:
        if med.lower().startswith(user_entry_lower):
            return med

    # Step 3: Fuzzy match as fallback
    best_match, score = process.extractOne(user_entry, medicine_names, scorer=fuzz.partial_ratio)
    if score >= threshold:
        return best_match
    return None

def get_composition(df, medicine_name):
    """Get composition for matched medicine"""
    matched_row = df[df["name"] == medicine_name]
    if not matched_row.empty:
        return matched_row["short_composition1"].values[0]
    return None

def get_ai_analysis(medicine_name, composition, api_key):
    """Get AI analysis of the medicine"""
    client = Groq(api_key=api_key)

    prompt = f"""You are a helpful and knowledgeable medical assistant.
    Given the following medicine information, explain:
    1. What the medicine is typically used for.
    2. What each ingredient in the composition does.
    3. The drug class or type (e.g., antibiotic, painkiller, etc).
    4. Any common side effects or warnings (if applicable).

    Medicine Name: {medicine_name}
    Composition: {composition}

    Keep the explanation simple, clear, and suitable for a general audience."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error getting AI analysis: {e}"

def main():
    # Configuration
    FILE_PATH = "./A_Z_medicines_dataset_of_India.csv"
    API_KEY = "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"

    # Load data
    df = load_medicine_data(FILE_PATH)
    if df is None:
        return

    # Prepare data
    medicine_names = df["name"].dropna().tolist()

    # Get user input
    user_entry = input("Enter your medicine name: ")

    # Find match
    best_match = get_medicine_match(user_entry, medicine_names)
    if best_match is None:
        print("Match not found")
        return

    print(f"Found match: {best_match}")

    # Get composition
    composition = get_composition(df, best_match)
    if composition is None:
        print("Composition not found")
        return

    print(f"Composition: {composition}")

    # Get AI analysis
    analysis = get_ai_analysis(best_match, composition, API_KEY)
    print("\nAI Analysis:")
    print(analysis)

def get_med_details(name):
    FILE_PATH = "./A_Z_medicines_dataset_of_India.csv"
    API_KEY = "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"

    # Load data
    df = load_medicine_data(FILE_PATH)
    if df is None:
        return

    # Prepare data
    medicine_names = df["name"].dropna().tolist()

    bestMatch = ""
    # Find match
    best_match = get_medicine_match(name, medicine_names)
    if best_match is None:
        bestMatch = "No Best Match Found"
        return
    bestMatch = best_match
    # Get composition
    composition = get_composition(df, best_match)
    compos_result = ""
    if composition is None:
        compos_result = "Composition not found"
        return

    compos_result = composition


    # Get AI analysis
    analysis = get_ai_analysis(best_match, composition, API_KEY)

    return {
        "med": bestMatch,
        "composition": compos_result,
        "analysis": analysis
    }



if __name__ == "__main__":
    main()
