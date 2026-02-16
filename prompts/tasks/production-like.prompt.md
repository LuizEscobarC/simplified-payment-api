```markdown
# Task: Criar ambiente "production-like" (checklist aplicável ao repo)

## Contexto
- Objetivo: fornecer um conjunto de artefatos e passos reproduzíveis para executar um ambiente que replica o comportamento crítico da produção (config, serviços, observability, healthchecks), sem precisar da escala completa.

## Entregáveis esperados
- `docker-compose.prod.yml` ou manifests `k8s/` mínimos
- scripts para levantar ambiente (`scripts/up-prod.sh`, `scripts/down-prod.sh`)
- documentação (`prompts/tasks/production-like.prompt.md` atualizado e `README-prod.md`)
- smoke tests automatizados e comandos para load test (`k6`)

## Requisitos essenciais
- Paridade de configuração: mesmas variáveis `ENV`/secrets (ou mock seguro), flags e versões runtime.
- Serviços parity: Postgres, Redis e broker equivalentes; ou endpoints gerenciados com comportamento similar.
- Imagens idênticas: usar mesmas tags de imagem e configuração non-root.
- Observability: logs estruturados, métricas (Prometheus) e tracing (OpenTelemetry) configurados.
- Healthchecks: endpoints `/health/liveness` e `/health/readiness` implementados e expostos.
- Segurança: secrets via provider (Vault/Secrets Manager) ou arquivos mock encriptados; endpoints protegidos.

## Checklist atômico (ordem de implementação)
- [ ] Adicionar `docker-compose.prod.yml` com serviços: app, postgres, redis, broker, observability (prometheus/grafana) e reverse-proxy (nginx).
- [ ] Criar scripts: `scripts/up-prod.sh` (build + up -d) e `scripts/down-prod.sh` (down + cleanup).
- [ ] Garantir imagens fixas: usar `IMAGE_TAG`/`DOCKER_TAG` e não `latest` no compose/manifests.
- [ ] Implementar healthchecks na aplicação (`/health/liveness`, `/health/readiness`) e configurar probes no compose/k8s.
- [ ] Configurar resource limits nas definições (cpu/memory) no compose/k8s.
- [ ] Integrar logs estruturados (JSON) e configurar um collector local (efk/otel) para testes.
- [ ] Adicionar dashboard/prometheus scrape config e um dashboard simples no Grafana.
- [ ] Implementar modo de dados realistas: script `scripts/load-data.sh` para importar snapshot anonimizado ou gerar dados sintéticos.
- [ ] Adicionar examples de secrets: `secrets.example.env` e instruções para usar Vault/Secrets Manager.
- [ ] Incluir smoke tests: `scripts/smoke-test.sh` que valida endpoints básicos, health e DB connectivity.
- [ ] Adicionar job de CI (GitHub Actions) que executa: build images, `docker-compose -f docker-compose.prod.yml up --build -d`, smoke tests, e `docker-compose down`.
- [ ] Criar documentação `README-prod.md` com comandos e checklist de validação.

## Exemplos práticos (comandos)
```bash
# subir ambiente production-like
./scripts/up-prod.sh

# rodar smoke tests
./scripts/smoke-test.sh

# executar load test básico
k6 run - < load-tests/basic.js
```

## Sugestões de conteúdo para `docker-compose.prod.yml`
- app: use a mesma imagem usada em produção (com `DOCKER_TAG` ARG)
- postgres: `image: postgres:15-alpine`, volumes com backup
- redis: `image: redis:7-alpine`
- broker: rabbitmq:3-management (ou kafka local via confluent)
- observability: prometheus + grafana + jaeger/opentelemetry-collector
- nginx/proxy: TLS (self-signed) para testar HTTPS local

## Critérios de aceitação
- [ ] `scripts/up-prod.sh` levanta todos os serviços sem erros.
- [ ] `/health/readiness` responde 200 quando dependências OK e 503 quando DB simulated down.
- [ ] Smoke tests passam no CI e localmente.
- [ ] Métricas básicas aparecem no Prometheus e gráfico no Grafana.
- [ ] Data load script importa dataset de teste representativo.
- [ ] Runbook curto criado com passos para incident response (onde olhar logs, traces, como reiniciar serviços).

## Observações
- Não é necessário replicar escala total — ajuste recursos para simular latência e limites.
- Usar snapshots anonimizados para preservar privacidade.
- Automatize limpeza de volumes e imagens antigas para evitar consumo excessivo de disco.

``` 