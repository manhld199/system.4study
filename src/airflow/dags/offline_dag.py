# Set environment
import sys, os

sys.path.append(os.path.abspath("."))

# Import libs
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import custom modules
from process.preprocess import preprocess_csv
from process.build_graph import build_graph
from process.train_model import train_cbf, train_cf, train_fm
from process.compare_model import compare_model

default_args = {
	'owner':'Group1',
	'start_date': datetime(2024, 12, 7, 10, 0),
	'retries': 5,
  'retry_delay': timedelta(minutes=10),
}

with DAG(
	dag_id='offline_dag_ldm2',
	default_args=default_args,
	schedule_interval='@daily'
) as dag:
  data_preprocessing=PythonOperator(
    task_id='data_processing',
    python_callable=preprocess_csv,
    op_kwargs={
      'input_path': "/opt/airflow/data/raw",
      'output_path': "/opt/airflow/data/preprocessed",
    }
  )

  graph_building=PythonOperator(
    task_id='graph_building',
    python_callable=build_graph,
    op_kwargs={
      'input_path': "/opt/airflow/data/raw",
      'output_path': "/opt/airflow/data/graph",
    }
  )

  # cf_training=PythonOperator(
  #   task_id='cf_training',
  #   python_callable=train_cf,
  #   op_kwargs={
  #     'graph_path': "/opt/airflow/data/graph/graph.gexf",
  #     'model_path': "/opt/airflow/data/models"
  #   }
  # )

  cbf_training=PythonOperator(
    task_id='cbf_training',
    python_callable=train_cbf,
    op_kwargs={
      'graph_path': "/opt/airflow/data/graph/graph.gexf",
      'model_path': "/opt/airflow/data/models"
    }
  )

  fm_training=PythonOperator(
    task_id='fm_training',
    python_callable=train_fm,
    op_kwargs={
      'graph_path': "/opt/airflow/data/graph/graph.gexf",
      'model_path': "/opt/airflow/data/models"
    }
  )

  model_comparing=PythonOperator(
    task_id='model_comparing',
    python_callable=compare_model,
    op_kwargs={
      "test_path": "/opt/airflow/data/preprocessed/test-user.csv",
      'model_path': "/opt/airflow/data/models",
      'graph_path': "/opt/airflow/data/graph/graph.gexf"
    }
  )

  data_preprocessing >> graph_building  \
  >> cbf_training >> fm_training \
  >> model_comparing