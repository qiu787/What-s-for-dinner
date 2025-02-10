import streamlit as st
import openai
import json
import random

headers = {
        "authorization":st.secrets["dinner_key"]
}


if "page" not in st.session_state:
    st.session_state.page = "home"  
if "food_inventory" not in st.session_state:
    st.session_state.food_inventory = {}  
if "preferences" not in st.session_state:
    st.session_state.preferences = ""      
if "recipes_list" not in st.session_state:
    st.session_state.recipes_list = []     


top_col1, top_col2, top_col3 = st.columns([4, 12, 3])

with top_col1:
    st.write("")  

with top_col2:
    st.title("What's for dinner?")

with top_col3:

    if st.button("Preference", key="edit_pref"):
        st.session_state.page = "preferences"


col1, col2 = st.columns([6, 1])  
with col1:
    if st.button("Fridge", key="to_warehouse"):
        st.session_state.page = "warehouse"

with col2:
    if st.button("Recipes", key="to_recipes"):
        st.session_state.page = "recipes"




def parse_recipes_from_json(json_str):
    """
    解析AI返回的JSON格式字符串，获取食谱列表
    期望格式：
    {
      "recipes": [
        {
          "name": "Recipe Name",
          "description": "Short Description "
        },
        ...
      ]
    }
    """
    recipes = []
    try:
        data = json.loads(json_str)
        if "recipes" in data:
            recipes = data["recipes"]
    except json.JSONDecodeError:
        pass
    return recipes



def generate_recipes_list(ingredients, preferences, n=5):
    """
    向 OpenAI 发送请求，让其基于食材和口味偏好
    返回一个JSON结构，包含 n 个菜名 + 简要描述
    """
    prompt = f"""
You are a professional chef, and the user has provided these ingredients: {", ".join(ingredients)}.
The user's taste preferences: {preferences if preferences else "No special preferences"}.
Please list {n} delicious dishes that can be made with the above ingredients.
Only return data in JSON format, like the example below:
{{
  "recipes": [
    {{"name": "Recipe1", "description": "Short description"}},
    {{"name": "Recipe2", "description": "Short description"}}
  ]
}}
Do not output any extra text.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional western food chef who needs to return a list of recipes in JSON format based on the user's preferences and ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


def generate_recipe_instructions(recipe_name, ingredients, preferences):
    """
    对具体的菜名，再次询问AI，生成详细的制作步骤
    """
    prompt = f"""
You are a professional chef. The user has these ingredients: {", ".join(ingredients)}.
The user wants to make: {recipe_name}.
The user's taste preferences: {preferences if preferences else "No special preferences"}.
Please list the detailed steps and techniques to make this dish.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional western food chef who needs to give detailed recipe instructions based on user preferences and ingredients。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


def show_home_page():
    st.write("This is the homepage. You can click the buttons above to go to Warehouse, Generate Recipes, or Edit Preferences.")

def show_warehouse_page():
    st.subheader("🍖 My little fridge")
    
    total_items = sum(st.session_state.food_inventory.values())
    st.progress(min(total_items/50, 1), text=f"capacity: {total_items}/50")

    if st.session_state.food_inventory:
        for food, qty in st.session_state.food_inventory.items():

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                food_emoji = {
                    "egg": "🥚", "beef": "🥩", "milk": "🥛", 
                    "tomato": "🍅", "rice": "🍚"
                }.get(food, "🌱")
                st.markdown(f"{food_emoji} **{food}**")

            with col2:
                st.markdown(f"`{qty}pcs`")
            
            with col3:
                if st.button(f"➕", key=f"plus_{food}", 
                           help="Increase quantity"):
                    st.session_state.food_inventory[food] += 1
                    st.rerun()
            
            with col4:
                if st.button(f"➖", key=f"minus_{food}",
                           help="Decrease quantity"):
                    st.session_state.food_inventory[food] -= 1
                    if st.session_state.food_inventory[food] <= 0:
                        del st.session_state.food_inventory[food]
                    st.rerun()
        
        st.markdown("---")
    else:
        st.markdown("> 🧺 The fridge is empty, add ingredients now!")

