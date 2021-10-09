import configparser
from configparser import ConfigParser
from dataclasses import dataclass

import boto3
from mypy_boto3_redshift import RedshiftClient
from mypy_boto3_redshift.type_defs import ClusterTypeDef


@dataclass
class RedshiftCluster:
    db_name: str
    db_user: str
    db_password: str
    db_port: int
    cluster_type: str
    num_nodes: int
    node_type: str
    cluster_identifier: str
    iam_role_name: str


@dataclass
class EtlConfig:
    region_name: str
    redshift_cluster: RedshiftCluster


def get_static_config_instance() -> EtlConfig:
    region_name = boto3.session.Session().region_name

    config: ConfigParser = configparser.ConfigParser()
    config.read('etl.cfg')

    redshift_cluster = RedshiftCluster(
        db_name=config['CLUSTER'].get('DB_NAME'),
        db_user=config['CLUSTER'].get('DB_USER'),
        db_password=config['CLUSTER'].get('DB_PASSWORD'),
        db_port=config['CLUSTER'].getint('DB_PORT'),
        cluster_type=config['CLUSTER'].get('CLUSTER_TYPE'),
        num_nodes=config['CLUSTER'].getint('NUM_NODES'),
        node_type=config['CLUSTER'].get('NODE_TYPE'),
        cluster_identifier=config['CLUSTER'].get('CLUSTER_IDENTIFIER'),
        iam_role_name=config['CLUSTER'].get('IAM_ROLE_NAME')
    )

    return EtlConfig(
        region_name=region_name,
        redshift_cluster=redshift_cluster
    )


def get_cluster_endpoint(redshift_client: RedshiftClient, etl_config: EtlConfig) -> str:
    cluster_props: ClusterTypeDef = redshift_client.describe_clusters(
        ClusterIdentifier=etl_config.redshift_cluster.cluster_identifier
    )['Clusters'][0]

    return cluster_props['Endpoint']['Address']
