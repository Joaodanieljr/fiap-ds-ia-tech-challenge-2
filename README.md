# Tech Challenge 2 - FIAP Data Science & Analytics

Este repositório reúne uma solução de dados para o Tech Challenge 2 da FIAP, com foco em dados educacionais de alfabetização. O projeto usa uma arquitetura em camadas (Medallion) para receber, transformar e disponibilizar dados em lote e em tempo real, além de provisionar a infraestrutura básica com Terraform.

## Visão geral

A proposta da solução é demonstrar um fluxo completo de dados com:

- ingestão em lote de arquivos CSV para a camada Bronze;
- ingestão em streaming com Azure Event Hubs;
- transformação e padronização nas camadas Prata e Ouro;
- provisionamento inicial de recursos em Azure com Terraform.

## Arquitetura do projeto

A arquitetura segue o modelo Medallion com separação entre dados brutos, dados tratados e dados analíticos.

```text
Fontes de dados
  ├── Batch -> Bronze
  └── Streaming -> Event Hubs -> Bronze

Bronze -> Prata -> Ouro
```

### Componentes principais

- Batch: leitura de arquivos CSV e gravação particionada na camada Bronze.
- Streaming: produtor envia eventos simulados para o Event Hub e o consumidor grava os payloads brutos na camada Bronze.
- Notebooks: transformações de Bronze para Prata e de Prata para Ouro.
- Infraestrutura: recursos do Azure Storage, containers e Data Factory provisionados via Terraform.

## Estrutura do repositório

```text
fiap-ds-ia-tech-challenge-2/
├── doc/
│   └── arquitetura/
│       └── arquitetura.md
├── infra/
│   └── terraform/
│       ├── main.tf
│       └── variables.tf
├── pipeline/
│   ├── camadas/
│   │   ├── bronze/
│   │   ├── prata/
│   │   └── ouro/
│   └── ingestao/
│       ├── batch/
│       └── stream/
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

Antes de usar os fluxos de batch ou streaming, a pessoa precisa ter criado no Azure:

1. um Resource Group;
2. uma Storage Account com Data Lake Gen2 habilitado;
3. um container chamado bronze;
4. um Event Hub Namespace e um Event Hub;
5. uma connection string com permissão de envio/recebimento no Event Hub;
6. se for usar o batch, um caminho de entrada com um arquivo CSV para leitura.

### Checklist de criação no Azure

1. Acesse o portal Azure ou Azure CLI e crie um Resource Group.
2. Crie uma Storage Account e ative o suporte a Data Lake Gen2.
3. Dentro da Storage Account, crie o container bronze.
4. Crie um Event Hub Namespace e, dentro dele, um Event Hub.
5. Gere ou copie a connection string do Event Hub com permissões para Send e Listen.
6. Se o batch for usado, coloque um arquivo CSV em um caminho acessível pela aplicação, por exemplo em uma pasta de entrada no Data Lake ou em um diretório local.
7. Preencha as variáveis de ambiente com os valores corretos.

O projeto espera que os nomes e valores abaixo sejam informados nas variáveis de ambiente:

- STORAGE_ACCOUNT_NAME ou o nome da Storage Account usada pelo script batch;
- EH_CONNECTION_STRING com a connection string do Event Hub;
- EVENTHUB_NAME com o nome do Event Hub;
- TABLE_NAME com o nome da entidade/tabela processada.

Se a infraestrutura ainda não existir, o Terraform pode ser usado para provisionar a base inicial a partir de [infra/terraform/main.tf](infra/terraform/main.tf).

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
EH_CONNECTION_STRING=Endpoint=sb://seu-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=sua-chave
EVENTHUB_NAME=seu-event-hub
TABLE_NAME=alfabetizacao
```

## Variáveis de ambiente

As principais variáveis esperadas são:

- STORAGE_ACCOUNT_NAME: nome da Storage Account do Azure.
- EH_CONNECTION_STRING: string de conexão do Azure Event Hubs.
- EVENTHUB_NAME: nome do Event Hub utilizado pelo producer/consumer.
- TABLE_NAME: nome da tabela/entidade processada no batch.
- AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID: credenciais opcionais para autenticação Azure.

## Como executar

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

O produtor gera mensagens simuladas e o consumidor lê essas mensagens e grava os payloads na camada Bronze.

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

## Checklist final antes de rodar

- [ ] Python instalado
- [ ] dependências instaladas com pip install -r requirements.txt
- [ ] arquivo .env criado e preenchido
- [ ] Resource Group criado no Azure
- [ ] Storage Account criada e container bronze disponível
- [ ] Event Hub Namespace e Event Hub criados
- [ ] connection string configurada
- [ ] arquivo CSV disponível para o batch, se aplicável

