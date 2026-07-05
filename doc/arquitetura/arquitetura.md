# Arquitetura da solução

## Objetivo

O projeto implementa um fluxo de dados educacionais com ingestão batch e streaming, transformações em camadas e armazenamento em Azure Data Lake Storage Gen2.

## Fluxo principal

1. Dados chegam por ingestão batch ou streaming.
2. A camada Bronze armazena os dados brutos e não tratados.
3. A camada Prata aplica limpeza, tipagem e padronização.
4. A camada Ouro entrega tabelas analíticas agregadas.

## Componentes

- Ingestão batch: script Python com PySpark para ler CSVs e gravar particionado na camada Bronze.
- Ingestão streaming: produtor envia eventos simulados para Azure Event Hubs e o consumidor grava os payloads na Bronze.
- Transformação: notebooks para executar a lógica de negócios e gerar dados prontos para consumo.
- Infraestrutura: Terraform provisiona o resource group, storage account, containers e recursos base do Data Lake.

## Pontos de melhoria

- adicionar Event Hubs e Data Factory como recursos Terraform explícitos;
- incluir um catálogo de dados ou schema registry;
- separar melhor os ambientes de desenvolvimento e produção.
