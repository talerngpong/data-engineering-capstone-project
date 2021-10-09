from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from helpers.rich_query import RichQuery, default_query


class LoadFactOperator(BaseOperator):
    ui_color: str = '#F98866'

    def __init__(
            self,
            redshift_conn_id: str = '',
            load_fact_table_query: RichQuery = default_query,
            *args,
            **kwargs
    ):
        super(LoadFactOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id: str = redshift_conn_id
        self.load_fact_table_query: RichQuery = load_fact_table_query

    def execute(self, context: any):
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        table_name = self.load_fact_table_query.table_name

        self.log.info(f'start inserting data to table `{table_name}`')
        redshift_hook.run(
            sql=self.load_fact_table_query.value, autocommit=True)
        self.log.info(f'finish inserting data to table `{table_name}`')
