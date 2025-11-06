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
