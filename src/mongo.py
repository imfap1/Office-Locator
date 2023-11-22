from pymongo import MongoClient
import time
import logging
import pandas as pd
import math
from geopy.distance import geodesic
import folium
from geopy.distance import great_circle
import sys
sys.path.append("./src")
import api
from dotenv import load_dotenv
import os
import webbrowser

load_dotenv()
token = os.getenv('token')


# Conecting to the database and collection that is in mongoDB
def connection_database(database, collection):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        print("Successful connection to MongoDB")
    except Exception as e:
        print(f"Unable to connect to MongoDB. Error: {e}")

    try:
        db = client[database]
        c = db[collection]
        logging.info("Successful connection to the database and collection.")
    except Exception as e:
        logging.error(f"Error connecting to the database or collection: {e}")
        return None
    return db, c

db, c = connection_database("Ironhack", "Companies")

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

offices_by_condition = count_offices_by_condition(c, condition1, condition2)
offices_by_condition

condition_design = {"category_code": {"$in": ["design", "web"]}}
condition_funding = {"funding_rounds.raised_amount": {"$gt": 1000000}}

result_design_web = count_offices_by_condition(c, condition_design, condition_funding)
result_design_web

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
        condition_city = {"offices.city": city_name}
        condition_category = {"category_code": "games_video"}
        condition_funding = {"funding_rounds.raised_amount": {"$gt": 1000000}}
        query = {"$and": [condition_city, condition_category, condition_funding]}

        pipeline = [
            {"$match": query},
            {"$unwind": "$offices"},
            {"$match": {"offices.city": city_name}},
            {"$project": {"_id": 0, "name": 1, "latitude": "$offices.latitude", "longitude": "$offices.longitude"}}
        ]

        result = list(collection.aggregate(pipeline))

        df = pd.DataFrame(result).drop_duplicates().dropna()

        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

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
        condition_city = {"offices.city": city_name}
        condition_category = {"$or": [{"category_code": "design"}, {"category_code": "web"}]}
        query = {"$and": [condition_city, condition_category]}

        pipeline = [
            {"$match": query},
            {"$unwind": "$offices"},
            {"$match": {"offices.city": city_name}},
            {"$project": {"_id": 0, "name": 1, "latitude": "$offices.latitude", "longitude": "$offices.longitude", "category_code": 1}}
        ]

        result = list(collection.aggregate(pipeline))

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
        condition_city = {"offices.city": city}
        condition_category = {"category_code": "games_video"}
        condition_employees = {"number_of_employees": {"$gte": min_employees, "$lte": max_employees}}

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

        result = list(collection.aggregate(pipeline))

        df = pd.DataFrame(result)

        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()
    

def insert_offices_data_create_index(city, min_employees, max_employees, collection_name, db):

    """
    Inserts office data into a MongoDB collection and creates a geospatial index. 
    This function first finds offices in a specific city that can accommodate a specified range of employees using the
    'find_offices_by_criteria' function. It then processes this data for geospatial querying by converting latitude and longitude into GeoJSON format and inserting the data into the specified MongoDB collection. After insertion, it creates a 2dsphere index on the 'location' field for efficient geospatial queries.

    Parameters:
    - city: Name of the city to search for offices.
    - min_employees: Minimum number of employees the office can accommodate.
    - max_employees: Maximum number of employees the office can accommodate.
    - collection_name: Name of the MongoDB collection where data will be inserted.
    - db: MongoDB database instance.

    Returns:
    - A confirmation message indicating successful data insertion and index creation.
    """
    
    city_sf = city
    min_employees_sf = min_employees
    max_employees_sf = max_employees
    sf_offices_df = find_offices_by_criteria(c, city_sf, min_employees_sf, max_employees_sf)
    sf_offices_df
    
    db[collection_name].drop()

    sf_offices_df['location'] = sf_offices_df.apply(lambda row: {'type': 'Point', 'coordinates': [row['longitude'], row['latitude']]}, axis=1)

    sf_offices_df.drop(['latitude', 'longitude'], axis=1, inplace=True)

    records = sf_offices_df.to_dict(orient="records")

    db[collection_name].insert_many(records)

    db[collection_name].create_index([("location", "2dsphere")])

    return f"Data inserted and index created for {collection_name}"



city = "San Francisco"
min_employees = 87
max_employees = 150
collection_name = 'san_francisco_offices'
sf_offices_df = find_offices_by_criteria(c, city, min_employees, max_employees)
inserting_offices = insert_offices_data_create_index(city,min_employees, max_employees, collection_name, db)
inserting_offices
sf_offices_df


latitude = 37.7804301
longitude = -122.4103305
limit= 30

venue = "design talks"
df_design_talks = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "bar"
df_bars = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "night club"
df_clubs = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "airport"
df_airport = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)

