# Arquitetura da Solução — Plataforma de Dados Educacionais

## 1. Objetivo
O objetivo deste projeto é implementar uma plataforma de dados robusta, escalável e segura para o processamento de indicadores educacionais de alfabetização no Brasil. A solução adota o modelo de **Arquitetura Lambda Híbrida** combinada com o padrão **Medallion (Design em Camadas)** sobre a nuvem Microsoft Azure, permitindo o processamento eficiente tanto de cargas históricas massivas quanto de atualizações em tempo real.

---

## 2. Fluxo de Dados End-to-End

O ciclo de vida dos dados na plataforma está estruturado em cinco etapas principais:

```text
+---------------------------------------------------------------------------------+
|                               CAMADA DE INGESTÃO                                |
+---------------------------------------------------------------------------------+
   | (A) Carga Massiva Anual              | (B) Atualizações em Tempo Real
   v                                      v
+-----------------------+              +------------------------------------------+
|  Azure Data Factory   |              | Script Python (producer.py)              |
|          +            |              |                    |                     |
|    Script PySpark     |              |                    v                     |
|      (batch.py)       |              |             Azure Event Hubs             |
+-----------------------+              |                    |                     |
   |                                   |                    v                     |
   |                                   |         Script Python (consumer.py)      |
   +-----------------+                 +------------------+
                     |                                    |
                     v                                    v
+---------------------------------------------------------------------------------+
|               AZURE DATA LAKE STORAGE GEN2 (ARQUITETURA MEDALLION)              |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  [Camada Bronze] ------> [Camada Prata] --------------> [Camada Ouro]           |
|  Dados brutos e          Limpeza, tipagem e             Tabelas analíticas      |
|  não tratados            padronização (Schema)          agregadas para negócio  |
|  (CSVs e Payloads)       (silver_alfabetizacao.ipynb)   (gold_alfabetizacao.ipynb)
|                                                                                 |
+---------------------------------------------------------------------------------+
                                                             |
                                                             v
                                                  +----------------------+
                                                  |  CAMADA DE CONSUMO   |
                                                  +----------------------+
                                                  | Power BI / Analytics |
                                                  | Modelos de ML / IA   |
                                                  +----------------------+

```

1. **Ingestão Batch (Carga Histórica/Massiva):** O volume principal de dados consiste no fechamento anual de alfabetização das escolas brasileiras. Esse arquivo CSV volumoso é processado em lote, utilizando uma pipeline do **Azure Data Factory** que orquestra um script PySpark para garantir alta performance no particionamento e salvamento inicial.
2. **Ingestão em Streaming (Atualizações Tempestivas):** Incrementos na base de dados, correções cadastrais e novos registros são capturados via microsserviços de mensageria. Isso mitiga a necessidade de reprocessar volumes massivos anualmente e garante dados sempre atualizados.
3. **Persistência na Camada Bronze:** Centraliza o armazenamento de dados em seu estado bruto (*raw*), preservando o histórico imutável tanto dos CSVs do Batch quanto dos payloads JSON recuperados do streaming.
4. **Transformação na Camada Prata:** Realiza a limpeza de strings, eliminação de duplicidades, coerção de tipos de dados (*data typing*) e aplicação de esquemas padronizados, consolidando as fontes de lote e tempo real em um formato unificado e otimizado.
5. **Enriquecimento na Camada Ouro:** Consolida regras de negócio, agregações analíticas e cruzamentos necessários para gerar tabelas prontas para consumo de relatórios e inteligência artificial.

---

## 3. Matriz de Componentes e Tecnologias

A tabela abaixo descreve o ecossistema tecnológico adotado e a respectiva justificativa técnica de cada componente na solução:

| Componente | Tecnologia | Função na Arquitetura | Justificativa Técnica |
| --- | --- | --- | --- |
| **Ingestão Batch** | Python + PySpark | Leitura e particionamento dos CSVs anuais de grande porte. | O PySpark distribui o processamento na leitura de arquivos massivos, evitando gargalos de memória comuns no Pandas tradicional. |
| **Orquestração Batch** | Azure Data Factory | Agendamento e gerenciamento do fluxo do script de lote. | Permite criar gatilhos (*triggers*) baseados em eventos e monitorar falhas operacionalmente na nuvem. |
| **Ingestão Stream** | Python (`producer.py` / `consumer.py`) | Simulação, envio e consumo de eventos em tempo real. | Estrutura modular que desacopla a origem produtora da lógica de persistência de dados. |
| **Mensageria** | Azure Event Hubs | Barramento de eventos de alta escala para ingestão de streaming. | Serviço gerenciado nativo da Azure capaz de receber milhões de eventos por segundo com baixa latência. |
| **Transformações** | Jupyter Notebooks (`.ipynb`) | Desenvolvimento da lógica de limpeza (Prata) e agregação (Ouro). | Facilita a prototipagem rápida, análise exploratória e documentação visual das regras de negócio aplicadas. |
| **Armazenamento** | Azure Data Lake Storage Gen2 (ADLS) | Repositório centralizado (*Data Lake*) organizado em modelo Medallion. | Fornece armazenamento hierárquico compatível com drivers de Big Data (Blob + recursos de sistema de arquivos), com baixo custo e alta segurança. |
| **Segurança** | Azure Key Vault | Gerenciamento centralizado de segredos, chaves e strings de conexão. | Evita a exposição de credenciais confidenciais no código-fonte (*hardcoded secrets*), em conformidade com as diretrizes da LGPD. |
| **Infraestrutura** | Terraform | Provisionamento declarativo de recursos da nuvem (*Infrastructure as Code*). | Garante a reprodutibilidade exata do ambiente Azure, facilidade de destruição e consistência entre execuções. |

---

## 4. Próximos Passos e Oportunidades de Melhoria

Para evoluir a maturidade desta plataforma de dados de um estágio de MVP (*Minimum Viable Product*) para um ambiente corporativo resiliente (*Enterprise Ready*), mapeamos os seguintes pontos de melhoria:

* **Infraestrutura como Código Completa (IaC Expandida):** Incluir de forma explícita as definições do *Azure Event Hubs* e do *Azure Data Factory* nos arquivos declarativos do Terraform (`main.tf`), garantindo que 100% do ecossistema de nuvem seja provisionado via código sem intervenções manuais no portal.
* **Governança de Dados e Catálogo de Esquemas:** Implementar um catálogo de dados (ex: *Azure Purview*) e um *Schema Registry* na camada de streaming. Isso garante a governança sobre a evolução do layout das mensagens e impede que dados corrompidos quebrem as pipelines (*data contract*).
* **Segregação Estrita de Ambientes:** Expandir a estrutura do projeto para isolar completamente os ambientes de Desenvolvimento (DEV), Homologação/Testes (QA) e Produção (PROD) usando workspaces do Terraform e gerando parametrizações distintas de permissão de acesso.
