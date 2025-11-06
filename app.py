import streamlit as st
import requests
import json
import time

# --- Gemini API Setup (MUST be available globally for Streamlit) ---
# NOTE: The apiKey is left blank. Streamlit Cloud automatically handles
# providing the API key at runtime if the project is run inside Canvas.
# If running locally, replace "" with your actual API Key.
API_KEY = ""
MODEL_NAME = "gemini-2.5-flash-preview-05-20" 
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

st.set_page_config(layout="wide", page_title="Structured Meal Planner")

# --- Structured Output Schema (The most important part!) ---
# Define the exact JSON structure we expect the model to return.
# This forces the model to deliver machine-readable data.
MEAL_PLAN_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "day": {"type": "STRING"},
            "breakfast": {
                "type": "OBJECT",
                "properties": {
                    "mealName": {"type": "STRING"},
                    "ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "calories": {"type": "INTEGER"}
                },
                "propertyOrdering": ["mealName", "ingredients", "calories"]
            },
            "lunch": {
                "type": "OBJECT",
                "properties": {
                    "mealName": {"type": "STRING"},
                    "ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "calories": {"type": "INTEGER"}
                },
                "propertyOrdering": ["mealName", "ingredients", "calories"]
            },
            "dinner": {
                "type": "OBJECT",
                "properties": {
                    "mealName": {"type": "STRING"},
                    "ingredients": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "calories": {"type": "INTEGER"}
                },
                "propertyOrdering": ["mealName", "ingredients", "calories"]
            }
        },
        "propertyOrdering": ["day", "breakfast", "lunch", "dinner"]
    }
}

# --- System Instruction ---
SYSTEM_PROMPT = """You are an expert nutritionist and meal planner. Your sole task is to generate a comprehensive 7-day meal plan based on the user's specific dietary requirements.

RULES:
1. The response MUST be a JSON array that strictly adheres to the provided JSON schema.
2. The total calories for the 7-day plan must meet the user's daily target as closely as possible, spread across the three meals.
3. Every ingredient must be simple and easily available.
4. DO NOT include any text or markdown outside of the JSON structure.
"""

def generate_meal_plan(dietary_reqs):
    """Calls the Gemini API to generate a structured meal plan."""
    
    user_query = f"Generate a 7-day meal plan for a diet of: {dietary_reqs}"
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": MEAL_PLAN_SCHEMA
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    # Simple retry logic with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise exception for bad status codes
            
            result = response.json()
            
            # Extract and parse the JSON response text
            json_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
            
            if json_text:
                return json.loads(json_text)
            else:
                st.error("Model did not return valid content. Retrying...")
                time.sleep(2 ** attempt)
                continue

        except requests.exceptions.HTTPError as e:
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                st.warning(f"API Rate Limit or Server Error ({response.status_code}). Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
            else:
                st.error(f"HTTP Error: {e} - Could not connect to API.")
                return None
        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Could not reach the API.")
            return None
        except json.JSONDecodeError:
            st.error("Error: Model returned non-JSON data. Please try adjusting your request.")
            st.code(json_text) 
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return None
    return None

def display_meal_plan(plan_data):
    """Displays the structured meal plan data in a clean Streamlit table/dataframe."""
    
    # Flatten the JSON data into a simple DataFrame-like structure for display
    display_data = []
    
    for day_entry in plan_data:
        day = day_entry.get('day', 'N/A')
        
        display_data.append({
            'Day': day,
            'Meal': 'Breakfast',
            'Name': day_entry.get('breakfast', {}).get('mealName', 'N/A'),
            'Ingredients': ', '.join(day_entry.get('breakfast', {}).get('ingredients', [])),
            'Calories': day_entry.get('breakfast', {}).get('calories', 'N/A')
        })
        display_data.append({
            'Day': day,
            'Meal': 'Lunch',
            'Name': day_entry.get('lunch', {}).get('mealName', 'N/A'),
            'Ingredients': ', '.join(day_entry.get('lunch', {}).get('ingredients', [])),
            'Calories': day_entry.get('lunch', {}).get('calories', 'N/A')
        })
        display_data.append({
            'Day': day,
            'Meal': 'Dinner',
            'Name': day_entry.get('dinner', {}).get('mealName', 'N/A'),
            'Ingredients': ', '.join(day_entry.get('dinner', {}).get('ingredients', [])),
            'Calories': day_entry.get('dinner', {}).get('calories', 'N/A')
        })

    st.subheader("✅ Generated 7-Day Structured Meal Plan")
    st.dataframe(
        display_data, 
        use_container_width=True,
        hide_index=True,
        column_order=('Day', 'Meal', 'Name', 'Calories', 'Ingredients')
    )
    
# --- Streamlit UI ---
st.title("🍽️ Structured AI Meal Planner")
st.markdown("Use this tool to generate a 7-day meal plan customized to your diet, caloric goals, and preferences. This application demonstrates **structured output (JSON) enforcement** on the Gemini model.")

with st.sidebar:
    st.header("Plan Requirements")
    diet = st.text_input("Diet Type (e.g., Keto, Vegan, Gluten-Free)", "Balanced")
    calories = st.number_input("Daily Calorie Target", min_value=1000, max_value=4000, value=2000, step=100)
    preferences = st.text_area("Specific Preferences/Dislikes (e.g., Prefers chicken and fish, dislikes onions)", "Prefers quick preparation time. Focus on high protein.")
    
    full_reqs = f"Diet: {diet}. Daily Calorie Target: {calories}. Preferences: {preferences}."
    
    if st.button("Generate Meal Plan", type="primary"):
        with st.spinner("Generating and Structuring Plan..."):
            plan = generate_meal_plan(full_reqs)
            if plan:
                st.session_state.meal_plan = plan
                
if 'meal_plan' in st.session_state:
    display_meal_plan(st.session_state.meal_plan)
else:
    st.info("Enter your dietary requirements in the sidebar and click 'Generate Meal Plan' to begin.")
