# Tech Challenge 2 - FIAP Data Science & Analytics

Este repositório reúne uma solução de dados para o Tech Challenge 2 da FIAP, com foco em dados educacionais de alfabetização. O projeto usa uma arquitetura em camadas (Medallion) para receber, transformar e disponibilizar dados em lote e em tempo real, além de provisionar a infraestrutura básica com Terraform.

A proposta é demonstrar um fluxo completo de dados, desde a ingestão até a geração de tabelas analíticas, com foco em clareza operacional e facilidade de execução em ambientes Azure.

## Visão geral

A solução contempla:

- ingestão em lote de arquivos CSV para a camada Bronze;
- simulação local de streaming para geração e consumo de eventos;
- transformação e padronização nas camadas Prata e Ouro;
- provisionamento inicial de recursos em Azure com Terraform.

## Arquitetura do projeto

A arquitetura segue o modelo Medallion com separação entre dados brutos, dados tratados e dados analíticos.

Para detalhes sobre o modelo e os padrões adotados, consulte `doc/arquitetura/arquitetura.md`. Informações complementares de FinOps e custos operacionais estão disponíveis em `doc/finops/`.

```text
Fontes de dados
  ├── Batch -> Bronze
  └── Streaming -> Event Hubs -> Bronze

Bronze -> Prata -> Ouro
```

### Componentes principais

- Batch: leitura de arquivos CSV e gravação particionada na camada Bronze.
- Streaming: produtor envia eventos simulados localmente e o consumidor grava os payloads brutos na camada Bronze.
- Notebooks: transformações de Bronze para Prata e de Prata para Ouro.
- Infraestrutura: recursos do Azure Storage, containers e Data Factory provisionados via Terraform.

## Estrutura do repositório

```text
fiap-ds-ia-tech-challenge-2/
├── doc/
│   ├── arquitetura/
│   │   └── arquitetura.md
│   ├── finops/
│   └── uteis/
├── infra/
│   └── terraform/
│       ├── main.tf
│       └── variables.tf
├── pipeline/
│   ├── camadas/
│   │   ├── bronze/
│   │   │   └── bronze_alfabetizacao.ipynb
│   │   ├── prata/
│   │   │   └── silver_alfabetizacao.ipynb
│   │   └── ouro/
│   │       └── gold_alfabetizacao.ipynb
│   └── ingestao/
│       ├── batch/
│       │   └── batch.py
│   │   ├── stream/
│   │   │   ├── consumer.py
│   │   │   └── producer.py
│       ├── config.py
│       └── mock_support.py
├── tests/
│   ├── test_config.py
│   └── test_mock_support.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Pré-requisitos

- Python 3.10 ou superior
- Terraform 1.5 ou superior (opcional para provisionamento da infraestrutura)
- Conta e credenciais Azure para execução em nuvem
- Jupyter Notebook opcional para abrir os notebooks

## O que precisa existir no Azure antes de rodar

> Importante: o projeto não roda de forma totalmente autônoma apenas com o código. Ele depende de alguns recursos Azure já criados ou provisionados previamente.

Antes de usar o fluxo de batch e a simulação local de streaming, a pessoa precisa ter criado no Azure:

1. um Resource Group;
2. uma Storage Account com Data Lake Gen2 habilitado;
3. um container chamado bronze;
4. se for usar o batch, um caminho de entrada com um arquivo CSV para leitura.

### Checklist de criação no Azure

1. Acesse o portal Azure ou Azure CLI e crie um Resource Group.
2. Crie uma Storage Account e ative o suporte a Data Lake Gen2.
3. Dentro da Storage Account, crie o container bronze.
4. Se o batch for usado, coloque um arquivo CSV em um caminho acessível pela aplicação, por exemplo em uma pasta de entrada no Data Lake ou em um diretório local.
5. Preencha as variáveis de ambiente com os valores corretos.

O projeto espera que os nomes e valores abaixo sejam informados nas variáveis de ambiente:

- STORAGE_ACCOUNT_NAME ou o nome da Storage Account usada pelo script batch;
- TABLE_NAME com o nome da entidade/tabela processada.

Se a infraestrutura ainda não existir, o Terraform pode ser usado para provisionar a base inicial a partir de [infra/terraform/main.tf](infra/terraform/main.tf).

### Provisionamento com Terraform

Exemplo de fluxo inicial:

```bash
cd infra/terraform
terraform init
terraform plan -var="resource_group_name=rg-tech-challenge-fase2" -var="storage_account_name=seu-storage-account" -var="data_factory_name=adf-alfabetizacao-pipeline"
terraform apply -var="resource_group_name=rg-tech-challenge-fase2" -var="storage_account_name=seu-storage-account" -var="data_factory_name=adf-alfabetizacao-pipeline"
```

Depois do apply, os outputs retornam o nome do resource group, da Storage Account e do Data Factory para facilitar a configuração das variáveis do projeto.

## Configuração rápida

1. Clone o repositório.
2. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

3. Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env.example .env
```

4. Preencha as variáveis com os valores do seu ambiente.

Exemplo de conteúdo do arquivo .env para Azure:

```env
STORAGE_ACCOUNT_NAME=seu-storage-account
TABLE_NAME=alfabetizacao
```

## Variáveis de ambiente

Os valores abaixo devem ser preenchidos no arquivo .env antes de executar qualquer fluxo que dependa de Azure ou dos notebooks.

As principais variáveis esperadas são:

- STORAGE_ACCOUNT_NAME: nome da Storage Account do Azure.
- TABLE_NAME: nome da tabela/entidade processada no batch.
- KEY_VAULT_URL: URL do Azure Key Vault usado pelos notebooks para ler a chave de acesso.
- KEY_VAULT_SECRET_NAME: nome do segredo que armazena a chave da Storage Account.
- AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID: credenciais opcionais para autenticação Azure.

