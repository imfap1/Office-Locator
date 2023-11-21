# %%
from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import json
import plotly.graph_objects as go
import folium
from folium import Choropleth, Circle, Marker, Icon, Map, plugins
from folium.plugins import HeatMap, MarkerCluster
import time
import geopy.distance
import math
from geopy.distance import geodesic
from geopy.distance import great_circle


# Hidding my token for FourSquare
load_dotenv()
token = os.getenv('token')


def conection_collection():
    # Connect to MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017/")
        print("Successful connection to MongoDB")
    except Exception as e:
        print(f"Unable to connect to MongoDB. Error: {e}")
        # Handle the error or exit the program if connection fails

    # Get the database and collection
    try:
        db = client.get_database("Ironhack")
        c = db.Companies
        print("Successful connection to the database and collection")
    except Exception as e:
        print(f"Unable to access the database or collection. Error: {e}")
        # Handle the error or exit the program if access fails
    return c


def conection_client():
    # Connect to MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017/")
        print("Successful connection to MongoDB")
    except Exception as e:
        print(f"Unable to connect to MongoDB. Error: {e}")
        # Handle the error or exit the program if connection fails

    # Get the database and collection
    try:
        db = client.get_database("Ironhack")
        c = db.Companies
        print("Successful connection to the database and collection")
    except Exception as e:
        print(f"Unable to access the database or collection. Error: {e}")
        # Handle the error or exit the program if access fails
    return db


db = conection_client()


c = conection_collection()


# visualizing sample
sample_documents = c.find().limit(5)
print("Sample documents:")
for document in sample_documents:
    print(document)


def count_offices_by_condition(collection, condition1, condition2):
    """
    Count the number of offices for companies meeting the specified conditions.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to query.
        condition1 (dict): First condition for filtering companies.
        condition2 (dict): Second condition for filtering companies.

    Returns:
        pandas.Series: A Series containing the count of offices for each unique office location.
    """
    query = {"$and": [condition1, condition2]}
    projection = {"name": 1, "offices.city": 1, "_id": 0}
    
    cursor = collection.find(query, projection)
    data = []

    for company in cursor:
        for office in company.get('offices', []):
            data.append(office.get('city'))

    if data:
        office_counts = pd.Series(data).value_counts()
        return office_counts
    else:
        return pd.Series()  

condition1 = {"category_code": "games_video"}
condition2 = {"funding_rounds.raised_amount": {"$gt": 1000000}}

result = count_offices_by_condition(c, condition1, condition2)
result



# Conditions for design and web
condition_design = {"category_code": {"$in": ["design", "web"]}}
condition_funding = {"funding_rounds.raised_amount": {"$gt": 1000000}}

# Call the function for design and web
result_design_web = count_offices_by_condition(c, condition_design, condition_funding)

# Print the result for design and web
print(result_design_web)




