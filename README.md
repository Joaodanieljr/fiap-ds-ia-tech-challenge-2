# Tech Challenge — Fase 2 · Pipeline Híbrida de Dados de Alfabetização

Solução de engenharia de dados para o Tech Challenge 2 (FIAP Pós-Tech), construída sobre dados educacionais de alfabetização infantil no Brasil. O projeto implementa uma **pipeline híbrida (batch + streaming)** em **arquitetura Medalhão** na Azure, do dado bruto até a camada analítica consumida por dashboard em Power BI.

**Equipe:** Vinicius Moreira · João Daniel · Samara Siqueira

---

## 1. Contexto do problema

O Brasil acompanha a alfabetização na idade certa por meio do **Indicador Criança Alfabetizada** (Compromisso Nacional Criança Alfabetizada). Cada município e estado possui metas pactuadas de alfabetização até 2030, comparadas anualmente com os resultados reais das avaliações estaduais (AEEB/INEP).

Este projeto integra essas fontes em uma pipeline única, permitindo responder perguntas como: *quais estados superaram suas metas? Onde o gap é maior? Qual a proficiência média dos alunos avaliados por município?*

## 2. Fontes de dados

O desafio exige a integração de 6 entidades, obtidas de duas origens públicas:

| Entidade | Origem | Formato |
|---|---|---|
| UF | Base dos Dados (`br_inep_avaliacao_alfabetizacao`) | CSV |
| Município | Base dos Dados | CSV |
| Meta Alfabetização Brasil | Base dos Dados | CSV |
| Meta Alfabetização por UF | Base dos Dados | CSV |
| Meta Alfabetização por Município | Base dos Dados | CSV |
| Dados de alunos (TS_ALUNO, 2,2M linhas) | INEP — Microdados AEEB 2025 | CSV |

Complementarmente: TS_MUNICIPIO, TS_ESTADO e TS_ITEM (INEP) e a tabela `dicionario` da Base dos Dados (traduções de códigos, consultada via BigQuery).

## 3. Arquitetura

```text
FONTES                       INGESTÃO                          MEDALHÃO (ADLS Gen2)              CONSUMO
──────                       ────────                          ────────────────────              ───────
Base dos Dados ─┐
INEP (AEEB) ────┼── Batch (upload CSV) ──────────┐
                │                                ├──▶ BRONZE ──▶ SILVER ──▶ GOLD ──▶ Power BI
Eventos ────────┴── producer.py ─▶ Event Hubs ───┘    (bruto)    (limpo)   (star     (Import,
simulados            └─▶ consumer.py                                        schema)   zero ETL)
                        (Spark Structured Streaming)
```

O diagrama completo está em `doc/arquitetura/` (arquivo draw.io).

**Camadas:**

- **Bronze** — dado bruto convertido para Parquet. Batch (8 fontes CSV) e streaming (4 tipos de evento JSON com schema explícito) convergem no mesmo container; a Silver não distingue a origem.
- **Silver** — limpeza e padronização: deduplicação, tratamento de nulos em chaves, cast de tipos, normalização de nomes (`NU_ANO`→`ano`, `CO_MUNICIPIO`→`id_municipio`, `SG_UF`→`sigla_uf`) e de valores (`upper`/`trim`).
- **Gold** — modelo dimensional (star schema): `dim_uf`, `dim_municipio`, `dim_tempo` e **quatro tabelas fato**, cada uma na sua granularidade:

| Fato | Granularidade | Compara |
|---|---|---|
| `fato_indicador` | Município × ano × rede | realizado vs. meta municipal (particionado por ano) |
| `fato_indicador_uf` | UF × ano × rede | realizado vs. meta estadual (rede Pública) |
| `fato_indicador_brasil` | Brasil × ano | meta nacional |
| `fato_aluno_agregado` | Município × ano | % alfabetizados, proficiência média e nº de alunos avaliados (só presentes na prova) |

