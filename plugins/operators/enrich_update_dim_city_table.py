from typing import List, Tuple
from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from helpers.sql_queries import SqlQueries
from helpers.battuta_data_source import BattutaDataSource, Country


class EnrichUpdateDimCityTableOperator(BaseOperator):
    ui_color: str = '#80BD9E'

    def __init__(
            self,
            redshift_conn_id: str = '',
            battuta_api_key: str = '',
            *args,
            **kwargs
    ):
        super(EnrichUpdateDimCityTableOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id: str = redshift_conn_id
        self.battuta_api_key: str = battuta_api_key

    def execute(self, context):
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        battuta_data_source = BattutaDataSource(api_key=self.battuta_api_key)

        result_set_rows = redshift_hook.get_records(
            sql=SqlQueries.retrieve_distinct_country_name_query.value
        )
        country_names: List[str] = [
            country_name
            for (country_name,)
            in result_set_rows
        ]

        countries: List[Country] = battuta_data_source.get_countries()

        country_name_to_nullable_country_code_tuples = [
            (country_name, next(
                (country.code for country in countries if country.name == country_name),
                None
            ))
            for country_name
            in country_names
        ]
        country_name_to_country_code_tuples = [
            (country_name, nullable_country_code)
            for (country_name, nullable_country_code)
            in country_name_to_nullable_country_code_tuples
            if nullable_country_code is not None
        ]

        for (country_name, country_code) in country_name_to_country_code_tuples:
            redshift_hook.run(
                sql=SqlQueries.build_dim_city_table_enrich_update_query(
                    country_name=country_name,
                    country_code=country_code
                ).value,
                autocommit=True
            )