with st.expander("✨ Add New Ingredient", expanded=True):
    new_food = st.text_input("Ingredient", key="new_food",
                           placeholder="e.g. Beef")
    new_qty = st.number_input("Quantity", min_value=1, value=1, format="%d")  
    
    if st.button("✨ Add to fridge！", type="primary"): 
        if new_food.strip():
            # Ensure food_inventory exists in session state
            if "food_inventory" not in st.session_state:
                st.session_state.food_inventory = {}

            # Update the inventory
            st.session_state.food_inventory[new_food.strip()] = st.session_state.food_inventory.get(new_food.strip(), 0) + new_qty
            
            # Display a success message
            st.success(f"🎉 Successfully added{new_food} x {new_qty}")
            
            # Rerun the app to reflect changes (if needed)
            st.rerun()



def show_preferences_page():
    st.subheader("👅 Taste Preferences")

    st.markdown("**Quick Select：**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌶️ Spicy Food Lover", help="Loves spicy food", use_container_width=True):
            st.session_state.preferences += " Likes spicy food"
    with col2:
        if st.button("🍭 Dessert Lover", help="Loves sweets", use_container_width=True):
            st.session_state.preferences += " Likes sweets"
    with col3:
        if st.button("🍃 Healthy Light Meals", help="Low oil and salt", use_container_width=True):
            st.session_state.preferences += " Low oil and salt"

    pref = st.text_area(
        "Write your personal taste preferences：",
        value=st.session_state.preferences,
        height=150,
        placeholder="e.g. \n- Dislike cilantro\n- Love cheese pull effect\n- Allergic to seafood"
    )

    if st.button("🔒 save Preferences", type="primary"):
        st.session_state.preferences = pref
        st.success("✅ Taste preferences saved！")
        st.session_state.page = "home"
        st.rerun() 
def show_recipes_page():
    st.markdown("""
        <style>
        /* 覆盖 Streamlit 默认宽度 */
        div.stMarkdown > div > div > div > div > div {
            max-width: 100% !important;
            width: 90% !important;
        }
        /* 调整文本样式 */
        .custom-recipe-text {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🔮 Magic Recipe Generation")
    
    pref_emoji = "🌶️" if "spicy" in st.session_state.preferences else "🍭"
    st.markdown(f"Current taste preferences：{pref_emoji} `{st.session_state.preferences or 'None'}`")

    selected_ingredients = []
    cols = st.columns(3)
    for idx, food in enumerate(st.session_state.food_inventory.keys()):
        with cols[idx % 3]:
            if st.checkbox(f"{food}", key=f"select_{food}"):
                selected_ingredients.append(food)
    
    if st.button("✨ Generate Recipe", type="primary", use_container_width=True):
        if not selected_ingredients:
            st.warning("⚠️ Please select at least one ingredient！")
        else:
            with st.spinner("🧙‍♂️ AI is generating your recipe..."):
                raw_json = generate_recipes_list(selected_ingredients, st.session_state.preferences, 5)
                if raw_json.startswith("ERROR:"):
                    st.error(raw_json)
                else:
                    new_recipes = parse_recipes_from_json(raw_json)
                    if new_recipes:
                        st.session_state.recipes_list.extend(new_recipes)
                        st.balloons()
                    else:
                        st.error("AI returned an unparseable format. Please try again later.")

    st.write("### Generated Recipes")
    if st.session_state.recipes_list:
        for idx, r in enumerate(st.session_state.recipes_list):
            recipe_name = r.get("name", f"Untitled Recipe {idx+1}")
            desc = r.get("description", "")

            with st.expander(f"**{idx+1}. {recipe_name}**  \n*{desc}*", expanded=False):
                instructions = generate_recipe_instructions(recipe_name, selected_ingredients, st.session_state.preferences)
                st.markdown(
                    f"""
                    <div class="custom-recipe-text">
                        {instructions}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.write("No recipes generated yet")

if st.session_state.page == "home":
    show_home_page()
elif st.session_state.page == "warehouse":
    show_warehouse_page()
elif st.session_state.page == "preferences":
    show_preferences_page()
elif st.session_state.page == "recipes":
    show_recipes_page()
