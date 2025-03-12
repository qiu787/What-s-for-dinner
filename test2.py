import streamlit as st
from openai import OpenAI
import json
import random

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #FFF5E6;
}
[data-testid="stHeader"] {
    background-color: #FFE4C4;
}
div.stButton > button:first-child {
    background-color: #FFA500;
    color: white;
    border-radius: 8px;
    transition: all 0.3s;
}
div.stButton > button:hover {
    background-color: #FF8C00 !important;
}
.recipe-card {
    background: white !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    padding: 1rem;
    margin: 1rem 0;
    border-left: 4px solid #FFA500;
}
.pref-card {
    background: rgba(255,255,255,0.9) !important;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=st.secrets["dinner_key"])

if "page" not in st.session_state:
    st.session_state.page = "home"  
if "food_inventory" not in st.session_state:
    st.session_state.food_inventory = {}  
if "preferences" not in st.session_state or not isinstance(st.session_state.preferences, dict):
    st.session_state.preferences = {
        "text": "",
        "tools": [],
        "cooking_time": "Any"
    }
   
if "recipes_list" not in st.session_state:
    st.session_state.recipes_list = []



top_col1, top_col2, top_col3 = st.columns([4, 12, 3])

with top_col1:
    st.write("")  

with top_col2:
    st.title("☕ What's for dinner?")

with top_col3:
    if st.button("⚙️ Preferences", key="edit_pref"):
        st.session_state.page = "preferences"

col1, col2 = st.columns([6, 1])  
with col1:
    if st.button("🧊 Fridge", key="to_warehouse"):
        st.session_state.page = "warehouse"
with col2:
    if st.button("📜 Recipes", key="to_recipes"):
        st.session_state.page = "recipes"

def parse_recipes_from_json(json_str):
    recipes = []
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "recipes" in data:
            recipes = data["recipes"]
    except json.JSONDecodeError as e:
        st.error(f"JSON Decode Error: {e}")
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
    return recipes

def generate_recipes_list(ingredients, preferences, n=5, random_mode=False):
    prompt = f"""
You are a professional chef, and the user has provided these ingredients: {", ".join(ingredients)}.
Preferences:
- Taste: {preferences['text'] if preferences['text'] else "No special preferences"}
- Tools: {', '.join(preferences['tools']) if preferences['tools'] else 'Any'}
- Time: {preferences['cooking_time'] if preferences['cooking_time'] != 'Any' else 'Flexible'}

Please list {n} delicious dishes.{" Add creative and unexpected combinations!" if random_mode else ""}
Return in JSON format:
{{
  "recipes": [
    {{"name": "Recipe1", "description": "Short description"}},
    {{"name": "Recipe2", "description": "Short description"}}
  ]
}}
"""

    try:
        # Remove the 'response_format' parameter
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Professional chef returning recipes in JSON"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.8 if random_mode else 0.6
        )
        # Return the content of the response
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"


