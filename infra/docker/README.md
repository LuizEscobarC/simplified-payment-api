# Infra Docker - API de Pagamentos

Infraestrutura Docker para desenvolvimento da API de Pagamentos, com orquestração Python, serviços modulares e automação de qualidade de código.

## 🚀 Início Rápido

### Comando Único (Recomendado)
```bash
cd infra/docker && make all
```

Este comando:
- ✅ Prepara o ambiente Python (venv + dependências)
- ✅ Sobe todos os serviços (Laravel, MySQL, Redis, MongoDB, Nginx)
- ✅ Configura Git hooks de qualidade de código

### Acesso
- **API Laravel**: http://localhost
- **Adminer (DB)**: http://localhost:8080
- **MailHog (Emails)**: http://localhost:8025

## 📋 Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `make all` | Setup completo + serviços + hooks |
| `make setup` | Apenas ambiente Python |
| `make start` | Sobe serviços básicos |
| `make start-monitoring` | Sobe serviços + monitoramento |
| `make hooks` | Configura Git hooks |
| `make status` | Status dos serviços |
| `make stop` | Para serviços |
| `make clean` | Limpa containers/volumes |

## 🏗️ Arquitetura

### Serviços
- **Laravel** (PHP 8.3 + FPM)
- **MySQL** (Banco principal)
- **MongoDB** (Dados flexíveis)
- **Redis** (Cache + Filas)
- **Nginx** (Proxy reverso)
- **Supervisor** (Processos Laravel)

### Qualidade de Código
- **PHPStan** (Análise estática)
- **Laravel Pint** (Estilo de código)
- **PHPMD** (Detecção de code smells)
- **PHP-CS-Fixer** (Correção automática)

### Volumes
- `mysql_data` - Dados MySQL
- `redis_data` - Dados Redis
- `mongo_data` - Dados MongoDB
- `laravel_storage` - Arquivos Laravel

## 🔧 Desenvolvimento

### Ambiente Python
```bash
cd infra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Orquestrador
```bash
cd infra/docker
python3 orchestrator.py --help
```

### Git Hooks
```bash
cd infra/docker
python3 orchestrator.py hooks
```

## 🧪 Testes

### Status dos Serviços
```bash
make status
```

### Logs
```bash
docker-compose -f docker-compose.local.yml logs -f [service]
```

### Debug
```bash
# Ver containers
docker ps

# Ver logs específicos
docker logs [container_name]
```

## 📁 Estrutura

```
infra/docker/
├── docker-compose.local.yml    # Configuração serviços
├── orchestrator.py            # Orquestrador Python
├── services/                  # Classes de serviço
│   ├── base_service.py
│   ├── git_hooks_service.py
│   └── ...
├── scripts/                   # Scripts auxiliares
├── mysql/                     # Config MySQL
├── nginx/                     # Config Nginx
├── php/                       # Config PHP
├── redis/                     # Config Redis
├── supervisor/                # Config Supervisor
└── Makefile                   # Automação
```

## 🔒 Segurança

- Redes Docker isoladas
- Secrets via variáveis de ambiente
- Ferramentas de qualidade automatizadas
- Git hooks para controle de qualidade

## 🐛 Troubleshooting

### Problemas Comuns

1. **Portas ocupadas**: Verifique se portas 80, 3306, 6379, 27017 estão livres
2. **Permissões**: Execute como usuário com permissões Docker
3. **Venv não ativa**: Sempre ative o ambiente virtual antes dos comandos
4. **Ferramentas PHAR**: Verifique se os arquivos foram baixados em `infra/tools/`

### Limpeza Completa
```bash
make clean
docker system prune -a --volumes
```

```bash
cd infra

# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

cd docker
```

### Arquivo .env

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar senhas se necessário
nano .env
```

## 🏗️ O que sobe

### Básico (`make start`)
- **MySQL 8.0** (porta 3307) - Banco relacional
- **MongoDB 7.0** (porta 27017) - Banco NoSQL
- **Redis 7.2** (porta 6377) - Cache/sessões
- **Laravel 11** (porta 80) - API backend
- **Nginx** - Servidor web

### Com Monitoramento (`make start-monitoring`)
- Tudo acima +
- **Elasticsearch** (porta 9200) - Busca/indexação
- **Logstash** (porta 9600) - Processamento de logs
- **Kibana** (porta 5601) - Dashboard de logs
- **Prometheus** (porta 9090) - Métricas

## 📁 Estrutura

```
infra/docker/
├── orchestrator.py          # 🏗️ Orquestrador principal
├── docker-compose.*.yml     # 📦 Configs Docker Compose
├── services/                # 🔧 Classes Python dos serviços
├── scripts/                 # 🛠️ Utilitários
└── [mysql|redis|nginx|...]/ # ⚙️ Configs específicas
```

## 🐛 Desenvolvimento

Para desenvolvimento iterativo:
- Use `make start` para subir tudo rapidamente
- Serviços são verificados automaticamente após startup
- Logs são mostrados em tempo real durante inicialização

## 🧹 Limpeza

```bash
# Parar tudo
make stop

# Remover containers e volumes
make clean
```

---

**Dica**: Use `make all` para preparar tudo e subir em um comando só! 🎯