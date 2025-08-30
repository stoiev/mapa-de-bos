# CLI ETL para Dados Criminais da Polícia Brasileira

Uma ferramenta de linha de comando especializada para extrair e carregar dados criminais da polícia brasileira de arquivos XLSX. Por padrão, processa os dados criminais mais recentes da Polícia do Estado de São Paulo, mas também pode lidar com arquivos locais ou URLs remotas personalizadas.

## Funcionalidades

- **Fonte de Dados Padrão**: Processa automaticamente dados criminais do Estado de São Paulo (2025)
- **Local e Remoto**: Processa arquivos XLSX do disco local ou URLs remotas
- **Carregamento SQLite**: Carrega dados criminais diretamente no SQLite para armazenamento de dados brutos
- **CLI Rica**: Interface de linha de comando bonita com formatação rica
- **Configuração Simples**: Configuração baseada em INI para configurações do banco de dados
- **Log Abrangente**: Log no console com opção verbosa

## Instalação

### Instalação para Desenvolvimento

1. Clone o repositório e navegue para o diretório do projeto
2. Instale o projeto em modo de desenvolvimento usando uv:

```bash
cd /caminho/para/extract-and-load
export PATH="$HOME/.cargo/bin:$PATH"  # Certifique-se de que uv está no PATH
uv sync
```

### Instalação para Produção

```bash
uv pip install .
```

## Uso

### Uso Básico

```bash
# Processa dados padrão da polícia de São Paulo (2025)
extract-and-load

# Processa arquivo XLSX local
extract-and-load dados_policiais.xlsx

# Processa arquivo XLSX remoto
extract-and-load https://exemplo.com/dados_policiais.xlsx

# Processa planilha específica
extract-and-load dados_policiais.xlsx -s "Janeiro_2024"

# Execução teste com dados padrão (valida sem inserir)
extract-and-load --dry-run

# Usa configuração personalizada
extract-and-load -c config.ini

# Log verboso com dados padrão
extract-and-load -v
Crie um arquivo de configuração chamado `config.ini`:

```ini
[database]
# Configuração SQLite para dados criminais brutos
host = localhost
port = 5432
database = ../../data/bronze.db
username = 
password = 
driver = sqlite

[logging]
# Configuração de logging
level = INFO
```

Use com configuração:

```bash
extract-and-load -c config.ini
```

### Exemplos

1. **Processamento de Dados Padrão de São Paulo**:
```bash
# Processa os dados criminais mais recentes da polícia de São Paulo
extract-and-load

# Execução teste com dados padrão
extract-and-load --dry-run

# Log verboso com dados padrão
extract-and-load -v
```

2. **Processamento XLSX Personalizado**:
```bash
# Processamento de arquivo local
extract-and-load relatorios_policiais_2024.xlsx

# Processa planilha específica com execução teste
extract-and-load relatorios_policiais.xlsx -s "Janeiro_2024" --dry-run
```

3. **Processamento XLSX Remoto**:
```bash
# Baixa e processa de URL personalizada
extract-and-load https://transparencia.sp.gov.br/outros_dados.xlsx

# Com log verboso
extract-and-load -v https://data.gov.br/police/reports.xlsx
```

## Contribuindo

1. Faça um fork do repositório
2. Crie uma branch de funcionalidade
3. Faça suas alterações
4. Adicione testes se aplicável
5. Envie um pull request

## Desenvolvimento

### Estrutura do Projeto

```
src/extract_and_load/
├── __init__.py          # Inicialização do pacote
├── cli.py               # Interface CLI principal
├── config.py            # Gerenciamento de configuração
├── utils.py             # Funções utilitárias
└── commands/            # Módulos de comando
    └── extract.py       # Funções de processamento XLSX
```

### Adicionando Novas Funcionalidades

1. Adicione novas opções ao comando principal em `cli.py`
2. Estenda a função `process_xlsx` em `extract.py`
3. Siga o padrão existente usando decoradores Click

### Executando Testes

```bash
uv run pytest
```

### Formatação de Código

```bash
uv run black src/
uv run isort src/
```

## Requisitos

- Python 3.13+
- Dependências gerenciadas pelo uv (veja pyproject.toml)

## Licença

Licença MIT
