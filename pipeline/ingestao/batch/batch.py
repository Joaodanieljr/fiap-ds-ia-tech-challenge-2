"""
Azure Spark Job - Ingestão Batch: Metas de Alfabetização
Fonte: Servidor Web / Base dos Dados (Arquivos CSV)
Destino: Azure Data Lake Gen2 (ADLS Gen2) - Camada Bronze Particionada (Ano/Mês/Dia)
"""
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from datetime import datetime

def get_args():
    args = {}
    for i in range(1, len(sys.argv), 2):
        if sys.argv[i].startswith("--"):
            args[sys.argv[i].replace("--", "")] = sys.argv[i+1]
    return args

args = get_args()
STORAGE_ACCOUNT = args.get("STORAGE_ACCOUNT", "stterraformstate") 
TABLE_NAME = args.get("TABLE_NAME") 

# Inicializa a Sessão Spark nativa
spark = SparkSession.builder \
    .appName(f"Ingestao-Bronze-CSV-{TABLE_NAME}") \
    .getOrCreate()

CONTAINER_BRONZE = "bronze"
BASE_PATH = f"abfss://{CONTAINER_BRONZE}@{STORAGE_ACCOUNT}.dfs.core.windows.net"

# Onde o servidor web dropou o arquivo original recebido
input_path = f"{BASE_PATH}/raw_landing/{TABLE_NAME}/"

# O caminho final do arquivo particionado na camada Bronze
output_path = f"{BASE_PATH}/{TABLE_NAME}/"

print(f"Lendo dados brutos em CSV de: {input_path}")

# Leitura do CSV bruto
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .option("mergeSchema", "true") \
    .option("delimiter", ",") \
    .csv(input_path)

current_date = datetime.utcnow()

# Colunas de controle e as colunas de partição
df = (
    df.withColumn("_bronze_timestamp", F.current_timestamp())
      .withColumn("ano", F.lit(current_date.strftime("%Y")))
      .withColumn("mes", F.lit(current_date.strftime("%m")))
      .withColumn("dia", F.lit(current_date.strftime("%d")))
)

print(f"Gravando dados na árvore de diretórios: {output_path}")

# Salva na camada Bronze
df.write.mode("overwrite") \
    .option("header", "true") \
    .option("delimiter", ",") \
    .partitionBy("ano", "mes", "dia") \
    .csv(output_path)
      
print(f"Escrito com sucesso! Total de registros processados: {df.count()}")