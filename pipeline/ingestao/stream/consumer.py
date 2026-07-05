"""
Azure Spark Job - Consumidor Streaming (Event Hubs -> Bronze JSON)
"""
import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from dotenv import load_dotenv

from pipeline.ingestao.config import resolve_runtime_config, validate_runtime_config

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="Consumidor streaming para Event Hubs")
    parser.add_argument("--storage_account", default=None)
    parser.add_argument("--eventhub_connection_string", default=None)
    parser.add_argument("--eventhub_name", default=None)
    return parser.parse_args()


args = parse_args()
config = resolve_runtime_config({
    "storage_account": args.storage_account,
    "eventhub_connection_string": args.eventhub_connection_string,
    "eventhub_name": args.eventhub_name,
})
config = validate_runtime_config(
    config,
    required_keys=["storage_account", "eventhub_connection_string"],
    context="streaming consumer",
)

STORAGE_ACCOUNT = config["storage_account"]
EH_CONNECTION_STRING = config["eventhub_connection_string"]

spark = SparkSession.builder \
    .appName("Streaming-Bronze-Consumidor-4-Tabelas") \
    .getOrCreate()

# Configura a conexão com o Event Hubs
eh_conf = {
    "eventhubs.connectionString": spark._jvm.org.apache.spark.eventhubs.EventHubsUtils.encryptConnectionString(EH_CONNECTION_STRING)
}

print(f"🔄 Iniciando consumo de streaming da Azure...")
print(f"📦 Destino: Storage Account [{STORAGE_ACCOUNT}]")

df_raw_stream = spark.readStream \
    .format("eventhubs") \
    .options(**eh_conf) \
    .load()

df_string_stream = df_raw_stream.withColumn("json_payload", F.col("body").cast("string"))

df_final_stream = df_string_stream \
    .withColumn("tipo_mensagem", F.get_json_object(F.col("json_payload"), "$.tipo_mensagem")) \
    .withColumn("_raw_data", F.col("json_payload")) \
    .withColumn("_bronze_timestamp", F.current_timestamp()) \
    .withColumn("ano", F.date_format(F.current_timestamp(), "yyyy")) \
    .withColumn("mes", F.date_format(F.current_timestamp(), "MM")) \
    .withColumn("dia", F.date_format(F.current_timestamp(), "dd"))

CONTAINER_BRONZE = "bronze"
output_path = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net/streaming_ingest/"
checkpoint_path = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net/checkpoints/streaming_ingest/"

df_bronze_clean = df_final_stream.select("_raw_data", "tipo_mensagem", "ano", "mes", "dia")

query = df_bronze_clean.writeStream \
    .format("json") \
    .outputMode("append") \
    .option("checkpointLocation", checkpoint_path) \
    .partitionBy("tipo_mensagem", "ano", "mes", "dia") \
    .start(output_path)

query.awaitTermination()