def gaming_startup_finder(collection, city_name):
    """
    Retrieve gaming startups in a specific city that have raised over $1 million in funding.

    Parameters:
    - collection: MongoDB collection
    - city_name: Name of the city to search for gaming startups

    Returns:
    - A Pandas DataFrame containing the names, latitude, and longitude of the gaming startups in the specified city.
    """
    try:
        # Define conditions for the query
        condition_city = {"offices.city": city_name}
        condition_category = {"category_code": "games_video"}
        condition_funding = {"funding_rounds.raised_amount": {"$gt": 1000000}}
        query = {"$and": [condition_city, condition_category, condition_funding]}

        # Aggregation pipeline
        pipeline = [
            {"$match": query},
            {"$unwind": "$offices"},
            {"$match": {"offices.city": city_name}},
            {"$project": {"_id": 0, "name": 1, "latitude": "$offices.latitude", "longitude": "$offices.longitude"}}
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Create a DataFrame and handle duplicates and missing values
        df = pd.DataFrame(result).drop_duplicates().dropna()

        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

# Example usage
city_name_sf = "San Francisco"
gaming_startups_sf = gaming_startup_finder(c, city_name_sf)
gaming_startups_sf.head()


def design_web_startup_finder(collection, city_name):
    """
    Retrieve design and web startups in a specific city.

    Parameters:
    - collection: MongoDB collection
    - city_name: Name of the city to search for design and web startups

    Returns:
    - A Pandas DataFrame containing the names, latitude, and longitude of the design and web startups in the specified city.
    """
    try:
        # Define conditions for the query
        condition_city = {"offices.city": city_name}
        condition_category = {"$or": [{"category_code": "design"}, {"category_code": "web"}]}
        query = {"$and": [condition_city, condition_category]}

        # Aggregation pipeline
        pipeline = [
            {"$match": query},
            {"$unwind": "$offices"},
            {"$match": {"offices.city": city_name}},
            {"$project": {"_id": 0, "name": 1, "latitude": "$offices.latitude", "longitude": "$offices.longitude", "category_code": 1}}
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Create a DataFrame and handle duplicates and missing values
        df = pd.DataFrame(result).drop_duplicates().dropna()

        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

city_name_sf = "San Francisco"
design_web_startups_sf = design_web_startup_finder(c, city_name_sf)
design_web_startups_sf.head()


def find_offices_by_criteria(collection, city, min_employees, max_employees):
    """
    Find offices in a specific city that can accommodate a specified range of employees.

    Parameters:
    - collection: MongoDB collection
    - city: Name of the city to search for offices
    - min_employees: Minimum number of employees the office can accommodate
    - max_employees: Maximum number of employees the office can accommodate

    Returns:
    - A Pandas DataFrame containing information about the offices that meet the criteria.
    """
    try:
        # Define criteria
        condition_city = {"offices.city": city}
        condition_category = {"category_code": "games_video"}
        condition_employees = {"number_of_employees": {"$gte": min_employees, "$lte": max_employees}}

        # Create the aggregation pipeline
        pipeline = [
            {"$unwind": "$offices"},
            {"$match": {"$and": [condition_city, condition_employees, condition_category]}},
            {"$project": {
                "_id": 0,
                "name": 1,
                "latitude": "$offices.latitude",
                "longitude": "$offices.longitude",
                "address": "$offices.address1",
                "city": "$offices.city",
                "employees": "$number_of_employees",
                "category_code": 1
            }}
        ]

        # Execute the aggregation
        result = list(collection.aggregate(pipeline))

        # Create a DataFrame from the results
        df = pd.DataFrame(result)

        # Remove duplicate rows and rows with missing values
        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()


def insert_offices_data_create_index(collection_name, db):
    
    city_sf = "San Francisco"
    min_employees_sf = 87
    max_employees_sf = 150
    sf_offices_df = find_offices_by_criteria(c, city_sf, min_employees_sf, max_employees_sf)
    sf_offices_df
    
    # Drop the collection if it exists for a clean start
    db[collection_name].drop()

    # Convert latitude and longitude to GeoJSON format
    sf_offices_df['location'] = sf_offices_df.apply(lambda row: {'type': 'Point', 'coordinates': [row['longitude'], row['latitude']]}, axis=1)

    # Drop the original latitude and longitude columns
    sf_offices_df.drop(['latitude', 'longitude'], axis=1, inplace=True)

    # Convert the dataframe to a list of dictionaries
    records = sf_offices_df.to_dict(orient="records")

    # Insert the data into the corresponding collection
    db[collection_name].insert_many(records)

    # Create a 2dsphere index on the 'location' field
    db[collection_name].create_index([("location", "2dsphere")])

    # Return confirmation
    return f"Data inserted and index created for {collection_name}"

# Use the function for the 'sf_offices_df' dataframe
result = insert_offices_data_create_index('san_francisco_offices', db)
print(result)


city_sf = "San Francisco"
min_employees_sf = 87
max_employees_sf = 150
sf_offices_df = find_offices_by_criteria(c, city_sf, min_employees_sf, max_employees_sf)
sf_offices_df

def map_offices():
    map_center = [sf_offices_df['latitude'].mean(), sf_offices_df['longitude'].mean()]
    startup_map = folium.Map(location=map_center, zoom_start=13)

    # Add markers for each location in the DataFrame
    for index, row in sf_offices_df.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['name']}, Employees: {row['employees']}",
            tooltip=row['name']
        ).add_to(startup_map)

    # Save the map as an HTML file
    map_filename = 'startups_map.html'
    startup_map.save(f'./maps/{map_filename}')

    # Display the map in a Jupyter notebook
    return startup_map



map_offices()

