# Simplified Payment API

Uma API RESTful para transferências financeiras simplificadas, desenvolvida com foco em práticas de fintech, segurança e escalabilidade. Implementada em Laravel 11 (PHP).

## Visão Geral

Este projeto simula um sistema de pagamentos onde usuários podem transferir dinheiro para outros usuários ou lojistas. Inclui validações de saldo, autorizações externas, notificações e auditoria completa, seguindo padrões de compliance (LGPD, PCI-DSS).

### Funcionalidades Principais

- **Cadastro de Usuários**: Permite registrar usuários comuns e lojistas com nome, CPF/CNPJ, e-mail e senha únicos, evitando duplicatas.
- **Transferências Seguras**: Usuários podem enviar dinheiro para outros usuários ou lojistas, sempre validando saldo disponível e autorização externa.
- **Transações Atômicas**: Toda transferência é feita em uma transação que reverte automaticamente em caso de erro, garantindo integridade.
- **Notificações**: Após sucesso, o sistema notifica os envolvidos de forma assíncrona, lidando bem com falhas de serviços externos.
- **API RESTful**: Endpoints simples e padronizados para facilitar integrações, com respostas em JSON e códigos de status claros.

### Endpoint Principal

Para fazer uma transferência, basta enviar um POST para /transfer com os dados do valor, quem paga e quem recebe. O sistema cuida de todas as validações e responde rapidinho se deu certo ou não.

```http
POST /transfer
Content-Type: application/json

{
  "value": 100.0,
  "payer": 4,
  "payee": 15
}
```

## Arquitetura

Para visualizar os diagramas de arquitetura na pasta `/doc` (arquivos .puml), você precisa instalar uma extensão no VS Code. É simples:

1. Abra o VS Code e vá para a aba de Extensões (ícone de quadrado com uma peça faltando, ou Ctrl+Shift+X).
2. No campo de busca, digite "PlantUML" e selecione a extensão oficial de "jebbs".
3. Clique em "Instalar" e aguarde.
4. Pronto! Agora, abra qualquer arquivo .puml em `/doc` (como `architecture_diagram.puml`), e use o comando "PlantUML: Preview Current Diagram" (ou clique com o botão direito no arquivo e selecione "Preview Diagram") para ver o diagrama renderizado.

Isso facilita entender a estrutura do sistema sem precisar de ferramentas externas.

## Instalação e Setup

Para subir tudo rapidinho, vá na pasta `infra/docker` e rode `make all`. Isso usa o orquestrador Python para preparar o ambiente virtual, instalar dependências e subir os serviços via Docker Compose (Laravel, MySQL, Redis, MongoDB, Nginx). Os arquivos Python cuidam da automação, os docker-compose.yml definem os containers, e os Makefiles facilitam comandos como `make test` (na raiz) para rodar testes ou `make start` (em infra/docker) para subir serviços. É tudo automatizado, mas se precisar ajustar, olhe os scripts em `infra/docker/scripts` e `services`.

Se quiser usar valores customizados para variáveis de ambiente, altere nos arquivos docker-compose.yml e no .env na raiz dentro de api/, pois o sistema copia automaticamente do .env.example do infra para o .env da api se estiver faltando.

Para testar o código, use o Makefile na raiz: `make test` roda os testes PHP (52 testes passando), `make lint` verifica estilo com Pint e análise com PHPStan, `make pint` corrige estilo automaticamente. Tudo executa no container Docker para consistência.

O setup também configura automaticamente os Git hooks (pre-commit e pre-push) para manter a qualidade do código, executando linters e testes antes de commits e pushes.

*Para mais detalhes leia o arquivo infra.md, existe um comando para cada situação.*

## Uso

A API é RESTful e usa JSON para tudo. Quando rodando localmente, a base é http://localhost/api.

### Autenticação
Usa Laravel Sanctum. Faça POST /login com email e senha para pegar o token, depois inclua no header: `Authorization: Bearer {seu_token}` nas requisições que precisam.

### Endpoints Principais
- **POST /transfer**: Faz transferência (value, payer_id, payee_id) - só logado, valida saldo e autorização externa
- **GET /test**: Teste

Respostas sempre em JSON com códigos HTTP claros (200 OK, 401 Unauthorized, 422 Validation Error, etc.). Use Postman ou curl para testar.

## Desenvolvimento

### Estrutura de Pastas

- **api/**: Código Laravel (app/ com Models/Controllers/Services; config/; routes/api.php; tests/ com 52 testes)
- **infra/**: Infraestrutura Docker (docker/ com Compose files para app/databases/cache/monitoring; scripts Python para orquestração; orchestrator.py que sobe tudo automaticamente)
- **doc/**: Diagramas e docs (arquivos .puml para arquitetura, .md para use cases)
- **prompts/**: Arquivos de prompt para guiar desenvolvimento
- **Makefile**: Na raiz, para testes/lint/setup (make test, make lint, start, entre outros)
- **infra.md**: Explica todos os comandos dos Makefiles

## Segurança e Compliance

A API prioriza segurança e compliance para lidar com dados financeiros. Usamos Laravel Sanctum para autenticação baseada em tokens (apesar de não utilizada). Todas as validações (saldo, autorização externa) previnem fraudes, e as transações são atômicas para evitar inconsistências.

Para compliance, seguimos LGPD (proteção de dados pessoais, como CPF/CNPJ e emails únicos) e PCI-DSS (segurança em pagamentos, com dados criptografados e auditoria completa). 

LGPD: Dados pessoais como CPF/CNPJ e e-mails são únicos (restrições unique na migração e testes validam isso), protegendo contra duplicatas e garantindo integridade.
PCI-DSS: Senhas são armazenadas com hash seguro (padrão Laravel com bcrypt), transferências validam saldo e autorização externa, e notificações são assíncronas via jobs (não expõem dados em tempo real). Eventos de auditoria (usando Event model) rastreiam todas as operações (início de transferência, atualização de saldos, notificações), assegurando rastreabilidade completa. Transações atômicas previnem fraudes, e dados são criptografados onde necessário (ex.: conexões seguras).

## Justificativas Técnicas

O sistema usa Laravel 11 para API robusta e escalável, com PHP 8.3 para performance. Transações atômicas (DB::transaction) garantem integridade financeira, revertendo tudo em falhas. Event sourcing (MongoDB) rastreia mudanças imutáveis para auditoria. Circuit breaker protege contra falhas no autorizador externo, abrindo após 5 erros. Notificações assíncronas via Redis queues evitam bloqueios. Diagramas PlantUML mostram arquitetura clara: Nginx proxy, Laravel app, bancos separados (MySQL para transações, Mongo para eventos, Redis para cache/filas). Testes unitários e feature (52 no total) validam regras, como idempotência e validações. Repositórios e policies seguem SOLID para manutenção. Tudo containerizado com Docker para consistência.

Não deu tempo de aplicar todas as ideias que tenho, mas será uma hora explicar quais seriam os próximos passos (observabilidade, segurança, projections + sharding de banco, balanceamento com ngix, worker para transferencias, fallback para outro autorizador caso o primeiro esteja falhando, ao inves de somente recusar no circuit, entre outros). 

Atenciosamente Luiz :'^) .


## Licença

Este projeto é para fins educacionais.