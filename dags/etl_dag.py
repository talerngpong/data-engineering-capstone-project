from datetime import datetime, timedelta
from typing import Dict

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable

from helpers import SqlQueries, DataQualityHelper
from operators import (
    DataQualityOperator,
    LoadDimensionOperator,
    LoadFactOperator,
    StageToRedshiftOperator,
    EnrichUpdateDimCityTableOperator
)

default_args: Dict = {
    'owner': 'sample-owner',
    'depends_on_past': False,
    'start_date': datetime(2019, 1, 12),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'email_on_retry': False,
}

with DAG(
    dag_id='etl_dag',
    default_args=default_args,
    description='Extract, load and transform data in Redshift with Airflow',
    schedule_interval='0 7 * * *'
) as dag:
    redshift_conn_id: str = 'sample-data-pipeline-redshift-cluster'
    s3_conn_id: str = 'sample-data-pipeline-s3'
    battuta_api_key: str = Variable.get('battuta_api_key')
    staging_global_land_temperature_by_city_s3_source_path: str = Variable.get(
        'staging_global_land_temperature_by_city_s3_source_path'
    )

    begin_execution_task = DummyOperator(task_id='begin_execution', dag=dag)
    start_data_quality_task = DummyOperator(
        task_id='start_data_quality',
        dag=dag
    )
    end_execution_task = DummyOperator(task_id='end_execution', dag=dag)

    stage_global_land_temperature_by_city_to_redshift_task = StageToRedshiftOperator(
        task_id='stage_global_land_temperature_by_city_to_redshift',
        redshift_conn_id=redshift_conn_id,
        s3_conn_id=s3_conn_id,
        query_builder=SqlQueries.build_staging_global_land_temperature_by_city(
            s3_data_set_source_path=staging_global_land_temperature_by_city_s3_source_path
        )
    )
    load_initial_dim_city_table_task = LoadDimensionOperator(
        task_id='load_initial_dim_city_table',
        redshift_conn_id=redshift_conn_id,
        load_dim_table_query=SqlQueries.dim_city_table_initial_insert_query
    )
    enrich_update_dim_city_table_task = EnrichUpdateDimCityTableOperator(
        task_id='enrich_update_dim_city_table',
        redshift_conn_id=redshift_conn_id,
        battuta_api_key=battuta_api_key
    )
    load_fact_temperature_table_task = LoadFactOperator(
        task_id='load_fact_temperature_table',
        redshift_conn_id=redshift_conn_id,
        load_fact_table_query=SqlQueries.fact_temperature_insert_query
    )

    data_quality_for_non_null_columns_task = DataQualityOperator(
        task_id='data_quality_for_non_null_columns',
        redshift_conn_id=redshift_conn_id,
        data_quality_checker=DataQualityHelper.check_tables_for_non_null_columns
    )
    data_quality_for_non_negative_value_columns_task = DataQualityOperator(
        task_id='data_quality_for_positive_value_columns',
        redshift_conn_id=redshift_conn_id,
        data_quality_checker=DataQualityHelper.check_tables_for_non_negative_value_columns
    )

    begin_execution_task >> stage_global_land_temperature_by_city_to_redshift_task
    stage_global_land_temperature_by_city_to_redshift_task >> load_initial_dim_city_table_task
    load_initial_dim_city_table_task >> enrich_update_dim_city_table_task
    enrich_update_dim_city_table_task >> load_fact_temperature_table_task
    load_fact_temperature_table_task >> start_data_quality_task

    start_data_quality_task >> data_quality_for_non_null_columns_task
    start_data_quality_task >> data_quality_for_non_negative_value_columns_task

    data_quality_for_non_null_columns_task >> end_execution_task
    data_quality_for_non_negative_value_columns_task >> end_execution_task
