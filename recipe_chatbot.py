from flask import Flask, jsonify, render_template, request, session
import aiml
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session

# AIML Kernel
kernel = aiml.Kernel()
kernel.learn("std-startup.xml")
kernel.respond("LOAD AIML B")

# API Keys
SPOONACULAR_API_KEY = 'bdf93e0f01ea4e8e88713289d1c79abf'
WEATHER_API_KEY = '8fd2f09c00a34ad4981234752250504'

BASE_URL_SPOONACULAR = 'https://api.spoonacular.com/recipes'
BASE_URL_WEATHER = 'http://api.weatherapi.com/v1/current.json'

def get_weather(city):
    try:
        response = requests.get(BASE_URL_WEATHER, params={'key': WEATHER_API_KEY, 'q': city})
        data = response.json()
        if data.get('error'):
            return None, f"Error: {data['error']['message']}"
        else:
            temp = data['current']['temp_c']
            weather = data['current']['condition']['text']
            location = data['location']
            return temp, weather, location['name'], location['region'], location['country']
    except Exception as e:
        return None, f"An error occurred: {e}"

def suggest_food_based_on_weather(temp):
    if temp < 15:
        return "It's quite cold! How about some hot soup or spicy food to warm you up?"
    elif 15 <= temp < 25:
        return "The weather is mild. A nice pasta or sandwich might be just right."
    elif 25 <= temp < 35:
        return "It's getting warm! Maybe a fresh salad or cold beverage would be refreshing."
    else:
        return "It's really hot outside! A cold dessert or something light would be perfect."

def get_recipe(query):
    try:
        response = requests.get(f"{BASE_URL_SPOONACULAR}/search", params={
            'query': query, 'apiKey': SPOONACULAR_API_KEY, 'number': 1
        })
        data = response.json()
        if data['results']:
            recipe = data['results'][0]
            recipe_id = recipe['id']
            recipe_info = get_recipe_details(recipe_id)
            return f"Here's a recipe for {recipe['title']}. More info: {recipe['sourceUrl']}<br><br>Ingredients:<br>{recipe_info}"
        else:
            return "Sorry, I couldn't find any recipes for that query."
    except Exception as e:
        return f"An error occurred: {e}"

def get_recipe_details(recipe_id):
    try:
        response = requests.get(f"{BASE_URL_SPOONACULAR}/{recipe_id}/information", params={'apiKey': SPOONACULAR_API_KEY})
        data = response.json()
        ingredients = data.get('extendedIngredients', [])
        return "<br>".join([f"{i['amount']} {i['unit']} {i['name']}" for i in ingredients])
    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["message"].strip().lower()
        response = ""

        if session.get("awaiting_location"):
            city = user_input
            session["awaiting_location"] = False
            result = get_weather(city)
            if result[0] is not None:
                temp, weather, city_name, region, country = result
                suggestion = suggest_food_based_on_weather(temp)
                response = f"According to {city_name}, {region}, {country}, where it's {temp}°C ({weather}), I suggest: {suggestion}"
            else:
                response = result[1]

        elif user_input == "what should i eat":
            session["awaiting_location"] = True
            response = "Hmm! Lemme see... Please type your city name."

        elif 'recipe' in user_input or 'how to cook' in user_input:
            query = user_input.replace('recipe', '').replace('how to cook', '').strip()
            response = get_recipe(query)

        else:
            response = kernel.respond(user_input)

        return jsonify({"reply": response})

    return render_template("index.html", response="")

if __name__ == "__main__":
    app.run(debug=True)
