"""
Simulador de Produtor - Envio das 4 Estruturas Reais de Alfabetização
Lendo chaves de forma segura através de variáveis de ambiente (.env)
"""
import os
import time
import json
import random
from datetime import datetime
from dotenv import load_dotenv
from azure.eventhub import EventHubProducerClient, EventEventData

# 1. Carrega as variáveis do arquivo .env localizado na raiz
load_dotenv()

# 2. Captura as variáveis de ambiente com tratamento de erro básico
CONNECTION_STR = os.getenv("EH_CONNECTION_STRING")
EVENTHUB_NAME = os.getenv("EVENTHUB_NAME")

if not CONNECTION_STR or not EVENTHUB_NAME:
    raise ValueError(
        "ERRO: As variáveis 'EH_CONNECTION_STRING' ou 'EVENTHUB_NAME' "
        "não foram encontradas no arquivo .env!"
    )

# --- Funções para gerar as 4 mensagens baseadas nos seus prints reais ---

def gerar_mensagem_aluno():
    return {
        "tipo_mensagem": "dados_aluno",
        "NU_ANO": 2025,
        "CO_UF": 11,
        "SG_UF": "RO",
        "ID_ALUNO": random.randint(10000000, 99999999),
        "TP_SERIE": 2,
        "ID_ESCOLA": random.randint(11000000, 11999999),
        "TP_DEPENDENCIA": random.choice([2, 3]),
        "CO_MUNICIPIO": 1100023,
        "NO_MUNICIPIO": "Ariquemes",
        "IN_PRESENCA": 1,
        "VL_PROFICIENCIA": round(random.uniform(400.0, 800.0), 3),
        "IN_ALFABETIZADO": random.choice([0, 1]),
        "timestamp_evento": datetime.utcnow().isoformat()
    }

def gerar_mensagem_indicadores():
    return {
        "tipo_mensagem": "dados_indicadores",
        "NU_ANO": 2025,
        "CO_UF": 11,
        "SG_UF": "RO",
        "TP_SERIE": 2,
        "ID_TIPO_REDE": 2,
        "PC_ALUNO_MEDIA": round(random.uniform(70.0, 85.0), 2),
        "PC_ALUNO_NIVEL_8_LP": round(random.uniform(5.0, 15.0), 2),
        "timestamp_evento": datetime.utcnow().isoformat()
    }

def gerar_mensagem_itens():
    return {
        "tipo_mensagem": "dados_itens",
        "NU_ANO": 2025,
        "CO_UF": 11,
        "SG_UF": "RO",
        "CO_BLOCO": random.choice(["4A", "6B"]),
        "NU_POSICAO": random.randint(1, 20),
        "CO_ITEM": random.randint(100, 999),
        "TP_DISCIPLINA": 1,
        "NU_DESCR_ITEM": "0.04899000000000",
        "TX_GABARITO": random.choice(["A", "B", "C", "D"]),
        "NU_PARAM_A1": round(random.uniform(0.5, 2.5), 6),
        "NU_PARAM_B1": round(random.uniform(-3.0, 3.0), 6),
        "IN_ITEM_COMUM": 0,
        "timestamp_evento": datetime.utcnow().isoformat()
    }

def gerar_mensagem_municipio():
    return {
        "tipo_mensagem": "dados_municipio",
        "NU_ANO": 2025,
        "CO_UF": 11,
        "SG_UF": "RO",
        "CO_MUNICIPIO": 1100122,
        "NO_MUNICIPIO": random.choice(["Alta Floresta", "Ariquemes", "Porto Velho"]),
        "TP_SERIE": 3,
        "VL_MEDIA": round(random.uniform(700.0, 780.0), 3),
        "timestamp_evento": datetime.utcnow().isoformat()
    }

# --- Loop Principal de Envio ---

def iniciar_streaming():
    # Inicializa o cliente do Event Hubs usando a string de conexão do .env
    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR, 
        eventhub_name=EVENTHUB_NAME
    )
    
    geradores = [gerar_mensagem_aluno, gerar_mensagem_indicadores, gerar_mensagem_itens, gerar_mensagem_municipio]
    
    print("="*60)
    print("🚀 PRODUTOR AZURE INICIADO COM SUCESSO!")
    print(f"Enviando dados para o Event Hub: {EVENTHUB_NAME}")
    print("Pressione Ctrl+C a qualquer momento para parar.")
    print("="*60)
    
    try:
        while True:
            # Cria um lote (batch) de eventos para otimizar o envio
            event_data_batch = producer.create_batch()
            
            # Escolhe aleatoriamente 3 tipos de tabelas para simular o tráfego misto
            for _ in range(3):
                funcao_geradora = random.choice(geradores)
                mensagem = funcao_geradora()
                
                # Converte o dicionário Python para string JSON
                json_string = json.dumps(mensagem)
                
                # Adiciona o JSON no lote de envio
                event_data_batch.add(EventEventData(json_string))
                print(f"📦 [{mensagem['tipo_mensagem'].upper()}] Mensagem estruturada gerada.")
                
            # Despacha o lote para a Azure
            producer.send_batch(event_data_batch)
            print("⚡ Lote enviado para a nuvem com sucesso. Aguardando 4 segundos...\n")
            
            time.sleep(4)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulação interrompida pelo usuário. Finalizando conexões...")
    finally:
        producer.close()
        print("🔒 Conexão com o Azure Event Hubs fechada.")

if __name__ == "__main__":
    iniciar_streaming()