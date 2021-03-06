# Capstone Project

## Project Summary
This project aims for a data warehouse with Kimball's Bus architecture resulting in a common dimentional data model for different use cases. For now, [World Temperature Data](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data) is a data source from Kaggle and only one main use case while [Battuta](http://battuta.medunes.net/#) is a companion data source enriching dimentional common data, in this case, geocoding.

## Schema Designs
- For both context of `World Temperature Data` and `Battuta`, smallest unit of geo datum is city. Therefore, a dimentional table is named as `dim_city` with auto-generated city ID as a primary key and other columns are country, latitude and longitude.
- According to `GlobalLandTemperaturesByCity.csv`, each combination of date and city (or city ID after dimentionalized) is unique. So, a fact table standing for world temperature use case is named as `fact_temperature` with a composite primary key of date and city ID and other columns are average temperature and its uncertainty.
- For `dim_city` table, with assumption of further usage, there is an additional column, country code.

## Tool Selection
- Redshift works as a main database to serve analytical operation/aggregation. It also has an ability to serve hundreds of concurrent users.
- Airflow stands for pipeline orchestration and scheduler. This is suitable by assumption that `World Temperature Data` are updated daily (let's say at 7 AM every day).
- S3 is used as a mock data source when we cannot download/fetch data directly from original ones.

## Steps to Run This Project
1. Follow [Developing inside a Container](https://code.visualstudio.com/docs/remote/containers#_installation) until [Quick start: Open an existing folder in a container](https://code.visualstudio.com/docs/remote/containers#_quick-start-open-an-existing-folder-in-a-container) step.
2. In project root directory as working directory, start devcontainer.
   ```bash
   $ ./run_devcontainer.sh
   # OR
   $ devcontainer open .
   ```
3. In `devops` as working directory, copy `template.etl.cfg` to `etl.cfg`.
   ```bash
   # assume `devops` as working directory
   $ cp ./template.etl.cfg ./etl.cfg
   ```
4. Fill `etl.cfg` on `CLUSTER` section. This section will be used to construct Redshift cluster from scratch. We are free to choose our values. Here are possible values.
   ```cfg
   [CLUSTER]
   DB_NAME=sample-data-pipeline-db
   DB_USER=sample-db-user
   DB_PASSWORD=<choose_whatever_you_want>
   DB_PORT=5439
   CLUSTER_TYPE=multi-node
   NUM_NODES=4
   NODE_TYPE=dc2.large
   CLUSTER_IDENTIFIER=sample-data-pipeline-cluster-identifier
   IAM_ROLE_NAME=sample-data-pipeline-iam-role-name
   ```
5. Spin up Redshift cluster. This script will omit Redshift cluster metadata related to public endpoint. In this case, for example, the endpoint is `sample-data-pipeline-cluster-identifier.cryhuvsimxxx.us-west-2.redshift.amazonaws.com`.
   ```bash
   # assume `devops` as working directory
   $ python spin_up_redshift_cluster.py
   ```
   ```log
   Successfully create cluster with metadata = RedshiftClusterMetadata(endpoint='sample-data-pipeline-cluster-identifier.cryhuvsimxxx.us-west-2.redshift.amazonaws.com', role_arn='arn:aws:iam::663276196999:role/sample-data-pipeline-iam-role-name', vpc_id='vpc-9817xxx')
   ```
6. Create necessary tables.
   ```bash
   # assume `devops` as working directory
   $ python create_tables.py
   ```
7. In root project directory, follow [Running Airflow in Docker](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html) until [Running Airflow](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#running-airflow) step.
8. Put credentials to access S3 and Redshift cluster as connections.
9. Put variables of Battuta API key and S3 path (to `GlobalLandTemperaturesByCity.csv`)
10. Look for `etl_dag` DAG and toggle it on to activate the DAG.
11. When finished using Redshift cluster, tear it down.
   ```bash
   # assume `devops` as working directory
   $ python tear_down_redshift_cluster.py
   ```

## Data Quality Checks
1. `dim_city` should contains no null of country code.
2. `average_temperature_uncertainty` should be equal or more than zero.

## Data Dictionary
### Temperature Fact Table (aka `fact_temperature`)
| Column                          | Description                                            |
|---------------------------------|--------------------------------------------------------|
| date                            | Date when temperature got measured                     |
| city_id                         | Foreign key of city where temperature got measured     |
| average_temperature             | Temperature of global average land in celsius          |
| averate_temperature_uncertainty | 95% confidence interval around the average temperature |

### City Dimension Table (aka `dim_city`)
| Column       | Description                                      |
|--------------|--------------------------------------------------|
| city_id      | Primary key made from city name and country name |
| city_name    | Name of city                                     |
| country_name | Name of country where city belongs to            |
| latitude     | Latitude of city                                 |
| longitude    | Longitude of city                                |
| country_code | Code of country where city belongs to            |

### ER Diagram
![ER Diagram](/er_diagram.png)

## ETL Process Result
In order to show one sample use case of the mentioned data model, here is a result when we ask a question "Give us the first five countries having the highest average temperature(s) in September, 1st 2013".

### Query
```sql
SELECT
	DISTINCT dc.country_code,
	dc.country_name,
	ft.average_temperature
FROM fact_temperature ft
JOIN dim_city dc
ON dc.city_id = ft.city_id
WHERE ft."date" = '2013-09-01'
ORDER BY average_temperature DESC
LIMIT 5
```

### Result Set from Query
| country_code | country_name       | average_temperature |
|--------------|--------------------|---------------------|
| co           | Colombia           | 30                  |
| mx           | Mexico             | 30                  |
|              | United States      | 29                  |
| do           | Dominican Republic | 29                  |
| jm           | Jamaica            | 29                  |

### Note to Result Set
Even though we can execute the query and get the result set, we can see that there is a missing country code for country name of "United States". Therefore, this ETL pipeline will failed (see more in [Future Improvements](#future_improvements)).

## Possible Challenging Scenarios

### The data was increased by 100x.
In case of scaling up (let's say `World Temperature Data` size comes with 100 times of an original size), one file of `GlobalLandTemperaturesByCity.csv` should be split to multiple files. Those should be partitioned to have a same file size or number of rows or logically by date. Moreover, if partition by data is too fine, PySpark can split it to larger unit of `month + year`. Then, each Spark executor will process each partition separately.

### The pipelines would be run on a daily basis by 7 am every day.
Since this pipeline based on Airflow DAG, DAG allows us to declare schedule interval (of its constructor argument `schedule_interval`) as [Crontab](https://en.wikipedia.org/wiki/Cron) schedule value. Then, we can have its value as `0 7 * * *` to achieve the desired schedule.

### The database needed to be accessed by 100+ people.
According to [Amazon Redshift quotas](https://docs.aws.amazon.com/redshift/latest/mgmt/amazon-redshift-limits.html), if accesses are done in Redshift query editor v2, the editor can serve requests up to 500 connections (aka 500 users).

## <a name="future_improvements"></a> Future Improvements
- In case of missing country names discovered by data quality check, it should be one additional Airflow operator to figure those names out.
