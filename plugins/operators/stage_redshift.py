from typing import Callable

from airflow.models import BaseOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

from helpers.aws_credentials import AwsCredentials
from helpers.rich_query import RichQuery, default_query


class StageToRedshiftOperator(BaseOperator):
    ui_color: str = '#358140'

    def __init__(
            self,
            redshift_conn_id: str = '',
            s3_conn_id: str = '',
            query_builder: Callable[[AwsCredentials],
                                    RichQuery] = lambda _: default_query,
            *args,
            **kwargs
    ):
        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id: str = redshift_conn_id
        self.s3_conn_id: str = s3_conn_id
        self.query_builder: Callable[[
            AwsCredentials], RichQuery] = query_builder

    def execute(self, context: any) -> None:
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        s3_hook = S3Hook(aws_conn_id=self.s3_conn_id)
        aws_access_key_id: str = s3_hook.get_credentials().access_key
        aww_secret_access_key: str = s3_hook.get_credentials().secret_key
        query = self.query_builder(AwsCredentials(
            access_key_id=aws_access_key_id,
            secret_access_key=aww_secret_access_key
        ))
        self.log.info(f'start staging data to table `{query.table_name}`')
        redshift_hook.run(sql=query.value, autocommit=True)
        self.log.info(f'finish staging data to table `{query.table_name}`')
