# Ideia mínima e prática para Health Checks em Laravel — direto ao ponto

Principais endpoints
- /health/liveness — verificação leve (processo vivo). 200 OK salvo travamento sério.
- /health/readiness — verificação completa (DB, cache, filas, disco, migrations, vars, dependências externas). 200 para Healthy/Degraded; 503 para Unhealthy (Kubernetes-friendly).
- Opcional: /health/startup — bloqueia até app pronto (útil se inicialização carrega caches pesados).

O que checar (priorizar impacto no serviço)
- Conectividade com DB (executar query simples ou getPdo)
- Redis/cache (PING ou read/write)
- Fila (conector/consumo básico)
- Espaço em disco / uso memória (limiares)
- Estado de migrations / esquema
- Variáveis de ambiente essenciais (existência/consistência)
- Dependências externas críticas (com timeout curto ou via cache)
- Idempotência / latência de endpoints internos se necessário

Boas práticas
- Separe liveness (apenas “estou vivo”) de readiness (pronto para tráfego).
- Use timeouts curtos para cada check; marque Degraded se apenas performance afetada.
- Não acople checks entre serviços (evitar “castelo de cartas”); prefira cache/assincronia para verificações caras.
- Cache de resultados (modo ativo): execute checks em background (artisan command / scheduler) e sirva respostas a partir do cache para reduzir custo e latência.
- Mapear status → HTTP: Healthy/Degraded → 200, Unhealthy → 503 (customizável).
- Proteja endpoints (IP, token interno, mutual TLS) para evitar abuso.
- Log e response com request_id e descrição por check para troubleshooting.

Resposta recomendada (JSON curto)
- { "status":"Healthy", "checks": { "db":"Healthy", "redis":"Degraded" }, "updated":"2026-02-16T..." }

Exemplo mínimo (routes + controller + comando para cache)

```php
// ...existing code...
use App\Http\Controllers\HealthController;
Route::get('/health/liveness', [HealthController::class, 'liveness']);
Route::get('/health/readiness', [HealthController::class, 'readiness']);
```

```php
// filepath: app/Http/Controllers/HealthController.php
// ...existing code...
<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Http;

class HealthController extends Controller
{
    public function liveness()
    {
        // liveness simples: processo responde
        return response()->json(['status' => 'Healthy'], 200);
    }

    public function readiness()
    {
        // servir do cache se existir (modo ativo)
        $report = Cache::get('health:readiness_report');
        if ($report) {
            $http = ($report['status'] === 'Unhealthy') ? 503 : 200;
            return response()->json($report, $http);
        }
```

// modo passivo: executar checks rápidos (com timeouts)
# Task: Implementar HealthChecks (genérico: Node.js / PHP)

## Contexto
- Objetivo: criar endpoints padronizados de liveness/readiness (opcional startup) e um modo ativo (publisher/cache) para reduzir custo de sondagens, compatível tanto com Node.js quanto PHP/Laravel.
- Valor: integrar harmonicamente com Kubernetes e sistemas de monitoramento, evitando reinícios em cascata e fornecendo dados úteis para troubleshooting.

## Requisitos essenciais
- Endpoints mínimos: `/health/liveness` e `/health/readiness` (opcional `/health/startup`).
- Mapping HTTP: `Healthy/Degraded` → 200, `Unhealthy` → 503 (configurável).
- `liveness`: check leve, sem dependências externas caras.
- `readiness`: checks completos (DB, cache, filas, disco, migrations, env vars), com timeouts por check.
- Modo ativo opcional: background job/command que publica resultado em cache; readiness deve poder servir do cache.
- Cada check deve ter timeout curto (ex.: 200–1000ms) e retornar detalhe (status + mensagem curta).
- Endpoints protegidos (IP allowlist, header token ou internal network). Logs estruturados com correlation id.
- Tests: unitários para cada check; integração que simula falha/recuperação.

