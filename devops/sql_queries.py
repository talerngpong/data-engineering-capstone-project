# DROP-related queries
staging_global_land_temperature_by_city_table_drop_query: str = '''
    DROP TABLE IF EXISTS staging_global_land_temperature_by_city
'''
dim_city_table_drop_query: str = '''
    DROP TABLE IF EXISTS dim_city
'''
fact_temperature_table_drop_query: str = '''
    DROP TABLE IF EXISTS fact_temperature
'''

# CREATE-TABLE-related queries
staging_global_land_temperature_by_city_table_create_query: str = '''
    CREATE TABLE staging_global_land_temperature_by_city (
        dt                            TEXT    NULL,
        AverageTemperature            TEXT    NULL,
        AverageTemperatureUncertainty TEXT    NULL,
        City                          TEXT    NULL,
        Country                       TEXT    NULL,
        Latitude                      TEXT    NULL,
        Longitude                     TEXT    NULL
    )
'''
dim_city_table_create_query: str = '''
    CREATE TABLE dim_city (
        city_id      TEXT NOT NULL,
        city_name    TEXT NOT NULL,
        country_name TEXT NOT NULL,
        latitude     TEXT NOT NULL,
        longitude    TEXT NOT NULL,
        country_code TEXT NULL,
        PRIMARY KEY (city_id)
    )
'''
fact_temperature_table_create_query: str = '''
    CREATE TABLE fact_temperature (
        "date" DATE NOT NULL,
        city_id TEXT NOT NULL,
        average_temperature NUMERIC NOT NULL,
        average_temperature_uncertainty NUMERIC NOT NULL,
        PRIMARY KEY (date, city_id),
        FOREIGN KEY (city_id) REFERENCES dim_city (city_id)
    )
'''

table_drop_queries = [
    fact_temperature_table_drop_query,
    dim_city_table_drop_query,
    staging_global_land_temperature_by_city_table_drop_query
]

table_create_queries = [
    staging_global_land_temperature_by_city_table_create_query,
    dim_city_table_create_query,
    fact_temperature_table_create_query
]