def design_web_and_gaming():
    # Combine design/web and gaming DataFrames
    all_companies_df = pd.concat([design_web_startups_sf, sf_offices_df], ignore_index=True)

    # Function to check if a location is within the desired area
    def is_within_desired_area(location, center, radius):
        coords_location = (location["latitude"], location["longitude"])
        coords_center = (center[0], center[1])
        distance = geopy.distance.distance(coords_location, coords_center).meters
        return distance <= radius

    # Filter companies within the desired area
    desired_area_location_sf = [37.7804301, -122.4103305]
    desired_area_radius_sf = 3500

    all_companies_df["within_desired_area"] = all_companies_df.apply(
        lambda row: is_within_desired_area(row, desired_area_location_sf, desired_area_radius_sf),
        axis=1
    )

    filtered_companies_df = all_companies_df[all_companies_df["within_desired_area"]]

    # Create a map with markers for each company within the desired area
    map_filtered_companies = folium.Map(location=desired_area_location_sf, zoom_start=12)

    for index, row in filtered_companies_df.iterrows():
        company_name = row["name"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        is_gaming = row["category_code"] == "games_video"

        # Determine the color and icon based on gaming status
        color = "red" if is_gaming else "blue"
        icon = folium.Icon(color=color, icon_color="white", icon="building", prefix="fa")

        # Create a marker for each office
        tooltip_content = f"{company_name}"
        folium.Marker([latitude, longitude], tooltip=tooltip_content, icon=icon).add_to(map_filtered_companies)

    # Add a circle to represent the desired area
    folium.Circle(location=desired_area_location_sf, fill_color='rgba(0, 0, 255, 0.1)',
                radius=desired_area_radius_sf, weight=2, color="blue", popup="Desired Area").add_to(map_filtered_companies)

    # Save the map as an HTML file
    map_filtered_companies.save('./maps/filtered_companies.html')
    return map_filtered_companies

    

CACHE_DIR = './data'

def foursquare_places(venue, token, latitude=None, longitude=None, limit=5):
    cache_file_path = os.path.join(CACHE_DIR, f'{venue}.json')

    # Intenta cargar los datos desde el archivo en caché
    try:
        with open(cache_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        pass  # El archivo en caché no existe, continúa con la llamada a la API

    # Si no está en caché, realiza la llamada a la API
    endpoint = f'https://api.foursquare.com/v3/places/search?query={venue}'

    if latitude is not None and longitude is not None:
        endpoint += f'&ll={latitude},{longitude}'

    endpoint += f'&limit={limit}'

    headers = {
        "accept": "application/json",
        "Authorization": token
    }

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        venues = data.get('results', [])

        # Guarda los datos en caché para futuros usos
        with open(cache_file_path, 'w') as file:
            json.dump(venues, file)

        return venues
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []
    finally:
        time.sleep(2)


CACHE_DIR = './data'

def get_venues_dataframe(venue, token, latitude=None, longitude=None, limit=5):
    # Construct the cache file path
    cache_file_path = os.path.join(CACHE_DIR, f'{venue}.json')

    # Try to load data from the cache file
    try:
        with open(cache_file_path, 'r') as file:
            venues = json.load(file)
    except FileNotFoundError:
        # If not in the cache, make the API call
        venues = foursquare_places(venue, token, latitude=latitude, longitude=longitude, limit=limit)

        # Save the data to the cache file for future use
        with open(cache_file_path, 'w') as file:
            json.dump(venues, file)

    # Initialize empty lists to store extracted information
    names = []
    latitudes = []
    longitudes = []

    # Loop through each venue in the list
    for venue_info in venues:
        # Check if 'geocodes' key is present
        if 'geocodes' in venue_info:
            # Extract latitude and longitude from 'geocodes' if available
            location = venue_info['geocodes'].get('main', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')

            # Append the extracted information to the respective lists
            names.append(venue_info.get('name', 'Unknown Name'))
            latitudes.append(latitude)
            longitudes.append(longitude)

    # Create a DataFrame from the extracted information
    df_venues = pd.DataFrame({'name': names, 'Lat': latitudes, 'Lng': longitudes, 'category': venue})

    return df_venues


latitude = 37.7804301
longitude = -122.4103305
limit= 30


venue = "design talks"

df_design_talks = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_design_talks

venue = "starbucks"

df_starbucks = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_starbucks

venue = "bar"

df_bars = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_bars

venue = "night club"

df_clubs = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_clubs

venue = "airport"

df_airport = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)
df_airport

venue = "train station"

df_train = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_train

venue = "ferry"

df_ferry = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)
df_ferry

venue = "vegan restaurant"

df_vegan = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_vegan

venue = "basketball stadium"

df_basketball = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_basketball

venue = "pet grooming"

df_grooming = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_grooming

venue = "school"

df_school = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)
df_school

