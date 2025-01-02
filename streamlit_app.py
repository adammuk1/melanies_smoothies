# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col

# Configure logging to capture detailed error information
logging.basicConfig(
    filename='app.log',  # Log file path
    filemode='a',         # Append mode
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR   # Log only errors and above
)

# Establish Snowflake connection using Streamlit's connection API
cnx = st.connection("snowflake")

if cnx is not None:
    try:
        session = cnx.session()
        
        # Fetch data from Snowflake using Snowpark
        my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
        pd_df = my_dataframe.to_pandas()
        
        # Display available fruits
        st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
        st.write("""Choose the fruits you want in your custom Smoothie!""")
        
        # Input for the name on the order
        name_on_order = st.text_input("Name on Smoothie: ")
        if name_on_order:
            st.write("The name on your Smoothie will be:", name_on_order)
        
        # Multiselect for ingredients
        ingredients_list = st.multiselect(
            'Choose up to 5 ingredients:',
            options=pd_df["FRUIT_NAME"].tolist(),
            max_selections=5
        )
        
        if ingredients_list:
            ingredients_string = ' '.join(ingredients_list)
            
            for fruit_chosen in ingredients_list:
                # Get the corresponding 'SEARCH_ON' value
                search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
                st.write(f'The search value for {fruit_chosen} is {search_on}.')
                
                st.subheader(f"{fruit_chosen} Nutrition Information")
                smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                if smoothiefroot_response.status_code == 200:
                    st.json(smoothiefroot_response.json())
                else:
                    st.warning(f"Failed to fetch data from Smoothiefroot API for {search_on}. Status code: {smoothiefroot_response.status_code}")
            
            # Prepare the SQL insert statement using parameterized queries
            my_insert_stmt = """
                INSERT INTO smoothies.public.orders (ingredients, name_on_order)
                VALUES (%s, %s)
            """
            
            time_to_insert = st.button('Submit Order')
            
            if time_to_insert:
                try:
                    session.sql(my_insert_stmt).bind([ingredients_string, name_on_order]).collect()
                    st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
                except Exception as e:
                    logging.error("Error inserting order into Snowflake", exc_info=True)
                    st.error("An error occurred while placing your order. Please check the logs for more details.")
    except Exception as e:
        logging.error("An unexpected error occurred.", exc_info=True)
        st.error("An unexpected error occurred. Please check the logs for more details.")
else:
    st.error("Failed to establish a connection to Snowflake.")