**Notebooks (Azure Synapse, PySpark):** `bronze/silver/gold_alfabetizacao` (pipeline principal) e `bronze/silver/gold_ts_aluno` (pipeline separada para o TS_ALUNO — decisão justificada abaixo).

## 4. Decisões técnicas e trade-offs

**Data Lake (Medalhão) vs. Data Warehouse tradicional.** Optamos por lake em ADLS Gen2 com camadas Medalhão: as fontes são heterogêneas (CSV, JSON de eventos), o volume do TS_ALUNO pede processamento distribuído (Spark), e o custo de storage em lake é muito menor que manter um warehouse dedicado ligado. O "warehouse" surge logicamente na Gold (star schema em Parquet), sem o custo de um servidor SQL dedicado.

**Batch vs. streaming.** Dados de alfabetização são de baixa frequência por natureza (avaliações anuais) — batch é o caminho natural para o histórico. O streaming (exigência do desafio) foi implementado como **simulação**: um produtor Python publica eventos em Azure Event Hubs e um consumer Spark Structured Streaming grava na Bronze particionado por `tipo_mensagem/ano/mes/dia`. Para fins de avaliação, a execução do fluxo foi simulada (eventos de exemplo depositados na Bronze), com o desenho completo versionado em `pipeline/ingestao/stream/`.

**Parquet em todas as camadas.** Formato colunar e comprimido: reduz storage, acelera leitura (só as colunas consultadas são lidas) e é nativo do Spark e do Power BI.

**Schema explícito onde importa.** No TS_ALUNO (2,2M linhas), `inferSchema` custaria uma varredura extra do arquivo inteiro — o schema das 27 colunas foi declarado manualmente. Nos eventos de streaming, o schema explícito elimina o risco de `_corrupt_record` na inferência de JSON.

**Pipeline separada para o TS_ALUNO.** O volume (2,2M vs. no máximo ~24k linhas das demais fontes) justifica notebooks próprios: reprocessar as fontes pequenas não deve custar o tempo do arquivo grande.

**Quatro fatos em vez de um.** Cada fonte de meta tem granularidade própria (município, UF, Brasil). Misturar níveis numa tabela única quebraria agregações no BI (dupla contagem). Um fato por granularidade é o padrão dimensional correto.

## 5. Descobertas e correções documentadas

Estes casos reais foram investigados e corrigidos durante o desenvolvimento — registrados aqui como evidência de qualidade do processo:

1. **Join de metas 100% vazio.** `municipio.rede` usa códigos numéricos (0, 2, 3, 5) e `meta_alfabetizacao_municipio.rede` usa texto ("Municipal") — o join nunca casava. A correção aplicou o de-para oficial consultado na tabela `dicionario` da Base dos Dados **via BigQuery** (não assumido): 0=Total, 1=Federal, 2=Estadual, 3=Municipal, 4=Privada, 5=Pública (Estadual e Municipal), 6=Pública (todas).

2. **Metas ausentes são realidade da fonte, não bug.** Só existe meta municipal para a rede Municipal, e a meta por UF cobre apenas a rede "Pública". Linhas sem meta permanecem com `NULL` na Gold (LEFT JOIN preserva o realizado) — filtrar seria descartar dado legítimo; a decisão de exibir ou não fica na camada de visualização.

3. **BLANK em subtração DAX vira zero silenciosamente.** O Acre não possui meta para 2024; a medida de gap (`taxa − meta`) retornava um "gap fantasma" de +51 p.p. porque o DAX trata BLANK como 0. Correção: `ISBLANK()` antes da subtração — UFs sem meta saem do ranking em vez de aparecer com valor absurdo.

4. **Falso alarme de corrupção de dados.** A proficiência parecia "7,8 bilhões" numa amostra aberta no Excel; a verificação no CSV bruto mostrou o valor correto (`781.7763317`) — era artefato de formatação do Excel. Lição registrada: validar sempre na fonte antes de "corrigir".

