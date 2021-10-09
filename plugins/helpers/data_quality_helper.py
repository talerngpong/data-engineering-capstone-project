from logging import Logger, error
from typing import Optional, Tuple

from airflow.providers.postgres.hooks.postgres import PostgresHook

from helpers.sql_queries import SqlQueries
from helpers.rich_query import RichQuery


class DataQualityHelper:
    @staticmethod
    def check_tables_for_non_null_columns(
        redshift_hook: PostgresHook,
        logger: Logger
    ) -> None:
        check_query: RichQuery = SqlQueries.data_quality_check_query_for_non_null_columns
        result_tuple: Optional[Tuple] = redshift_hook.get_first(
            sql=check_query.value
        )
        assert result_tuple is not None

        (number_of_null_country_code_rows, *_) = result_tuple
        assert isinstance(number_of_null_country_code_rows, int)

        if number_of_null_country_code_rows > 0:
            error_message: str = f'Country code column (in table {check_query.table_name}) ' + \
                'should not contain null value. Currently, there are ' + \
                f'{number_of_null_country_code_rows} rows coming with null value.'
            logger.error(error_message)
            raise AssertionError(error_message)

    @staticmethod
    def check_tables_for_non_negative_value_columns(
        redshift_hook: PostgresHook,
        logger: Logger
    ) -> None:
        check_query: RichQuery = SqlQueries.data_quality_check_query_for_non_negative_value_columns
        result_tuple: Optional[Tuple] = redshift_hook.get_first(
            sql=check_query.value
        )
        assert result_tuple is not None

        (number_of_neg_avg_temp_uncertainty_rows, *_) = result_tuple
        assert isinstance(number_of_neg_avg_temp_uncertainty_rows, int)

        if number_of_neg_avg_temp_uncertainty_rows > 0:
            error_message: str = 'Average temperature uncertainty column ' + \
                f'(in table {check_query.table_name}) should not contain negative value. ' + \
                f'Currently, there are {number_of_neg_avg_temp_uncertainty_rows} rows coming ' + \
                'with negative value'
            logger.error(error_message)
            raise AssertionError(error_message)
