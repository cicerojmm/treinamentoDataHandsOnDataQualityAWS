# Data Contract CLI

O Data Contract CLI é uma ferramenta para gerenciar contratos de dados em projetos de engenharia de dados. Este documento explica como usar a ferramenta para importar, testar e exportar contratos de dados.

## Instalação

O Data Contract CLI está disponível como uma imagem Docker:

```bash
docker pull datacontract/cli
```

Para verificar a instalação e ver os comandos disponíveis:

```bash
docker run --rm -v ${PWD}:/home/datacontract datacontract/cli
```

## Comandos Principais

### Importar metadados do AWS Glue

O comando abaixo importa metadados de um banco de dados do AWS Glue para um arquivo YAML de contrato de dados:

```bash
docker run --rm \
  -v ${PWD}:/home/datacontract \
  -e AWS_DEFAULT_REGION=us-east-2 \
  -e AWS_ACCESS_KEY_ID=<SUA_ACCESS_KEY> \
  -e AWS_SECRET_ACCESS_KEY=<SUA_SECRET_KEY> \
  datacontract/cli import \
  --format glue \
  --source datahandson-dq-lakehouse-amazonsales \
  --output datacontract_amazonsales.yml
```

### Testar um contrato de dados

Para validar um contrato de dados contra um servidor de produção:

```bash
docker run --rm \
  -v ${PWD}:/home/datacontract \
  -e DATACONTRACT_S3_REGION=us-east-2 \
  -e DATACONTRACT_S3_ACCESS_KEY_ID='<SUA_ACCESS_KEY>' \
  -e DATACONTRACT_S3_SECRET_ACCESS_KEY='<SUA_SECRET_KEY>' \
  -e DATACONTRACT_S3_SESSION_TOKEN='' \
  datacontract/cli test --server production quality-datacontract_amazonsales.yml
```

### Exportar um contrato de dados para HTML

Para gerar uma documentação HTML a partir de um contrato de dados:

```bash
docker run --rm \
  -v ${PWD}:/home/datacontract \
  datacontract/cli export --format html --output datacontract.html completao-datacontract_amazonsales.yml
```

## Arquivos de Exemplo

Este diretório contém os seguintes arquivos de exemplo:

- `completao-datacontract_amazonsales.yml`: Contrato de dados completo
- `quality-datacontract_amazonsales.yml`: Contrato de dados com regras de qualidade
- `export-datacontract_amazonsales.yml`: Contrato de dados exportado
- `datacontract.html`: Documentação HTML gerada


## Mais Informações

Para mais detalhes sobre o Data Contract CLI, visite a [documentação oficial](https://github.com/datacontract/datacontract-cli).