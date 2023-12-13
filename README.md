# Project: Office Locator

## Description
Office Locator is a dynamic data analysis tool integrating MongoDB, Foursquare API, and Folium for geospatial visualizations. Designed to identify optimal office locations based on specific criteria, it maps venues and analyzes urban data.

## Specific Needs and Final Location Choice
### Identifying Needs:
Utilizing MongoDB's database of companies, the primary focus was on locating areas dense with video game companies that raised over a million dollars. San Francisco emerged as the prime location with five established companies presenting promising opportunities.

### Decision-Making Criteria:
- Proximity to airports, train stations, bars, Starbucks, vegan restaurants, and basketball stadiums.
- Weighted considerations for each need to prioritize.

### Final Location:
The analysis concluded that Exent's office at 37.787646,-122.402759 (658 Market Street, San Francisco) is the optimal choice, considering the density of relevant companies and amenities.

## Features
- MongoDB integration for data storage.
- Foursquare API for real-time venue data.
- Folium for geospatial data visualization.
- Analysis of office locations and amenities.
- Customizable data queries.

## Installation
### Prerequisites
- Python 3.x
- MongoDB
- Foursquare API access

### Libraries
Required Python libraries:
- pandas, folium, pymongo, python-dotenv, requests, geopy, plotly

Install with:
```bash
$pip install pandas folium pymongo python-dotenv requests geopy plotly
```

## Data Sources
### MongoDB - Companies Collection
Stores company data including location and industry.

### Foursquare API
Provides venue data for enhanced urban landscape analysis.

## Process of Identifying the Best Office Locations
1. **Data Collection and Integration**
2. **Criteria Definition**
3. **Data Analysis and Geospatial Analysis**
4. **Optimization and Scoring**
5. **Interactive Visualization**
6. **Final Selection**


## Conclusion
The Office Locator successfully combines database querying, API usage, and analytical decision-making. It's a data-driven approach tailored to the specific needs of locating a prime office space, exemplified by the choice of Exent's office in San Francisco.

![Office Best Location Map](https://github.com/imfap1/Office-Locator/blob/main/maps/office_best_location.png?raw=true)
