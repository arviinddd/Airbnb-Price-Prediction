from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import pandas as pd
import time
import numpy as np


# 1) Data extraction from API (Extract)
def fetch_airbnb_data(limit=100, offset=0):
    url = "https://public.opendatasoft.com/api/v2/catalog/datasets/air-bnb-listings/records"
    params = {
        "refine": "column_19:United states",
        "limit": limit,
        "offset": offset,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("records", [])


def fetch_all_data(limit=100):
    all_records = []
    offset = 0  
    while offset + limit <= 10000:  
        batch = fetch_airbnb_data(limit=limit, offset=offset)
        if not batch:
            break
        all_records.extend(batch)
        offset += limit  
        time.sleep(0.5)  
    return all_records


# 2) Transform and process data (Transform)
def scrape_airbnb_data(ti):
    data = fetch_all_data(limit=100)

    parsed_data = []
    for record in data:
        fields = record.get("record", {}).get("fields", {})
        coordinates = fields.get("coordinates", {})
        parsed_data.append({
            "Room ID": fields.get("id"),
            "Host ID": fields.get("host_id"),
            "Room type": fields.get("room_type"),
            "Room Price": str(fields.get("column_10", "")).replace("$", "").replace(",", ""),
            "Minimum nights": fields.get("minimum_nights"),
            "Number of reviews": fields.get("number_of_reviews"),
            "Review Date": fields.get("last_review") or fields.get("updated_date"),
            "Reviews per month": fields.get("reviews_per_month"),
            "Number of rentals by host": fields.get("calculated_host_listings_count"),
            "Availibility": fields.get("availability_365"),
            "Country": fields.get("column_19"),
            "City": fields.get("city"),
            "Latitude": coordinates.get("lat"),
            "Longitude": coordinates.get("lon")
        })

    
    df = pd.DataFrame(parsed_data)
    df['Availibility'] = df['Availibility'].apply(lambda x: 'Yes' if x > 0 else 'No')
    df['Reviews per month'] = df['Reviews per month'].fillna(0).apply(np.floor).astype(int)
    df['Minimum nights'] = df['Minimum nights'].clip(lower=1, upper=7)
    df.dropna(inplace=True)

    ti.xcom_push(key='airbnb_data', value=df.to_dict('records'))


# 3) Loading data into PostgreSQL (Load)
def insert_airbnb_data_into_postgres(ti):
    airbnb_data = ti.xcom_pull(key='airbnb_data', task_ids='scrape_airbnb_data')
    if not airbnb_data:
        raise ValueError("No Airbnb data found")

    postgres_hook = PostgresHook(postgres_conn_id='airbnb_connection')

    
    room_type_mapping = {
        'Entire home/apt': 1,
        'Private room': 2,
        'Hotel room': 3,
        'Shared room': 4
    }
    for room_type, room_type_id in room_type_mapping.items():
        postgres_hook.run("""
        INSERT INTO Roomtype (Room_typeID, Room_type)
        VALUES (%s, %s)
        ON CONFLICT (Room_typeID) DO NOTHING;
        """, parameters=(room_type_id, room_type))

    
    availibility_mapping = {'Yes': 1, 'No': 2}
    for availibility, availibility_id in availibility_mapping.items():
        postgres_hook.run("""
        INSERT INTO Availibility (AvailibilityID, Availibility)
        VALUES (%s, %s)
        ON CONFLICT (AvailibilityID) DO NOTHING;
        """, parameters=(availibility_id, availibility))

    
    countries = {record['Country'] for record in airbnb_data}
    for country in countries:
        postgres_hook.run("""
        INSERT INTO Country (Country)
        VALUES (%s)
        ON CONFLICT (Country) DO NOTHING;
        """, parameters=(country,))

    
    cities = {record['City'] for record in airbnb_data}
    for city in cities:
        postgres_hook.run("""
        INSERT INTO City (City)
        VALUES (%s)
        ON CONFLICT (City) DO NOTHING;
        """, parameters=(city,))

    
    coordinates = {(record['Latitude'], record['Longitude']) for record in airbnb_data}
    for latitude, longitude in coordinates:
        postgres_hook.run("""
        INSERT INTO Coordinates (Latitude, Longitude)
        VALUES (%s, %s)
        ON CONFLICT (Latitude, Longitude) DO NOTHING;
        """, parameters=(latitude, longitude))

    
    for record in airbnb_data:
        postgres_hook.run("""
        INSERT INTO Listings (
            Room_ID, Host_ID, Room_typeID, Room_Price, Minimum_nights, 
            Number_of_reviews, Reviews_per_month, Number_of_rentals_by_host, 
            AvailibilityID, Review_Date, CountryID, CityID, CoordinatesID
        )
        SELECT 
            %s, %s, 
            (SELECT Room_typeID FROM Roomtype WHERE Room_type = %s),
            %s, %s, %s, %s, %s,
            (SELECT AvailibilityID FROM Availibility WHERE Availibility = %s),
            %s,
            (SELECT CountryID FROM Country WHERE Country = %s),
            (SELECT CityID FROM City WHERE City = %s),
            (SELECT CoordinatesID FROM Coordinates WHERE Latitude = %s AND Longitude = %s)
        ON CONFLICT (Room_ID) DO NOTHING;
        """, parameters=(
            record['Room ID'], record['Host ID'], record['Room type'], record['Room Price'],
            record['Minimum nights'], record['Number of reviews'], record['Reviews per month'],
            record['Number of rentals by host'], record['Availibility'], record['Review Date'],
            record['Country'], record['City'], record['Latitude'], record['Longitude']
        ))



dag = DAG(
    'etl_on_airbnb_data',
    description='A DAG to perform etl on Airbnb data from API and store it in normalized PostgreSQL tables',
    schedule_interval=None
)


scrape_airbnb_data_task = PythonOperator(
    task_id='scrape_airbnb_data',
    python_callable=scrape_airbnb_data,
    dag=dag,
)

insert_airbnb_data_task = PythonOperator(
    task_id='insert_airbnb_data',
    python_callable=insert_airbnb_data_into_postgres,
    dag=dag,
)


scrape_airbnb_data_task >> insert_airbnb_data_task
