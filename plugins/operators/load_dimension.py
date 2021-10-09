from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from helpers.rich_query import RichQuery, default_query


class LoadDimensionOperator(BaseOperator):
    ui_color: str = '#80BD9E'

    remove_existing_rows_from_table_query_template: str = 'TRUNCATE {table_name}'

    def __init__(
            self,
            redshift_conn_id: str = '',
            load_dim_table_query: RichQuery = default_query,
            should_remove_existing_rows: bool = False,
            *args,
            **kwargs
    ):
        super(LoadDimensionOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id: str = redshift_conn_id
        self.load_dim_table_query: RichQuery = load_dim_table_query
        self.should_remove_existing_rows: bool = should_remove_existing_rows

    def execute(self, context):
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        table_name = self.load_dim_table_query.table_name

        if self.should_remove_existing_rows:
            clean_table_query = self.remove_existing_rows_from_table_query_template.format(
                table_name=table_name)

            self.log.info(
                f'start removing existing data from table `{table_name}`')
            redshift_hook.run(sql=clean_table_query, autocommit=True)
            self.log.info(
                f'finish removing existing data from table `{table_name}`')

        self.log.info(f'start inserting data to table `{table_name}`')
        redshift_hook.run(sql=self.load_dim_table_query.value, autocommit=True)
        self.log.info(f'finish inserting data to table `{table_name}`')