import time
def  converting_to_collection():
    # Convert and insert each DataFrame into a collection
    collections = {
        "df_school": df_school,
        "df_grooming": df_grooming,
        "df_basketball": df_basketball,
        "df_vegan": df_vegan,
        "df_ferry": df_ferry,
        "df_train": df_train,
        "df_airport": df_airport,
        "df_clubs": df_clubs,
        "df_bars": df_bars,
        "df_starbucks": df_starbucks,
        "df_design_talks": df_design_talks
    }


    for collection_name, df in collections.items():
        # Drop the collection if it exists (for a fresh start)
        db[collection_name].drop()

        # Convert latitude and longitude to GeoJSON format
        # Ensure the order is [longitude, latitude]
        df['location'] = df.apply(lambda row: {'type': 'Point', 'coordinates': [row['Lng'], row['Lat']]}, axis=1)

        # Convert the dataframe to a list of dictionaries
        records = df.to_dict(orient="records")

        # Insert the data into the corresponding collection
        db[collection_name].insert_many(records)

        # Create a 2dsphere index on the 'location' field
        db[collection_name].create_index([("location", "2dsphere")])

        # Pause for a few seconds to ensure index creation
        time.sleep(2)

# Just testing if i could get the nearest grooming places!!

db = conection_client()

# Define the coordinates of the potential office location (hi5 company example)
office_location = [-122.400558, 37.788668]  # Longitude comes first in GeoJSON

# Set the maximum search radius in meters (10km)
max_distance = 5000

# Find all pet grooming places within 10km radius of the potential office location
pet_grooming_places = db.df_grooming.find({
    'location': {
        '$near': {
            '$geometry': {
                'type': 'Point',
                'coordinates': office_location
            },
            '$maxDistance': max_distance
        }
    },
    'category': 'pet grooming'
})

# Print out the names of the pet grooming places
for place in pet_grooming_places:
    print(place['name'])


def best_office_location():
    # Constants for maximum distances (in meters) for full score per category
    MAX_DISTANCE = {
        'df_school': 3000,  # Example: Max distance for a school to get a full score
        'df_grooming': 1000,  # Max distance for pet grooming
        'df_basketball': 10000,  # Max distance for basketball stadium
        'df_vegan': 1000,  # The CEO is vegan.
        'df_ferry': 5000,  # Account managers need to travel a lot.
        'df_train': 1000,  # Account managers need to travel a lot.
        'df_airport': 20000,  # Account managers need to travel a lot.
        'df_clubs': 1000,  # Everyone is between 25 and 40, they might want to party.
        'df_bars': 1000,  # Everyone is between 25 and 40, they might want to party.
        'df_starbucks': 1000,  # Executives like Starbucks A LOT.
        'df_design_talks': 1000  # Designers like to go to design talks and share knowledge.
    }


    # Function to calculate a normalized score between 0 and 1 based on distance
    def normalized_score(distance, max_distance):
        if distance > max_distance:
            return 0
        else:
            # Using a square root function for a non-linear score decrease
            return math.sqrt(1 - (distance / max_distance) ** 2)

    # Function to calculate the distance between two points
    def calculate_distance(point1, point2):
        # The points are expected to be in [longitude, latitude] format
        # Convert them into (latitude, longitude) format for geopy
        point1 = tuple(reversed(point1))
        point2 = tuple(reversed(point2))
        
        # Use geopy's geodesic function to calculate the distance between the two points
        distance = geodesic(point1, point2).meters  # distance in meters
        return distance


    # Constants for the weights (you can adjust these based on your priorities)
    WEIGHTS = {
        'df_school': 0.1,  # 30% of the company staff have at least 1 child.
        'df_grooming': 0.05,  # For the office dog "Dobby".
        'df_basketball': 0.05,  # For the maintenance guy.
        'df_vegan': 0.15,  # The CEO is vegan.
        'df_ferry': 0.05,  # Account managers need to travel a lot.
        'df_train': 0.05,  # Account managers need to travel a lot.
        'df_airport': 0.05,  # Account managers need to travel a lot.
        'df_clubs': 0.1,  # Everyone is between 25 and 40, they might want to party.
        'df_bars': 0.1,  # Everyone is between 25 and 40, they might want to party.
        'df_starbucks': 0.15,  # Executives like Starbucks A LOT.
        'df_design_talks': 0.15  # Designers like to go to design talks and share knowledge.
    }

    # Function to calculate the proximity score for a given office location
    def calculate_proximity_score(office, db):
        score = 0
        office_location = office['location']['coordinates']
        
        for venue_type, weight in WEIGHTS.items():
            # Find the nearest venue of each type to this office
            nearest_venue = db[venue_type].find_one({
                'location': {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': office_location
                        }
                    }
                }
            })
                    
            # If there's a nearest venue, calculate its proximity score
            if nearest_venue:
                # Calculate distance between office and the venue
                distance = calculate_distance(office_location, nearest_venue['location']['coordinates'])

                # Get the normalized score for the distance
                max_dist = MAX_DISTANCE.get(venue_type, 1000)  # Default max distance
                dist_score = normalized_score(distance, max_dist)
                            
                # Add to total score, weighted by the importance of this venue type
                score += dist_score * weight
                

        return score

    def find_best_office_location():
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client['Ironhack']
        
        # Get all possible office locations
        offices = db['san_francisco_offices'].find()
        
        # Calculate the score for each office based on proximity to desired venues
        office_scores = []
        for office in offices:
            office_score = {
                'office': office['name'],  # Office name
                'score': round(calculate_proximity_score(office, db), 2),  # Proximity score
                'location': office['location']['coordinates']  # Office location
            }
            office_scores.append(office_score)
            
        # Sort the offices by score, highest first
        office_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Return the list of offices with their scores and locations
        return office_scores

    office_scores = find_best_office_location()
    
    return office_scores

