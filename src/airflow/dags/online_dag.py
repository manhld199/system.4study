# Set environment
import sys, os
sys.path.append(os.path.abspath("."))

# Import libs
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import custom modules
from process.produce_kafka import produce_data
from process.consume_kafka import stream_data, consume_data

default_args = {
	'owner':'Group1',
	'start_date': datetime(2024, 12, 7, 10, 0),
	'retries': 5,
  'retry_delay': timedelta(minutes=10),
}

with DAG(
	dag_id='online_dag4',
	default_args=default_args,
	schedule_interval='@daily'
) as dag:
  data_producing=PythonOperator(
    task_id='data_producing',
    python_callable=produce_data,
    op_kwargs={
      'topic_name': "4study_users",
    }
  )

  data_streaming=PythonOperator(
    task_id='data_streaming',
    python_callable=stream_data,
    op_kwargs={
      'in_topic_name': "4study_users",
      'out_topic_name': "recommended_users",
      'model_path': "/opt/airflow/data/models",
      'graph_path': "/opt/airflow/data/graph/graph.gexf"
    }
  )

  data_consuming=PythonOperator(
      task_id='data_consuming',
      python_callable=consume_data,
      op_kwargs={
        'topic_name': "recommended_users",
      }
    )

  [
    data_producing,
    data_streaming,
    data_consuming
  ]