"""
Azure Spark Job - Consumidor Streaming (Event Hubs -> Bronze JSON)
Suporta leitura local via .env ou execução na nuvem via parâmetros do ADF
"""
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from dotenv import load_dotenv

# 1. Carrega o arquivo .env (caso esteja rodando localmente)
load_dotenv()

def get_args():
    args = {}
    for i in range(1, len(sys.argv), 2):
        if sys.argv[i].startswith("--"):
            args[sys.argv[i].replace("--", "")] = sys.argv[i+1]
    return args

args = get_args()

# Se não vier via argumento do ADF (sys.argv), ele busca do arquivo .env ou assume o padrão
STORAGE_ACCOUNT = args.get("STORAGE_ACCOUNT", os.getenv("STORAGE_ACCOUNT_NAME", "stterraformstate"))
EH_CONNECTION_STRING = args.get("EH_CONNECTION_STRING", os.getenv("EH_CONNECTION_STRING"))

if not EH_CONNECTION_STRING:
    raise ValueError(
        "ERRO: A string de conexão do Event Hubs não foi encontrada! "
        "Verifique o arquivo .env ou o parâmetro --EH_CONNECTION_STRING."
    )

# Inicializa a Sessão Spark
spark = SparkSession.builder \
    .appName("Streaming-Bronze-Consumidor-4-Tabelas") \
    .getOrCreate()

# Configura a conexão com o Event Hubs
eh_conf = {
    "eventhubs.connectionString": spark._jvm.org.apache.spark.eventhubs.EventHubsUtils.encryptConnectionString(EH_CONNECTION_STRING)
}

print(f"🔄 Iniciando consumo de streaming da Azure...")
print(f"📦 Destino: Storage Account [{STORAGE_ACCOUNT}]")

# 1. Inicia a leitura do fluxo em tempo real
df_raw_stream = spark.readStream \
    .format("eventhubs") \
    .options(**eh_conf) \
    .load()

# 2. Converte o binário recebido para string JSON
df_string_stream = df_raw_stream.withColumn("json_payload", F.col("body").cast("string"))

# 3. Extrai o tipo da mensagem e cria as colunas de partição temporal (ano, mes, dia)
df_final_stream = df_string_stream \
    .withColumn("tipo_mensagem", F.get_json_object(F.col("json_payload"), "$.tipo_mensagem")) \
    .withColumn("_raw_data", F.col("json_payload")) \
    .withColumn("_bronze_timestamp", F.current_timestamp()) \
    .withColumn("ano", F.date_format(F.current_timestamp(), "yyyy")) \
    .withColumn("mes", F.date_format(F.current_timestamp(), "MM")) \
    .withColumn("dia", F.date_format(F.current_timestamp(), "dd"))

# 4. Definição dos caminhos no Data Lake Gen2
CONTAINER_BRONZE = "bronze"
output_path = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net/streaming_ingest/"
checkpoint_path = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net/checkpoints/streaming_ingest/"

# 5. Escrita contínua aplicando o particionamento solicitado
query = df_final_stream.writeStream \
    .format("json") \
    .outputMode("append") \
    .option("checkpointLocation", checkpoint_path) \
    .partitionBy("tipo_mensagem", "ano", "mes", "dia") \
    .start(output_path)

# Mantém o processo escutando a fila ativamente
query.awaitTermination()