from src import mongo, api
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('token')

db, c = mongo.connection_database("Ironhack", "Companies")

condition1 = {"category_code": "games_video"}
condition2 = {"funding_rounds.raised_amount": {"$gt": 1000000}}

offices_by_condition = mongo.count_offices_by_condition(c, condition1, condition2)
offices_by_condition

condition_design = {"category_code": {"$in": ["design", "web"]}}
condition_funding = {"funding_rounds.raised_amount": {"$gt": 1000000}}

result_design_web = mongo.count_offices_by_condition(c, condition_design, condition_funding)
result_design_web

city_name_sf = "San Francisco"
design_web_startups_sf = mongo.design_web_startup_finder(c, city_name_sf)
design_web_startups_sf.head()

city = "San Francisco"
min_employees = 87
max_employees = 150
collection_name = 'san_francisco_offices'
sf_offices_df = mongo.find_offices_by_criteria(c, city, min_employees, max_employees)
inserting_offices = mongo.insert_offices_data_create_index(city,min_employees, max_employees, collection_name, db)
inserting_offices
sf_offices_df


# Center of San Francisco
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

office_scores = mongo.best_office_location()

mongo.converting_to_collection()

office_scores = mongo.best_office_location()


mongo.final_location()