## 6. Qualidade de dados

Notebooks dedicados (`monitoramento_pipeline_silver` e `monitoramento_pipeline_prata`) cobrem as quatro checagens exigidas:

- **Duplicidade** — `count()` vs. `dropDuplicates().count()` por dataset;
- **Valores ausentes** — contagem de nulos por coluna, com foco nas chaves;
- **Integridade de chave** — anti-join (`left_anti`) valida que todo `id_municipio` do fato existe na dimensão;
- **Consistência entre tabelas** — cruzamentos UF×Meta UF, Município×Meta Município e TS_ALUNO×Município.

Além das checagens, os notebooks registram **monitoramento operacional**: volume processado por dataset, latência de leitura e alertas.

## 7. FinOps

- **Parquet colunar + comprimido** em todas as camadas — menos storage, queries mais baratas;
- **`fato_indicador` particionado por ano** — consultas filtradas leem só a partição necessária;
- **Spark Pool Small (4 vCores) com pausa automática em 5 min** — zero custo ocioso;
- **Storage LRS** — redundância local é suficiente para o caso; mais barata que GRS;
- **Política de ciclo de vida** (Terraform): dados da Bronze migram para tier Cool após 30 dias e Archive após 90;
- **Schema explícito no TS_ALUNO** — evita a varredura extra do `inferSchema` em 2,2M linhas.

## 8. Segurança

- **Nenhuma credencial no código**: os notebooks leem a chave do Storage em runtime via `mssparkutils.credentials.getSecret()` do **Azure Key Vault**;
- **RBAC com menor privilégio**: Synapse acessa Key Vault como *Key Vault Secrets User* e o Storage como *Storage Blob Data Contributor* (via identidade gerenciada); o Power BI lê a Gold com *Storage Blob Data Reader* (somente leitura);
- Segredos locais ficam em `.env` (fora do versionamento — ver `.env.example`).

## 9. Aplicação em IA (potencial da camada Gold)

A Gold foi modelada para servir diretamente a casos de uso de IA — não implementados neste desafio, conforme escopo, mas viabilizados pela estrutura:

- **Predição de risco de não-alfabetização por município** — o `fato_aluno_agregado` (proficiência média, % alfabetizados, nº de avaliados) combinado com o histórico do `fato_indicador` fornece features prontas para um modelo de classificação/regressão que antecipe municípios em risco de não atingir a meta de 2030;
- **Clusterização de perfis municipais** — agrupar municípios por padrão de desempenho (proficiência × gap × participação) para direcionar políticas diferenciadas por perfil, em vez de ações uniformes;
- **Priorização de recursos** — ranquear municípios pelo gap projetado vs. meta, apoiando decisão de alocação de investimento educacional;
- **Séries temporais** — à medida que novos ciclos anuais forem ingeridos (a pipeline já particiona por ano), modelos de tendência podem projetar a trajetória de cada UF rumo às metas 2025–2030.

## 10. Dashboard (Power BI)

Painel Nacional de Alfabetização conectado **diretamente à Gold** (ADLS Gen2, modo Import) com **zero transformação no Power Query** — todo tratamento pertence à pipeline. Inclui KPIs nacionais (taxa, meta, gap, alunos avaliados), comparação Meta vs. Realizado por UF com cor condicional, ranking Top/Bottom 5 (com tratamento de UFs sem meta) e comparação por região. Medidas DAX documentadas com cabeçalho padrão (descrição, fonte, regra de negócio, dependências).

## 11. Estrutura do repositório

