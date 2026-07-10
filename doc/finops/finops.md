# Estratégia de FinOps (Cloud Cost Optimization) — Azure

## 1. Introdução e Filosofia FinOps
No desenvolvimento desta plataforma de dados educacionais, o gerenciamento de custos foi tratado como um requisito de arquitetura de primeira classe. A nuvem Azure opera sob um modelo de consumo variável (*Pay-as-you-go*), o que exige monitoramento contínuo e escolhas arquiteturais conscientes para evitar o desperdício de recursos (*cloud sprawl*). 

Este documento descreve as práticas recomendadas e as escolhas de design aplicadas para otimizar os custos de armazenamento, processamento e ingestão do projeto.

---

## 2. Direcionadores de Custo por Componente e Ações Aplicadas

A tabela abaixo mapeia os principais recursos provisionados na Azure, seus respectivos *drivers* de cobrança e as estratégias específicas que implementamos para mitigar gastos desnecessários:

| Serviço Azure | Direcionador de Custo (Billing Metric) | Estratégia de Otimização Aplicada na Solução |
| :--- | :--- | :--- |
| **Azure Data Lake Storage Gen2 (ADLS)** | • Volume de dados armazenado (GB/mês).<br>• Operações de leitura/escrita (Transações). | • **Migração para Formato Parquet:** Substituição de formatos textuais (CSV/JSON) por Parquet nas camadas Prata e Ouro. Por ser colunar e compactado, reduz drasticamente o espaço em disco ocupado e acelera as consultas (menor custo de varredura).<br>• **Camada de Acesso Dinâmica (Cool e Archive):** Configuração de políticas de ciclo de vida automatizadas para mover dados brutos e sem uso frequente para camadas de menor custo de armazenamento.<br>• **Redundância LRS (Local Redundant Storage):** Uso de replicação local (LRS) em vez de opções globais ou georreferenciadas (GRS), garantindo a menor tarifa possível de armazenamento para o escopo do projeto.<br>• **Estratégia de Particionamento Anual:** Organização física dos dados no Data Lake segmentada por ano, otimizando a leitura biológica dos jobs Spark (leitura seletiva de partições). |
| **Azure Synapse Analytics** | • Tempo de computação (Virtual Machines/Clusters ativos).<br>• Tipo e tamanho da instância (CPU/Memória). | • **Pausa Automática (Auto-Pause):** Configuração de desligamento automático por inatividade nos pools de computação do Synapse, garantindo que o cluster pare de faturar assim que a execução dos notebooks for finalizada. |
| **Azure Data Factory (ADF)** | • Horas de execução do Integration Runtime (IR). | • **Gatilhos Inteligentes (Triggers):** Como a carga Batch de alfabetização é anual, a pipeline não fica em execução contínua. Ela é acionada estritamente sob demanda ou em janelas específicas de entrega de dados. |

---

## 3. Automação de Ciclo de Vida (Lifecycle Management Code)

Para garantir que a transição para as camadas mais econômicas de armazenamento ocorra sem intervenção manual, foi implementada uma regra declarativa de ciclo de vida no Terraform direcionada ao container `bronze`. 

Os dados brutos passam por um rebaixamento progressivo de custo com base no tempo desde a sua última modificação:
*   **Após 30 dias:** O dado é movido para a camada **Cool**, reduzindo o custo de armazenamento enquanto mantém o dado disponível para consultas eventuais.
*   **Após 90 dias:** O dado é movido para a camada **Archive**, que possui o menor custo por GB do Azure, ideal para conformidade histórica e auditoria do Tech Challenge.

```hcl
# Trecho de infraestrutura que gerencia o ciclo de vida dos dados na Azure
resource "azurerm_storage_management_policy" "lifecycle_policy" {
  storage_account_id = azurerm_storage_account.adls.id

  rule {
    name    = "bronze-to-cool-or-archive"
    enabled = true
    
    filters {
      prefix_match = ["bronze/"]
      blob_types   = ["blockBlob"]
    }
    
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30
        tier_to_archive_after_days_since_modification_greater_than = 90
      }
    }
  }
}

```

---

## 4. Práticas de Governança e Controle Orçamentário

Para garantir a previsibilidade financeira da solução, foram mapeadas três camadas de controle de governança:

### A. Tags de Controle FinOps (Marcação de Recursos)

Todos os recursos criados via Terraform incluem tags de metadados obrigatórias para permitir o rastreamento, alocação e filtragem de custos no painel do *Azure Cost Management*:

* `Environment`: identificação do ambiente (`dev`, `prod`).
* `Project`: `fiap-tech-challenge-2`
* `CostCenter`: `educacao-alfabetizacao`
* `FinOps_Owner`: `equipe-dados`

### B. Azure Budgets e Alertas

Configuração de orçamentos lógicos no nível do *Resource Group* do projeto.

* Definição de um teto de gastos mensal.
* Gatilhos de alertas automatizados por e-mail quando o consumo atingir **50%**, **80%** e **100%** do orçamento previsto, permitindo uma ação reativa antes do fechamento da fatura.

### C. Abordagem Híbrida como Vetor de Economia

A decisão arquitetural de separar a ingestão em **Batch** (para a carga pesada anual) e **Streaming** (para correções rápidas) é, por si só, uma estratégia de FinOps. Em vez de manter um cluster Spark robusto ou um fluxo de streaming de larga escala ligado 24/7 processando arquivos pesados, a computação pesada é isolada e ligada apenas no momento da consolidação dos dados anuais.

---

## 5. Próximos Passos na Jornada FinOps

Para evoluir a maturidade financeira do projeto, as seguintes implementações são recomendadas:

* **Utilização de Instâncias Spot:** Configurar os nós de computação secundários do cluster Spark para utilizarem instâncias *Spot* da Azure, o que pode reduzir o custo de processamento em até 80% (ideal para jobs tolerantes a falhas em ambientes de teste).
* **Políticas Automatizadas de Purge:** Implementar regras rígidas de expiração para os arquivos temporários ou logs de execução armazenados na camada Bronze.


