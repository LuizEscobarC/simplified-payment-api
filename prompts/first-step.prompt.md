```prompt
## Checklist atômico escalonado — do básico ao avançado

Instrução: cada item abaixo é autocontido e verificável. Trabalhe em ordem crescente de complexidade.

-- Básico: ambiente local e containers --
- [x] Build da imagem Docker sem erros (`docker build`)
- [x] Rodar container PHP-FPM e confirmar porta ativa (ex.: `curl localhost:9000`)
- [x] Healthcheck mínimo responde 200 (endpoint `/health` ou equivalent)
- [ ] Dockerfile multi-stage aplicado e imagem otimizada (tamanho e layers)
- [ ] Usuário do processo não é `root` na imagem (non-root)
- [ ] `docker-compose up` sobe todo o stack local (DB, cache, app)

-- CI/CD inicial --
- [ ] Workflow GitHub Actions: rodar `composer install` / `npm install`
- [ ] Pipeline roda lint (phpstan/phpmd) com sucesso
- [ ] Pipeline roda testes unitários e falha em regressão
- [ ] Pipeline gera artefato de build (imagem ou pacote)

-- Deploy mínimo/Manual (infra básica) --
- [ ] Script/step para deploy manual para um ambiente remoto (S3 upload / ECS task)
- [ ] Secrets são lidos por variáveis seguras, não hardcoded

-- Banco de dados e cache --
- [ ] Conexão estável com PostgreSQL a partir do container
- [ ] Executar `EXPLAIN ANALYZE` em 1 query crítica e documentar plano
- [ ] Index parcial ou composto criado para caso de query lenta
- [ ] PgBouncer ou pooling configurado (simples test)
- [ ] Redis disponível e um valor de cache lido/escrito (cache-aside)
- [ ] TTL configurado e teste de expiração OK

-- Mensageria e consistência --
- [ ] Consumidor simples (worker) lê de uma fila e processa 1 mensagem com idempotência
- [ ] Outbox pattern implementado em exemplo (DB→fila atômico)
- [ ] Dead-letter queue configurada e teste de reentrega

-- tObservability e operações --
- [ ] Logs estruturados (JSON) emitidos com `request_id`/correlation id
- [ ] Métrica básica exposta (endpoint Prometheus) e coletada localmente
- [ ] Trace de request end-to-end em um cenário simples (OpenTelemetry/Jaeger)
- [ ] Dashboard com 1 gráfico de latency e 1 alerta básico configurado

-- Performance e resiliência --
- [ ] Teste de carga simples (k6) contra endpoint crítico, coletar throughput/latency
- [ ] Implementado retry/backoff para chamadas externas com circuit breaker simples
- [ ] Limitação de taxa (rate limit) testada com burst

-- Integração Backend + IA (prova de conceito) --
- [ ] Endpoint que envia payload para fila para processamento IA (sem bloquear request)
- [ ] Worker consome fila, chama LLM API (simulado ou real) e grava resultado
- [ ] Cache de respostas IA com política de invalidação testada
- [ ] Fallback quando API de IA indisponível (ex.: resposta padrão ou requeue)

-- Segurança e revisão final --
- [ ] Scans automáticos de dependências (composer audit / npm audit)
- [ ] Secrets scanning (nenhum segredo em repo)
- [ ] Revisão de permissões de filesystem (não world-writable)
- [ ] Política de CORS e validação de input aplicada nos endpoints críticos

``` 

| 1 | Docker avançado + Docker Compose | Ambiente local production-like |
| 2 | AWS core (VPC, ECS, RDS, S3) | App deployado na AWS |
| 3 | CI/CD completo com GitHub Actions | Pipeline build → test → deploy |


Docker avançado + Docker Compose | Ambiente local production-like

**Docker — Domine:**
- Multi-stage builds otimizados
- Layer caching strategies
- Security: non-root users, image scanning
- Networking entre containers
- Health checks e graceful shutdown


**debugar problemas de orquestração** e **otimizar para produção**.