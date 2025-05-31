# Treinamento Data Hands-on: Data Quality com AWS

Treinamento prático sobre **Qualidade de Dados** utilizando **Modern Data Stack na AWS**. Este projeto demonstra a implementação de diferentes ferramentas e técnicas para garantir a qualidade de dados em um pipeline de dados completo.

## 📋 Visão Geral

Este projeto implementa um pipeline de dados completo com foco em qualidade de dados, utilizando:

- **Infraestrutura como Código** com Terraform
- **Orquestração** com Apache Airflow (MWAA)
- **Processamento de Dados** com AWS Glue
- **Armazenamento** com S3 e Delta Lake
- **Qualidade de Dados** com Soda, Great Expectations e AWS Glue Data Quality
- **Contratos de Dados** com Data Contract CLI
- **Monitoramento** com Grafana
- **Notificações** com SNS, Lambda e Discord

## 🗂️ Dataset

O projeto utiliza o [Amazon Sales Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset) disponível no Kaggle, que contém dados de vendas da Amazon.

## 🏗️ Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Fonte    │────▶│  Ingestão   │────▶│Processamento│────▶│   Consumo   │
│    Dados    │     │    (S3)     │     │   (Glue)    │     │ (Redshift)  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                            ┌──────▼──────┐
                                                            │  Qualidade  │
                                                            │  de Dados   │
                                                            └──────┬──────┘
                                                                   │
                          ┌──────────┬────────────────────┬────────┴──────┐
                          │          │                    │               │
                     ┌────▼────┐┌────▼────┐          ┌────▼────┐     ┌────▼────┐
                     │  Soda   ││   GX    │          │  Glue   │     │  Data   │
                     │         ││         │          │   DQ    │     │Contract │
                     └────┬────┘└────┬────┘          └────┬────┘     └────┬────┘
                          │          │                    │               │
                          └──────────┴────────────────────┴───────────────┘
                                                │
                                          ┌─────▼─────┐
                                          │ Alertas & │
                                          │Dashboards │
                                          └───────────┘
```

## 🛠️ Componentes Principais

### Infraestrutura (Terraform)

A infraestrutura é gerenciada com Terraform e inclui:

- **VPC e Subnets**: Configuração de rede
- **S3 Buckets**: Armazenamento de dados e scripts
- **Glue Jobs**: Processamento de dados e testes de qualidade
- **Lambda Functions**: Processamento de eventos e alertas
- **SNS Topics**: Sistema de notificações
- **EventBridge Rules**: Captura de eventos de qualidade de dados
- **Redshift**: Armazenamento analítico

### Ferramentas de Qualidade de Dados

O projeto implementa três ferramentas de qualidade de dados:

1. **Soda**:
   - Verificações de qualidade baseadas em SQL
   - Integração com Airflow

2. **Great Expectations**:
   - Validações de dados com expectativas
   - Documentação automática de resultados

3. **AWS Glue Data Quality**:
   - Regras de qualidade nativas da AWS
   - Integração com EventBridge para alertas

### Contratos de Dados

Utilizamos o Data Contract CLI para:
- Importar metadados do AWS Glue
- Definir contratos de dados com regras de qualidade
- Exportar documentação HTML

## 📁 Estrutura do Projeto

```
treinamentoDataHandsOnDataQualityAWS/
├── data-contract/           # Contratos de dados
├── dbt_tests/               # Testes com dbt
├── glue_data_quality/       # Scripts para AWS Glue Data Quality
├── great_expectations/      # Configurações e testes do Great Expectations
├── infra/                   # Configurações de infraestrutura local
├── soda/                    # Configurações e testes do Soda
├── terraform/               # Código Terraform para infraestrutura AWS
│   └── infra/
│       ├── modules/         # Módulos Terraform reutilizáveis
│       ├── scripts/         # Scripts para Lambda, Glue, etc.
│       └── main.tf          # Configuração principal do Terraform
└── README.md                # Este arquivo
```

## 🚀 Como Usar

### Pré-requisitos

- AWS CLI configurado
- Terraform instalado
- Docker instalado (para execução local)
- Acesso à AWS com permissões adequadas

### Implantação da Infraestrutura

```bash
cd terraform/infra
terraform init -backend-config="backends/develop.hcl"
terraform apply -var-file=envs/develop.tfvars
```

## 📊 Monitoramento

O projeto inclui dashboards Grafana para monitoramento de qualidade de dados:
- Dashboard Soda para métricas de qualidade
- Dashboard Great Expectations para resultados de validação
- Alertas configurados para notificações no Discord

## 📝 Licença

Este projeto é para fins educacionais e de treinamento.

## 📚 Recursos Adicionais

- [Documentação do Soda](https://docs.soda.io/)
- [Documentação do Great Expectations](https://docs.greatexpectations.io/)
- [Documentação do AWS Glue Data Quality](https://docs.aws.amazon.com/glue/latest/dg/data-quality.html)
- [Documentação do Data Contract](https://datacontract.com/docs/cli)