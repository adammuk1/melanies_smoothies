# Import python packages
import streamlit as st 
from snowflake.snowpark.functions import col
import time  # Ensure you import time if you use it
import requests

# Initialize Snowflake session
cnx = st.connection("snowflake")
session = cnx.session()

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
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'),col('SEARCH_ON'))
    # st.dataframe(my_dataframe, use_container_width=True)
    # st.stop()

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df)
st.stop()




# Multiselect for ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    key='dataframe',
    max_selections=5
)

# Enforce a maximum of 5 selections
if len(ingredients_list) > 5:
    st.warning("You can select up to 5 ingredients only. Only the first 5 will be considered.")
    ingredients_list = ingredients_list[:5]

if ingredients_list:
    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write('The search value for ', fruit_chosen,' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + fruit_chosen)
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)

              
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
