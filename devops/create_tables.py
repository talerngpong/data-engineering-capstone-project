import boto3
import psycopg2
from mypy_boto3_redshift import RedshiftClient
from psycopg2.extensions import connection, cursor

from common import EtlConfig
from common import get_static_config_instance, get_cluster_endpoint
from sql_queries import table_drop_queries, table_create_queries


def drop_tables(cur: cursor, conn: connection) -> None:
    for query in table_drop_queries:
        try:
            cur.execute(query)
            conn.commit()
        except Exception as e:
            print(f'There is an exception when executing query = {query}')
            raise e


def create_tables(cur: cursor, conn: connection) -> None:
    for query in table_create_queries:
        try:
            cur.execute(query)
            conn.commit()
        except Exception as e:
            print(f'There is an exception when executing query = {query}')
            raise e


def main() -> None:
    etl_config: EtlConfig = get_static_config_instance()
    redshift_client: RedshiftClient = boto3.client('redshift')
    cluster_endpoint = get_cluster_endpoint(
        redshift_client, etl_config=etl_config)

    # https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    conn_string = 'host={endpoint} dbname={db_name} user={db_user} password={db_password} port={db_port}'.format(
        db_user=etl_config.redshift_cluster.db_user,
        db_password=etl_config.redshift_cluster.db_password,
        endpoint=cluster_endpoint,
        db_port=etl_config.redshift_cluster.db_port,
        db_name=etl_config.redshift_cluster.db_name
    )

    with psycopg2.connect(conn_string) as conn:
        cur: cursor = conn.cursor()

        drop_tables(cur, conn)
        create_tables(cur, conn)


if __name__ == '__main__':
    main()