def generate_recipe_instructions(recipe_name, ingredients, preferences):
    prompt = f"""
Create detailed instructions for: {recipe_name}
Ingredients: {", ".join(ingredients)}
Preferences: 
- Taste: {preferences['text']}
- Tools: {', '.join(preferences['tools'])}
- Time: {preferences['cooking_time']}

Include:
1. Ingredients preparation
2. Step-by-step instructions
3. Cooking tips
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

def show_warehouse_page():
    st.subheader("🧊 My Fridge")
    
    total_items = sum(st.session_state.food_inventory.values())
    st.progress(min(total_items/50, 1), text=f"Capacity: {total_items}/50")

    if st.session_state.food_inventory:
        for food, qty in st.session_state.food_inventory.items():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                emoji = random.choice(["🥑","🥦","🥩","🍳","🧀","🍅","🧄"])
                st.markdown(f"{emoji} **{food}**")
            with col2:
                st.markdown(f"`{qty}pcs`")
            with col3:
                if st.button(f"➕", key=f"plus_{food}"):
                    st.session_state.food_inventory[food] += 1
                    st.rerun()
            with col4:
                if st.button(f"➖", key=f"minus_{food}"):
                    st.session_state.food_inventory[food] -= 1
                    if st.session_state.food_inventory[food] <= 0:
                        del st.session_state.food_inventory[food]
                    st.rerun()
    else:
        st.markdown("> 🧺 The fridge is empty, add ingredients now!")

    with st.expander("✨ Add New Ingredient", expanded=True):
        new_food = st.text_input("Ingredient", placeholder="e.g. Beef")
        new_qty = st.number_input("Quantity", min_value=1, value=1)
        if st.button("✨ Add to fridge"):
            if new_food.strip():
                st.session_state.food_inventory[new_food.strip()] = new_qty
                st.success(f"Added {new_food} x{new_qty}")
                st.rerun()

def show_preferences_page():
    st.subheader("⚙️ Taste Preferences") 
    
    st.markdown("**Quick Select:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌶️ Spicy"):
            st.session_state.preferences['text'] += " Likes spicy food"
    with col2:
        if st.button("🍭 Sweet"):
            st.session_state.preferences['text'] += " Likes sweets"
    with col3:
        if st.button("🍃 Healthy"):
            st.session_state.preferences['text'] += " Low oil and salt"

    st.markdown("---")
    st.markdown("**Cooking Settings:**")
    
    tools = st.multiselect(
        "Available Tools:",
        ["Stovetop", "Oven", "Microwave", "Air Fryer", "Blender"],
        default=st.session_state.preferences['tools']
    )
    
  
    cook_time = st.selectbox(
        "Cooking Time:",
        ["Any", "15 mins", "30 mins", "1 hour", "1.5 hours+"],
        index=["Any", "15 mins", "30 mins", "1 hour", "1.5 hours+"].index(
            st.session_state.preferences['cooking_time']
        )
    )

    pref = st.text_area(
        "Additional Preferences:",
        value=st.session_state.preferences['text'],
        height=150,
        placeholder="e.g.\n- Dislike cilantro\n- Love cheese\n- Allergic to seafood"
    )

    if st.button("💾 Save Preferences", type="primary"):
        st.session_state.preferences = {
            "text": pref,
            "tools": tools,
            "cooking_time": cook_time
        }
        st.success("Preferences saved!")
        st.session_state.page = "home"
        st.rerun()

def show_recipes_page():
    if "recipes_list" not in st.session_state:
        st.session_state.recipes_list = []

    st.subheader("📜 Recipe Generation")
    

    pref_info = f"""
    🧂 Taste: {st.session_state.preferences['text'] or 'None'}
    ⚒️ Tools: {', '.join(st.session_state.preferences['tools']) or 'Any'}
    ⏳ Time: {st.session_state.preferences['cooking_time']}
    """
    st.markdown(f"```\n{pref_info}\n```")

    selected_ingredients = []
    cols = st.columns(3)
    for idx, food in enumerate(st.session_state.food_inventory.keys()):
        with cols[idx % 3]:
            if st.checkbox(f"{food}", key=f"select_{food}"):
                selected_ingredients.append(food)
    
    col_gen, col_random = st.columns(2)
    with col_gen:
        gen_clicked = st.button("✨ Generate Recipes", type="primary")
    with col_random:
        random_clicked = st.button("🎲 Random Combos", type="primary")

    if gen_clicked or random_clicked:
        if not selected_ingredients:
            st.warning("⚠️ Please select at least one ingredient!")
        else:
            with st.spinner("🧑🍳 Generating recipes..."):
                raw_json = generate_recipes_list(
                    selected_ingredients, 
                    st.session_state.preferences,
                    random_mode=random_clicked
                )
                

                if not raw_json.startswith("ERROR"):
                    
                    new_recipes = parse_recipes_from_json(raw_json)

                    if new_recipes:
                        st.session_state.recipes_list = new_recipes
                    else:
                        st.error("Failed to parse recipes")

    st.write("### 🍽️ Generated Recipes")
    if st.session_state.recipes_list:
        for idx, r in enumerate(st.session_state.recipes_list):
            with st.container():
                st.markdown(f"""
                <div class="recipe-card">
                    <h3>{r.get('name', 'Recipe')}</h3>
                    <p>{r.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
               
                with st.expander("📖 Show Instructions", expanded=False):
                    instructions = generate_recipe_instructions(
                        r['name'], 
                        selected_ingredients, 
                        st.session_state.preferences
                    )
                    st.markdown(f"""
                    <div class="pref-card">
                        {instructions}
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.write("No recipes generated yet")




   
if st.session_state.page == "home":
    st.write("Welcome! Use the navigation buttons to get started.")
elif st.session_state.page == "warehouse":
    show_warehouse_page()
elif st.session_state.page == "preferences":
    show_preferences_page()
elif st.session_state.page == "recipes":
    show_recipes_page()