## Como executar

A execução pode seguir duas abordagens principais:

### Opção A: execução com Azure (ambiente real)

### 1. Ingestão batch

```bash
python pipeline/ingestao/batch/batch.py --TABLE_NAME alfabetizacao --STORAGE_ACCOUNT stterraformstate
```

O script lê um CSV bruto e grava os dados particionados na camada Bronze.

### 2. Ingestão streaming

Em dois terminais, execute:

```bash
# Terminal 1
python pipeline/ingestao/stream/consumer.py
```

```bash
# Terminal 2
python pipeline/ingestao/stream/producer.py
```

O produtor gera mensagens simuladas localmente e o consumidor lê essas mensagens e grava os payloads na camada Bronze.

### 3. Pipelines de transformação

Depois que a ingestão estiver funcionando, a ordem recomendada para execução dos notebooks é:

1. pipeline/camadas/bronze/bronze_alfabetizacao.ipynb
2. pipeline/camadas/prata/silver_alfabetizacao.ipynb
3. pipeline/camadas/ouro/gold_alfabetizacao.ipynb


### Opção B: execução sem Azure (modo mock)

Se a pessoa quiser validar a estrutura do fluxo sem depender de recursos cloud, é possível usar os helpers de mock incluídos em [pipeline/ingestao/mock_support.py](pipeline/ingestao/mock_support.py).

Exemplo:

```python
from pathlib import Path
from pipeline.ingestao.mock_support import write_mock_csv, append_mock_message

write_mock_csv(Path("tmp/mock.csv"), table_name="alfabetizacao")
append_mock_message(Path("tmp/mock_messages.jsonl"), {"tipo_mensagem": "dados_aluno", "ID_ALUNO": 123})
```

Essa opção é útil para testar a lógica de preparação de dados e a estrutura de payloads antes de conectar a ambientes Azure reais.


## Potenciais Aplicações em IA e Advanced Analytics

Com a base de dados consolidada, limpa e modelada na camada **Ouro**, o ecossistema está pronto para alimentar modelos de Inteligência Artificial e Machine Learning. A estrutura em camadas (Medallion) garante a consistência necessária para os seguintes cenários de aplicação na gestão pública:

### 1. Previsão de Risco e Alerta Precoce
* **Objetivo:** Antecipar quais municípios ou redes escolares correm o risco de não atingir as metas de alfabetização estabelecidas.
* **Abordagem Técnica:** Implementação de modelos de classificação binária ou multiclasse (como *Random Forest*, *XGBoost* ou *Regressão Logística*). Ao analisar os dados históricos e os eventos em tempo real vindos da esteira de streaming, o modelo calcula a probabilidade de inadimplência da meta, permitindo que a secretaria de educação atue de forma preventiva antes das avaliações oficiais.

### 2. Identificação de Fatores Determinantes (Interpretabilidade)
* **Objetivo:** Descobrir quais variáveis (socioeconômicas, infraestrutura escolar, frequência, etc.) mais impactam o sucesso do aprendizado.
* **Abordagem Técnica:** Utilização de algoritmos baseados em árvores e técnicas de explicabilidade global e local (como valores *SHAP* ou *Feature Importance*). Isso remove o aspecto de "caixa-preta" da IA, permitindo que os gestores entendam, por exemplo, se a falta de recursos digitais ou a rotatividade de professores é o fator de maior peso estatístico no baixo desempenho de uma determinada região.

### 3. Motores de Recomendação Pedagógica
* **Objetivo:** Gerar sugestões automáticas de planos de ação personalizados para diretores e gestores públicos.
* **Abordagem Técnica:** Sistemas de recomendação baseados em filtragem colaborativa ou baseada em conteúdo, que cruzam o perfil de municípios com desafios similares. Se um município superou um problema de alfabetização aplicando uma política "X", o sistema recomenda essa mesma política para municípios vizinhos que apresentam o mesmo comportamento de dados.

### 4. Agrupamento Sociodemográfico (Clustering)
* **Objetivo:** Agrupar municípios por similaridade real de desafios, indo além das divisões geográficas tradicionais.
* **Abordagem Técnica:** Isso permite criar "personas" de municípios (ex: *Alta vulnerabilidade socioeconômica com boa infraestrutura escolar* vs. *Baixa vulnerabilidade com falta de insumos*). Com esses clusters, o governo pode distribuir orçamentos e materiais de apoio de forma cirúrgica e justa.

### 5. Análise de Séries Temporais e Projeções de Longo Prazo
* **Objetivo:** Projetar a evolução dos índices de alfabetização para os próximos 5 ou 10 anos caso as políticas atuais sejam mantidas.
* **Abordagem Técnica:** Modelagem preditiva temporal essencial para o planejamento orçamentário anual do Estado.

### 6. Auditoria de Dados e Detecção de Anomalias
* **Objetivo:** Identificar inconsistências, fraudes ou erros de preenchimento nos censos educacionais que chegam via lote ou streaming.
* **Abordagem Técnica:** Modelos de detecção de *outliers* (como *Isolation Forests*). Se uma escola reportar uma taxa de alfabetização perfeitamente discrepante do seu histórico sem nenhuma mudança estrutural, o sistema emite um alerta para auditoria interna antes que o dado contamine os relatórios analíticos da camada Ouro.

## Checklist final antes de rodar

Antes de iniciar a execução, confirme os itens abaixo:

- [ ] Python instalado
- [ ] dependências instaladas com pip install -r requirements.txt
- [ ] arquivo .env criado e preenchido
- [ ] Resource Group criado no Azure
- [ ] Storage Account criada e container bronze disponível
- [ ] arquivo CSV disponível para o batch, se aplicável

