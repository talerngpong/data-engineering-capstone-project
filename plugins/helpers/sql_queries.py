from typing import Callable, List

from helpers.aws_credentials import AwsCredentials
from helpers.rich_query import RichQuery


class SqlQueries:
    # INSERT-related queries
    dim_city_table_initial_insert_query = RichQuery(
        value='''
            INSERT INTO dim_city (
                city_id,
                city_name,
                country_name,
                latitude,
                longitude
            )
            SELECT
                DISTINCT MD5(City || Country) AS city_id,
                City AS city_name,
                Country AS country_name,
                Latitude AS latitude,
                Longitude AS longitude
            FROM staging_global_land_temperature_by_city
            WHERE COALESCE(City, '') <> ''
            AND COALESCE(Country, '') <> ''
        ''',
        table_name='dim_city'
    )
    fact_temperature_insert_query = RichQuery(
        value='''
            INSERT INTO fact_temperature (
                "date",
                city_id,
                average_temperature,
                average_temperature_uncertainty
            )
            SELECT
                DISTINCT CAST(stg.dt AS DATE) AS "date",
                dc.city_id,
                CAST(stg.AverageTemperature AS NUMERIC) AS average_temperature,
                CAST(stg.AverageTemperatureUncertainty AS NUMERIC) AS average_temperature_uncertainty
            FROM staging_global_land_temperature_by_city AS stg
            JOIN dim_city AS dc
            ON (dc.city_name = stg.City AND dc.country_name = stg.Country)
            WHERE COALESCE(stg.dt, '') SIMILAR TO '[0-9]{4}-[0-9]{2}-[0-9]{2}'
            AND COALESCE(stg.AverageTemperature, '') <> ''
            AND COALESCE(stg.AverageTemperatureUncertainty, '') <> ''
            AND COALESCE(stg.City, '') <> ''
            AND COALESCE(stg.Country, '') <> ''
        ''',
        table_name='fact_temperature'
    )

    retrieve_distinct_country_name_query = RichQuery(
        value='''
            SELECT
                DISTINCT country_name
            FROM
                dim_city
        ''',
        table_name='dim_city'
    )

    @staticmethod
    def build_dim_city_table_enrich_update_query(
        country_name: str,
        country_code: str
    ) -> RichQuery:
        return RichQuery(
            value='''
                UPDATE dim_city
                SET country_code='{country_code}'
                WHERE country_name='{country_name}'
            '''.format(
                country_name=country_name,
                country_code=country_code
            ),
            table_name='dim_city'
        )

    # COPY-related queries
    @staticmethod
    def build_staging_global_land_temperature_by_city(
        s3_data_set_source_path: str
    ) -> Callable[[AwsCredentials], RichQuery]:
        table_name = 'staging_global_land_temperature_by_city'

        return lambda aws_credentials: RichQuery(
            value='''
                COPY {table_name}
                FROM '{s3_data_set_source_path}'
                ACCESS_KEY_ID '{aws_access_key_id}'
                SECRET_ACCESS_KEY '{aws_secret_access_key}'
                DELIMITER ','
            '''.format(
                table_name=table_name,
                s3_data_set_source_path=s3_data_set_source_path,
                aws_access_key_id=aws_credentials.access_key_id,
                aws_secret_access_key=aws_credentials.secret_access_key
            ),
            table_name=table_name
        )

    data_quality_check_query_for_non_null_columns: RichQuery = RichQuery(
        value='''
            SELECT
                SUM(CASE
                    WHEN country_code IS NULL THEN 1
                    ELSE 0
                END) AS number_of_null_country_code_rows,
                SUM(CASE
                    WHEN country_code IS NOT NULL THEN 1
                    ELSE 0
                END) AS number_of_non_null_country_code_rows,
                COUNT(*) AS number_of_rows
            FROM
                dim_city
        ''',
        table_name='dim_city'
    )
    data_quality_check_query_for_non_negative_value_columns: RichQuery = RichQuery(
        value='''
            SELECT
                SUM(CASE
                    WHEN average_temperature_uncertainty < 0 THEN 1
                    ELSE 0
                END) AS number_of_neg_avg_temp_uncertainty_rows,
                SUM(CASE
                    WHEN average_temperature_uncertainty >= 0 THEN 1
                    ELSE 0
                END) AS number_of_zero_or_pos_avg_temp_uncertainty_rows,
                COUNT(*) AS number_of_rows
            FROM
                fact_temperature
        ''',
        table_name='fact_temperature'
    )
