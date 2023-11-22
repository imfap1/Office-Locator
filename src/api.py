from dotenv import load_dotenv
import os
import time
import json
import requests
import pandas as pd


load_dotenv()
token = os.getenv('token')

CACHE_DIR = './data'

def foursquare_places(venue, token, latitude=None, longitude=None, limit=5):
    cache_file_path = os.path.join(CACHE_DIR, f'{venue}.json')

    try:
        with open(cache_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        pass  

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

        with open(cache_file_path, 'w') as file:
            json.dump(venues, file)

        return venues
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []
    finally:
        time.sleep(2)
        

def get_venues_dataframe(venue, token, latitude=None, longitude=None, limit=5):
    cache_file_path = os.path.join(CACHE_DIR, f'{venue}.json')

    try:
        with open(cache_file_path, 'r') as file:
            venues = json.load(file)
    except FileNotFoundError:
        venues = foursquare_places(venue, token, latitude=latitude, longitude=longitude, limit=limit)

        with open(cache_file_path, 'w') as file:
            json.dump(venues, file)

    names = []
    latitudes = []
    longitudes = []

    for venue_info in venues:
        if 'geocodes' in venue_info:
            location = venue_info['geocodes'].get('main', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')

            names.append(venue_info.get('name', 'Unknown Name'))
            latitudes.append(latitude)
            longitudes.append(longitude)

    df_venues = pd.DataFrame({'name': names, 'Lat': latitudes, 'Lng': longitudes, 'category': venue})

    return df_venues


latitude = 37.7804301
longitude = -122.4103305
limit= 30

venue = "design talks"
df_design_talks = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "bar"
df_bars = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "night club"
df_clubs = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "airport"
df_airport = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)

venue = "train station"
df_train = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "ferry"
df_ferry = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=5)

venue = "vegan restaurant"
df_vegan = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "basketball stadium"
df_basketball = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "pet grooming"
df_grooming = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "school"
df_school = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)

venue = "starbucks"
df_starbucks = get_venues_dataframe(venue, token, latitude=latitude, longitude=longitude, limit=limit)