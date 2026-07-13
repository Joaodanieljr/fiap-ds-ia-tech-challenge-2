"""
Azure Spark Job - Ingestão Batch: Metas de Alfabetização
Fonte: Servidor Web / Base dos Dados (Arquivos CSV)
Destino: Azure Data Lake Gen2 (ADLS Gen2) - Camada Bronze Particionada (Ano/Mês/Dia)

"""
import argparse
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from pipeline.ingestao.config import resolve_runtime_config, validate_runtime_config


def parse_args():
    parser = argparse.ArgumentParser(description="Ingestão batch para camada Bronze")
    parser.add_argument("--storage_account", default=None)
    parser.add_argument("--table_name", default=None)
    return parser.parse_args()


args = parse_args()
config = resolve_runtime_config({
    "storage_account": args.storage_account,
    "table_name": args.table_name,
})
config = validate_runtime_config(config, required_keys=["storage_account", "table_name"], context="batch")

STORAGE_ACCOUNT = config["storage_account"]
TABLE_NAME = config["table_name"]

spark = SparkSession.builder \
    .appName(f"Ingestao-Bronze-CSV-{TABLE_NAME}") \
    .getOrCreate()

CONTAINER_BRONZE = "bronze"
BASE_PATH = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net"
input_path = f"{BASE_PATH}/raw_landing/{TABLE_NAME}/"
output_path = f"{BASE_PATH}/{TABLE_NAME}/"

print(f"Lendo dados brutos em CSV de: {input_path}")

df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .option("mergeSchema", "true") \
    .option("delimiter", ",") \
    .csv(input_path)

current_date = datetime.utcnow()

df = (
    df.withColumn("_bronze_timestamp", F.current_timestamp())
      .withColumn("ano", F.lit(current_date.strftime("%Y")))
      .withColumn("mes", F.lit(current_date.strftime("%m")))
      .withColumn("dia", F.lit(current_date.strftime("%d")))
)

print(f"Gravando dados na árvore de diretórios: {output_path}")

df.write.mode("overwrite") \
    .option("header", "true") \
    .option("delimiter", ",") \
    .partitionBy("ano", "mes", "dia") \
    .csv(output_path)

print(f"Escrito com sucesso! Total de registros processados: {df.count()}")