office_scores = best_office_location()


def final_location():
    def create_office_map(best_office, all_venues, radius=1000):  # radius in meters
        # Create a map centered around the best office
        office_location = [best_office['location'][1], best_office['location'][0]]  # [lat, lng]
        office_map = folium.Map(location=office_location, zoom_start=15)

        # Add a marker for the best office
        folium.Marker(
            location=office_location,
            popup=f"{best_office['office']} - Score: {best_office['score']:.2f}",
            tooltip=best_office['office'],
            icon=folium.Icon(color='red', icon='star')
        ).add_to(office_map)

        # Define different icon colors for different venue categories
        icon_colors = {
            'school': ('green', 'graduation-cap'),
            'airport': ('cadetblue', 'plane'),
            'bar': ('blue', 'beer'),
            'basketball stadium': ('orange', 'bullseye'),
            'night club': ('red', 'star'),
            'design talks': ('purple', 'thumb-tack'),
            'ferry': ('darkblue', 'ship'),
            'pet grooming': ('brown', 'paw'),
            'starbucks': ('darkgreen', 'coffee'),
            'train station': ('lightblue', 'train')
        }
        for _, venue in all_venues.iterrows():
            if venue['category'] == 'airport':
                venue_location = [venue['Lat'], venue['Lng']]  # [lat, lng]
                folium.Marker(
                    location=venue_location,
                    popup=f"{venue['name']} ({venue['category']})",
                    tooltip=venue['name'],
                    icon=folium.Icon(color=icon_colors['airport'], icon='plane', prefix='fa')
                ).add_to(office_map)
        # Add markers for the venues within the specified radius
        for _, venue in all_venues.iterrows():
            venue_location = [venue['Lat'], venue['Lng']]  # [lat, lng]
            # Calculate the distance from the office to the venue
            if great_circle(office_location, venue_location).meters <= radius:
                # Select the icon color and icon based on the venue's category
                venue_icon_color, venue_icon_name = icon_colors.get(venue['category'], ('gray', 'flag'))  # Default color is gray and icon is flag
                folium.Marker(
                    location=venue_location,
                    popup=f"{venue['name']} ({venue['category']})",
                    tooltip=venue['name'],
                    icon=folium.Icon(color=venue_icon_color, icon=venue_icon_name, prefix='fa')
                ).add_to(office_map)

        # Add circles for different radii
        folium.Circle(
            location=office_location,
            radius=1000,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.1,
            popup='1 km radius'
        ).add_to(office_map)

        folium.Circle(
            location=office_location,
            radius=2000,
            color='orange',
            fill=True,
            fill_color='orange',
            fill_opacity=0.1,
            popup='2 km radius'
        ).add_to(office_map)

        folium.Circle(
            location=office_location,
            radius=3500,
            color='pink',
            fill=True,
            fill_color='pink',
            fill_opacity=0.1,
            popup='3.5 km radius'
        ).add_to(office_map)

        # Save the map to an HTML file
        office_map.save("./maps/office_best_location_and_venues.html")

        return office_map

    # Usage
    best_office = office_scores[0] 
    radius = 4000  # Define the radius within which to look for venues

    # Concatenate all venue DataFrames into one if not already done
    all_venues = pd.concat([df_school, df_airport, df_bars, df_basketball, df_clubs, df_design_talks, df_ferry, df_grooming, df_starbucks, df_train])

    # Call the function and create the map
    office_map = create_office_map(best_office, all_venues, radius)

    # Open the saved HTML file in a web browser to view the map
    return office_map

final_location()


