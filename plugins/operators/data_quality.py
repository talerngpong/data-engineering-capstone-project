from logging import Logger
from typing import Callable

from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class DataQualityOperator(BaseOperator):
    ui_color: str = '#89DA59'

    def __init__(
            self,
            redshift_conn_id: str = '',
            data_quality_checker: Callable[[
                PostgresHook, Logger], None] = lambda _: None,
            *args,
            **kwargs
    ):
        super(DataQualityOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id: str = redshift_conn_id
        self.data_quality_checker: Callable[[
            PostgresHook, Logger], None] = data_quality_checker

    def execute(self, context):
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        self.data_quality_checker(redshift_hook, self.log)