venue = "train station"
df_train = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "ferry"
df_ferry = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)

venue = "vegan restaurant"
df_vegan = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "basketball stadium"
df_basketball = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "pet grooming"
df_grooming = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "school"
df_school = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "starbucks"
df_starbucks = api.get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

def  converting_to_collection():
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
        db[collection_name].drop()

        df['location'] = df.apply(lambda row: {'type': 'Point', 'coordinates': [row['Lng'], row['Lat']]}, axis=1)

        records = df.to_dict(orient="records")

        db[collection_name].insert_many(records)

        db[collection_name].create_index([("location", "2dsphere")])

        time.sleep(2)
        
converting_to_collection()

    
    
def best_office_location():
    MAX_DISTANCE = {
        'df_school': 3000, 
        'df_grooming': 1000,  
        'df_basketball': 10000,
        'df_vegan': 1000,  
        'df_ferry': 5000, 
        'df_train': 1000,  
        'df_airport': 20000,  
        'df_clubs': 1000,  
        'df_bars': 1000,  
        'df_starbucks': 1000,  
        'df_design_talks': 1000 
    }


    def normalized_score(distance, max_distance):
        if distance > max_distance:
            return 0
        else:
            return math.sqrt(1 - (distance / max_distance) ** 2)

    def calculate_distance(point1, point2):
        point1 = tuple(reversed(point1))
        point2 = tuple(reversed(point2))
        
        distance = geodesic(point1, point2).meters  # distance in meters
        return distance


    WEIGHTS = {
        'df_school': 0.1,  
        'df_grooming': 0.05,  
        'df_basketball': 0.05,  
        'df_vegan': 0.15,  
        'df_ferry': 0.05,  
        'df_train': 0.05,  
        'df_airport': 0.05,  
        'df_clubs': 0.1,  
        'df_bars': 0.1,  
        'df_starbucks': 0.15,  
        'df_design_talks': 0.15 
    }

    
    def calculate_proximity_score(office, db):
        score = 0
        office_location = office['location']['coordinates']
        
        for venue_type, weight in WEIGHTS.items():
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
                    
            if nearest_venue:
                distance = calculate_distance(office_location, nearest_venue['location']['coordinates'])

                max_dist = MAX_DISTANCE.get(venue_type, 1000)  # Default max distance
                dist_score = normalized_score(distance, max_dist)
                            
                score += dist_score * weight
                

        return score

    def find_best_office_location():
        client = MongoClient("mongodb://localhost:27017/")
        db = client['Ironhack']
        
        offices = db['san_francisco_offices'].find()
        
        office_scores = []
        for office in offices:
            office_score = {
                'office': office['name'],  
                'score': round(calculate_proximity_score(office, db), 2),
                'location': office['location']['coordinates']  
            }
            office_scores.append(office_score)
            
        office_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return office_scores

    office_scores = find_best_office_location()
    
    return office_scores

office_scores = best_office_location()

office_scores


def final_location():
    def create_office_map(best_office, all_venues, radius=1000): 
        office_location = [best_office['location'][1], best_office['location'][0]] 
        office_map = folium.Map(location=office_location, zoom_start=15)

        folium.Marker(
            location=office_location,
            popup=f"{best_office['office']} - Score: {best_office['score']:.2f}",
            tooltip=best_office['office'],
            icon=folium.Icon(color='red', icon='star')
        ).add_to(office_map)

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
                venue_location = [venue['Lat'], venue['Lng']] 
                folium.Marker(
                    location=venue_location,
                    popup=f"{venue['name']} ({venue['category']})",
                    tooltip=venue['name'],
                    icon=folium.Icon(color=icon_colors['airport'], icon='plane', prefix='fa')
                ).add_to(office_map)
        for _, venue in all_venues.iterrows():
            venue_location = [venue['Lat'], venue['Lng']]  
            if great_circle(office_location, venue_location).meters <= radius:
                venue_icon_color, venue_icon_name = icon_colors.get(venue['category'], ('gray', 'flag'))  
                folium.Marker(
                    location=venue_location,
                    popup=f"{venue['name']} ({venue['category']})",
                    tooltip=venue['name'],
                    icon=folium.Icon(color=venue_icon_color, icon=venue_icon_name, prefix='fa')
                ).add_to(office_map)

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

        map_file = "./maps/office_best_location_and_venues.html"
        office_map.save(map_file)

        final_map=  webbrowser.open('file://' + os.path.realpath(map_file))
        print("")

        return final_map

    best_office = office_scores[0] 
    radius = 4000  

    all_venues = pd.concat([df_school, df_airport, df_bars, df_basketball, df_clubs, df_design_talks, df_ferry, df_grooming, df_starbucks, df_train])

    create_office_map(best_office, all_venues, radius)
final_location()
