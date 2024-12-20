# Import python packages
import streamlit as st
import snowflake.connector
import time  # Ensure you import time if you use it
import logging
import requests

# Configure logging to capture detailed error information
logging.basicConfig(
    filename='app.log',  # Log file path
    filemode='a',         # Append mode
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR   # Log only errors and above
)

def get_snowflake_connection():
    """
    Establishes a connection to Snowflake using credentials from secrets.toml.

    Returns:
        connection: Snowflake connection object if successful, None otherwise.
    """
    try:
        # Access connection details from Streamlit's secrets
        snowflake_config = st.secrets["connections"]["snowflake"]
        
        # Establish connection using Snowflake Connector
        connection = snowflake.connector.connect(
            account=snowflake_config["account"],
            user=snowflake_config["user"],
            password=snowflake_config["password"],
            role=snowflake_config.get("role", "SYSADMIN"),
            warehouse=snowflake_config.get("warehouse", "COMPUTE_WH"),
            database=snowflake_config.get("database", "SMOOTHIES"),
            schema=snowflake_config.get("schema", "PUBLIC"),
            authenticator='snowflake'  # Default authenticator
        )
        return connection
    except Exception as e:
        logging.error("Failed to connect to Snowflake", exc_info=True)
        st.error("Failed to connect to Snowflake. Please check the logs for more details.")
        return None

def fetch_fruit_options(session):
    """
    Fetches fruit options from the Snowflake table.

    Args:
        session: Snowflake connection object.

    Returns:
        list: List of fruit names.
    """
    try:
        # Use Snowflake Connector to execute a query
        query = "SELECT FRUIT_NAME FROM smoothies.public.fruit_options"
        cursor = session.cursor()
        cursor.execute(query)
        fruit_rows = cursor.fetchall()
        fruit_options = [row[0] for row in fruit_rows]
        cursor.close()
        return fruit_options
    except Exception as e:
        logging.error("Error fetching fruit options", exc_info=True)
        st.error("Error fetching fruit options. Please check the logs for more details.")
        return []

def insert_order(session, ingredients, name):
    """
    Inserts a new order into the Snowflake table.

    Args:
        session: Snowflake connection object.
        ingredients (str): Space-separated string of ingredients.
        name (str): Name on the order.

    Returns:
        bool: True if insertion is successful, False otherwise.
    """
    try:
        # Parameterized query to prevent SQL injection
        insert_query = """
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES (%s, %s)
        """
        cursor = session.cursor()
        cursor.execute(insert_query, (ingredients, name))
        cursor.close()
        return True
    except Exception as e:
        logging.error("Error inserting order into Snowflake", exc_info=True)
        st.error("An error occurred while placing your order. Please check the logs for more details.")
        return False

def fetch_api_data():
    """
    Fetches data from the Smoothiefroot API.

    Returns:
        dict or None: JSON response from the API if successful, None otherwise.
    """
    try:
        response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to fetch data from Smoothiefroot API. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error("Error fetching data from Smoothiefroot API", exc_info=True)
        st.error("Error fetching data from Smoothiefroot API. Please check the logs for more details.")
        return None

def main():
    # Initialize Snowflake connection
    connection = get_snowflake_connection()
    if connection:
        session = connection  # Using the connection directly

        # Fetch data from Smoothiefroot API
        api_data = fetch_api_data()
        if api_data:
            st.subheader("Smoothiefroot API Data")
            st.json(api_data)  # Display the JSON response in a readable format

        # Write directly to the app
        st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
        st.write("""Choose the fruits you want in your custom Smoothie!""")
        
        # Input for the name on the order
        name_on_order = st.text_input("Name on Smoothie:")
        if name_on_order:
            st.write("The name on your Smoothie will be:", name_on_order)
        
        # Fetch fruit options from Snowflake
        fruit_options = fetch_fruit_options(session)
        if fruit_options:
            st.subheader("Available Fruits")
            st.write(f"Total Fruits Available: {len(fruit_options)}")
            st.dataframe(data=fruit_options, use_container_width=True)
        
            # Multiselect for ingredients
            ingredients_list = st.multiselect(
                'Choose up to 5 ingredients:',
                options=fruit_options
            )
            
            # Enforce a maximum of 5 selections
            if len(ingredients_list) > 5:
                st.warning("You can select up to 5 ingredients only. Only the first 5 will be considered.")
                ingredients_list = ingredients_list[:5]
            
            if ingredients_list and name_on_order:
                # Convert list of fruits to a space-separated string
                ingredients_string = ' '.join(ingredients_list)
                st.write(f"Selected Ingredients: {ingredients_string}")
                
                # Prepare the SQL insert statement using parameterized queries
                # This prevents SQL injection
                time_to_insert = st.button('Submit Order')
                
                if time_to_insert:
                    success = insert_order(session, ingredients_string, name_on_order)
                    if success:
                        success_message = f"Your Smoothie is ordered, {name_on_order}!"
                        st.success(success_message, icon="✅")
    else:
        st.stop()  # Stop execution if connection failed

if __name__ == "__main__":
    main()
