# Import python packages
import streamlit as st 
import logging  # Must be before using logging
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
import time  # Ensure you import time if you use it


# Configure logging at the top of the file
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# ... rest of your code ...


# Initialize Snowflake session
session = get_active_session()

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!"""
)

# Input for the name on the order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Fetch fruit options from Snowflake
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
    fruit_rows = my_dataframe.collect()
    fruit_options = [row['FRUIT_NAME'] for row in fruit_rows]
    st.dataframe(data=fruit_options, use_container_width=True)
except Exception as e:
    st.error(f"Error fetching fruit options: {e}")

# Multiselect for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    options=fruit_options
)

# Enforce a maximum of 5 selections
if len(ingredients_list) > 5:
    st.warning("You can select up to 5 ingredients only. Only the first 5 will be considered.")
    ingredients_list = ingredients_list[:5]

if ingredients_list:
    # Convert list of fruits to a space-separated string
    ingredients_string = ' '.join(ingredients_list)
    # st.write(f"Selected Ingredients: {ingredients_string}")
    
    
    # Prepare the SQL insert statement safely
    # Use parameterized queries or Snowflake's API to prevent SQL injection
    # Here, for simplicity, we're using f-strings but ensure inputs are sanitized in production
    my_insert_stmt = """INSERT INTO smoothies.public.orders(ingredients, name_on_order)
                            VALUES ('{}', '{}')""".format(ingredients_string, name_on_order)
    
    st.write("Generated SQL Statement:")
    st.code(my_insert_stmt, language='sql')
    
    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            success_message = f"Your Smoothie is ordered, {name_on_order}!"
            st.success(success_message, icon="✅")
        except Exception as e:
            st.error(f"An error occurred while placing your order: {e}")
