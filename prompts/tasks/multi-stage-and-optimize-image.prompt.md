```markdown
# Task: Otimizar Imagens Docker — Multi-stage e Build eficiente (Node.js / PHP)

## Contexto
- Imagens Docker grandes aumentam tempo de CI/CD, transferência e custo de armazenamento. Esta task padroniza passos para criar imagens pequenas, seguras e reproduzíveis, aplicáveis a projetos Node.js e PHP.

## Objetivo
- Entregar um conjunto verificável de arquivos e práticas: Dockerfile multi-stage, `.dockerignore`, pipeline mínimo (CI), e checklist de validação para garantir imagens otimizadas.

## Requisitos (aplicáveis a Node e PHP)
- Dockerfile multi-stage separando build e runtime.
- Uso de imagem base adequada (slim/alpine) compatível com dependências.
- Combinação de comandos para reduzir camadas e limpeza de caches em cada RUN.
- `.dockerignore` cobrindo artefatos e dependências locais.
- Aproveitamento de cache de dependências (COPY antes de instalar deps).
- Variáveis de build (ex.: DOCKER_TAG, IMAGE_VERSION) e labels para rastreabilidade.
- Script ou pipeline CI que: builda imagem, executa lint básico e publica artefato local ou registry (opcional).
- Métricas/validação: imagem construída reporta tamanho e lista de camadas; smoke test do container.

## Checklist atômico — passos mínimos e verificáveis
- [x] Escolher imagem base adequada (documentar por serviço: Node/PHP).
- [x] Criar `Dockerfile` multi-stage com etapa de build e etapa de runtime.
- [x] Implementar otimizações: combinar comandos RUN, limpar cache em mesma linha, usar `--no-cache` quando aplicável.
- [x] Adicionar `.dockerignore` (node_modules, vendor, tests, docs, .git).
- [x] Reorganizar `COPY` para maximizar cache (copiar arquivos de dependências antes do código fonte).
- [x] Adicionar variáveis `ARG` e `LABEL` para versão/build metadata.
- [x] Adicionar healthcheck mínimo no Dockerfile (`HEALTHCHECK` ou endpoint exposto).
- [x] Criar script de build local que gera imagem com tag e reporta `docker image ls` e `docker history` (tamanho por camada).
- [ ] Implementar pipeline CI básico (GitHub Actions ou similar) que builda imagem e executa `docker run --rm` smoke test.
- [ ] Validar runtime: iniciar container e executar teste HTTP simples ou comando de sanity check.
- [ ] Revisar e reduzir imagem final (remover ferramentas de build, dev deps, arquivos temporários).
- [ ] Documentar instruções de build, tag e push no `README.md` do projeto.

## Exemplos (snippets)

Node.js multi-stage (exemplo resumido):
```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

FROM node:22-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
RUN pnpm install --prod --frozen-lockfile
EXPOSE 3000
CMD ["node","dist/server.js"]
```

PHP (Laravel) multi-stage (exemplo resumido):
```dockerfile
FROM composer:2 AS builder
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader
COPY . .
RUN npm ci && npm run prod || true

FROM php:8.3-fpm-alpine AS runtime
WORKDIR /var/www/html
COPY --from=builder /app /var/www/html
RUN chown -R www-data:www-data /var/www/html
EXPOSE 9000
CMD ["php-fpm"]
```

`.dockerignore` exemplo:
```
node_modules
vendor
.git
tests
.env
coverage
build
```

## Métricas e validação
- Meça imagem antes/depois (comando): `docker image ls IMAGE:TAG`.
- Inspecione camadas: `docker history IMAGE:TAG` e `docker image inspect IMAGE:TAG --format '{{.RootFS.Layers}}'`.
- Smoke test: `docker run --rm -p 8080:3000 IMAGE:TAG curl -f http://localhost:3000/health || exit 1`.

## Integração CI (linha inicial)
- GitHub Actions job mínimo: checkout, build, run smoke test, upload artifact (optional) or push to registry with tag.

## Critérios de aceitação
- [ ] Dockerfile multi-stage presente e documentado.
- [ ] `.dockerignore` adicionada e validada.
- [ ] Build local gera imagem com tamanho aceitável (documentar baseline).
- [ ] Smoke test passa e imagem executa corretamente.
- [ ] Pipeline CI builda e testa a imagem automaticamente.

## Observações
- Prefira segurança: executar processos com usuário non-root quando possível.
- Balanceie tamanho vs funcionalidade: nem sempre a imagem mais pequena é a adequada se faltar libs necessárias.
- Automatize auditorias de imagens e limpezas periódicas no CI/CD.

``` 