```text
fiap-ds-ia-tech-challenge-2/
├── doc/
│   ├── arquitetura/          # diagrama draw.io + arquitetura.md
│   ├── finops/
│   └── uteis/
├── infra/
│   └── terraform/            # IaC: RG, ADLS Gen2, containers, Synapse, Spark Pool, Key Vault, RBAC
│       ├── main.tf
│       └── variables.tf
├── pipeline/
│   ├── camadas/
│   │   ├── bronze/           # bronze_alfabetizacao.ipynb · bronze_ts_aluno.ipynb
│   │   ├── prata/            # silver_alfabetizacao.ipynb · silver_ts_aluno.ipynb
│   │   ├── ouro/             # gold_alfabetizacao.ipynb · gold_ts_aluno.ipynb
│   │   └── monitoramento/    # monitoramento_pipeline_silver.ipynb · monitoramento_pipeline_prata.ipynb
│   └── ingestao/
│       ├── batch/batch.py            # desenho batch (execução simulada — ver nota de escopo no arquivo)
│       ├── stream/producer.py        # produtor de eventos (Event Hubs)
│       ├── stream/consumer.py        # consumer Spark Structured Streaming
│       ├── config.py
│       └── mock_support.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

> **Nota de escopo (streaming e batch standalone):** os scripts em `pipeline/ingestao/` representam a arquitetura pretendida em produção. Para fins do desafio, a execução foi simulada (eventos/arquivos de exemplo depositados na Bronze) — a nota de escopo está registrada no cabeçalho de cada script.

> **Nota sobre o Terraform:** o IaC descreve fielmente a infraestrutura implantada (Synapse, Spark Pool, Key Vault, RBAC, containers `bronze`/`silver`/`gold`); o provisionamento original foi realizado via portal Azure, e o Terraform está versionado como referência reproduzível.

## 12. Pré-requisitos

- Python 3.10+ · Terraform 1.5+ (opcional) · Conta Azure (Storage ADLS Gen2, Synapse, Key Vault) · Power BI Desktop (para o dashboard)

## 13. Como executar

### Provisionamento (Terraform)

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

A senha do administrador SQL do Synapse é variável sensível — informe via `terraform.tfvars` (fora do versionamento) ou variável de ambiente `TF_VAR_synapse_sql_admin_password`. Os defaults das demais variáveis já refletem os nomes do projeto (`rg-alfabetizacao`, `stalfalfabetizacao`, `synapse-alfabetizacao`, `kv-alfabetizacao`).

### Configuração local

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.\.venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env           # preencher com os valores do ambiente
```

### Pipeline (Azure Synapse)

Com os dados brutos no container `bronze`, executar os notebooks na ordem:

1. `bronze_alfabetizacao.ipynb` → 2. `silver_alfabetizacao.ipynb` → 3. `gold_alfabetizacao.ipynb`
4. `bronze_ts_aluno.ipynb` → 5. `silver_ts_aluno.ipynb` → 6. `gold_ts_aluno.ipynb`
7. Notebooks de monitoramento (qualidade de dados) a qualquer momento após a Silver.

### Simulação de streaming (opcional, local)

```bash
# Terminal 1
python pipeline/ingestao/stream/consumer.py
# Terminal 2
python pipeline/ingestao/stream/producer.py
```

### Modo mock (sem Azure)

Helpers em `pipeline/ingestao/mock_support.py` permitem validar a estrutura de payloads sem recursos cloud:

```python
from pathlib import Path
from pipeline.ingestao.mock_support import write_mock_csv, append_mock_message

write_mock_csv(Path("tmp/mock.csv"), table_name="alfabetizacao")
append_mock_message(Path("tmp/mock_messages.jsonl"), {"tipo_mensagem": "dados_aluno", "ID_ALUNO": 123})
```

## 14. Fluxo de versionamento

Desenvolvimento em branches por feature → Pull Request → review de outro membro → merge em `develop` → merge final em `main` para a entrega. O histórico de commits e PRs evidencia a evolução da pipeline.

---

*Tech Challenge Fase 2 · FIAP Pós-Tech · Dados: Base dos Dados & INEP (Microdados AEEB 2025) · Julho/2026*