## Checklist atômico (ordem de implementação)
- [ ] Criar rotas/endpoints: `/health/liveness`, `/health/readiness` (opcional `/health/startup`).
- [ ] Implementar `liveness` simples (processo responde → 200).
- [ ] Implementar `readiness` passivo: executar checks rápidos (DB ping, cache ping, disk free, env vars).
- [ ] Adicionar timeouts por check; transformar timeouts em `Degraded` ou `Unhealthy` conforme críticoidade.
- [ ] Estruturar resposta JSON: `{status, checks:{key:{status,detail?}}, updated}`.
- [ ] Implementar logs estruturados no fluxo do endpoint (incluir `request_id`).
- [ ] Criar testes unitários para cada check (mocks que forçam success/fail/timeout).
- [ ] Implementar modo ativo: comando/task agendado que executa checks e grava resultado em cache (TTL configurável).
- [ ] Alterar `readiness` para servir do cache quando modo ativo estiver habilitado.
- [ ] Implementar proteção simples do endpoint (token/header ou IP filter).
- [ ] Documentar thresholds, mapping de status e como proteger endpoint no README.
- [ ] Fornecer exemplos de `livenessProbe`/`readinessProbe` do Kubernetes com initialDelay/period/timeout.
- [ ] Adicionar validações no CI: rodar testes e validar health endpoints em container de teste.

## O que checar (sugestões por prioridade)
- Críticos (marcam `Unhealthy` se falham): DB (connection/ping), migrations applied, secrets/envs obrigatórias.
- Altamente importantes (podem marcar `Degraded`): Redis/cache (ping / set-get), queue broker connectivity (ping basic), disk free above threshold.
- Informativos: endpoints de terceiros (usar cache/async), métricas internas (latency samples).

## Recomendações de implementação (Node.js / PHP)
- Node.js: Express/Fastify middleware + per-check Promise.race com timeout; usar clients com timeout configurado.
- PHP (Laravel): Controller + Artisan Command para modo ativo; usar `DB::connection()->getPdo()`, `Cache`/`Redis` ping, `disk_free_space()`.
- Cache ativo: Redis ou Cache driver, TTL curto (30–90s), publicar `{status,checks,updated}`.
- Timeouts: aplicar abort/cancel quando possível; mapear timeout → `Degraded` a menos que seja crítico.
- Evitar checks encadeados entre serviços; marque dependências de outras apps como informativas ou cacheadas.

## Exemplo JSON de resposta
```json
{
  "status": "Degraded",
  "checks": {
    "db": {"status":"Healthy"},
    "redis": {"status":"Degraded","detail":"timeout 500ms"},
    "disk_free_mb": {"status":"Healthy","value":1024}
  },
  "updated": "2026-02-16T12:00:00Z"
}
```

## Exemplos rápidos (snippets)
- Kubernetes probe exemplo:
```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 15
  timeoutSeconds: 3
```

- Laravel minimal (controller skeleton):
```php
<?php
namespace App\Http\Controllers;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;

class HealthController extends Controller
{
    public function liveness()
    {
        return response()->json(['status'=>'Healthy'], 200);
    }

    public function readiness()
    {
        $report = Cache::get('health:readiness_report');
        if ($report) return response()->json($report, $report['status']==='Unhealthy'?503:200);

        // passive quick checks (simplified)
        $checks = [];
        $overall = 'Healthy';
        try { DB::connection()->getPdo(); $checks['db'] = 'Healthy'; } catch (\Throwable $e) { $checks['db']='Unhealthy'; $overall='Unhealthy'; }
        try { Redis::ping(); $checks['redis']='Healthy'; } catch (\Throwable $e) { $checks['redis']='Degraded'; if($overall!=='Unhealthy') $overall='Degraded'; }

        $report = ['status'=>$overall,'checks'=>$checks,'updated'=>now()->toIso8601String()];
        return response()->json($report, $overall==='Unhealthy'?503:200);
    }
}
```

## Critérios de aceitação
- [ ] `/health/liveness` responde 200 em container saudável.
- [ ] `/health/readiness` responde 200 quando dependências críticas OK.
- [ ] `/health/readiness` responde 503 quando DB simulado está down.
- [ ] Background publisher grava cache e readiness serve do cache quando habilitado.
- [ ] Exemplos de Kubernetes probes funcionam com as configurações fornecidas.
- [ ] Endpoints protegidos e documentados.

## Observações finais
- Use `Degraded` para problemas de performance; reserve `Unhealthy` para indisponibilidade real.
- Ajuste thresholds e lista de dependências ao contexto do serviço.

- readiness fail → remoção do pod do balanceamento (útil quando dependências não estão OK).
