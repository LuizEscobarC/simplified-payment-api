 
 # DB plan
 - [ ] modelagem de banco de dados mysql para usuários, lojistas, transações, notificações, auditoria e logs.
 - [ ] criar migrations para todas as tabelas.
 - [ ] criar seeders para popular tabelas com dados iniciais. (cadastro não será avaliado).
 - [ ] criar factorys para popular tabelas com dados de teste.
 - [ ] criar índices para otimizar consultas frequentes sem prejudicar os campos a serem atualizados.
 - [ ] para testes de integração utilizar banco em memória sqlite.

 # Setup inicial do projeto
 - [ ] implementar microserviço em python para subir automaticamente os serviços docker localmente seguindo as boas praticas de cultura devops.
 
 
 
 - [ ] implementar uma estrutura de ci para continuos integration no github actions merge.
 - [ ] implementar o git hooks para padronizar commits, branches, rodar testes, linting e formatação.
 - [ ] implementar laravel 11 e estrutura inicial
  - [ ] 
 - [ ] implementar setup inicial de testes basicos.
 - [ ] planejar pattern a serem utilizados para solucionar os problemas.
 - [ ] planejar arquitetura do sistema.
  - [ ] utilizar restful api
  - [ ] utilizar arquitetura em camadas
  - [ ] utilizar design patterns:
    - [ ] repository pattern
    - [ ] decorator pattern para cache
    - [ ] service layer pattern para use cases
    - [ ] strategy pattern para split de pagamento.
    - [ ] factory pattern para criação de estratégias de pagamento.
    - [ ] observer pattern para eventos do sistema.
    - [ ] circuit breaker para chamadas externas.
    - [ ] event sourcing para auditoria.
    - [ ] facade pattern para observabilidade e monitoramento.
    - [ ] innoDB com transactions para garantir integridade e atomicidade de dados nas transações financeiras (não tem como fazer 2 saques do mesmo valor ao mesmo tempo resulta em problemas).
    - [ ] utilizar redis  queue como mensage broker para integrações externas.
    - [ ] utilizar redis cache para otimização de consultas frequentes.
    - [ ] utilizar redis queue para processamento de transações.
    - [ ] utilizar Rules Engine para regras de negócio.
    - [ ] utilizar o pattern State Machine para gerenciar os estados das transações financeiras.
- [ ] utilizar mongo para armazenamento de logs e auditoria.
- [ ] mongo para armazenamento de eventos do sistema.
- [ ] começar com testes de integração tdd
- [ ] testes unitários vem por último para refinar e cobrir toda a aplicação.
- [ ] tdd é melhor em soluções delicadas.

- [ ] aplicar Circuit breaker + observabilidade + Redundancia/fallback + retry e backoff exponencial para chamadas externas (imaginando que seja idempotente, circuit breaker).



# regras de negócio
  - Para ambos tipos de usuário, precisamos do Nome Completo, CPF, e-mail e Senha. CPF/CNPJ e e-mails devem ser únicos no sistema. Sendo assim, seu sistema deve permitir apenas um cadastro com o mesmo CPF ou endereço de e-mail;
  - Usuários podem enviar dinheiro (efetuar transferência) para lojistas e entre usuários;
  - Lojistas só recebem transferências, não enviam dinheiro para ninguém;
  - Validar se o usuário tem saldo antes da transferência;
  - Antes de finalizar a transferência, deve-se consultar um serviço autorizador externo, use este mock https://util.devi.tools/api/v2/authorize para simular o serviço utilizando o verbo GET;
  - A operação de transferência deve ser uma transação (ou seja, revertida em qualquer caso de inconsistência) e o dinheiro deve voltar para a carteira do usuário que envia;
  - No recebimento de pagamento, o usuário ou lojista precisa receber notificação (envio de email, sms) enviada por um serviço de terceiro e eventualmente este serviço pode estar indisponível/instável. Use este mock https://util.devi.tools/api/v1/notify)) para simular o envio da notificação utilizando o verbo POST;
  - Este serviço deve ser RESTFul.

## Endpoint de transferência
 - Você pode implementar o que achar conveniente, porém vamos nos atentar somente ao fluxo de transferência entre dois usuários. A implementação deve seguir o contrato abaixo.
  
```json
POST /transfer
Content-Type: application/json

{
  "value": 100.0,
  "payer": 4,
  "payee": 15
}
```

## Avaliação
Apresente sua solução utilizando o framework que você desejar, justificando a escolha. Atente-se a cumprir a maioria dos requisitos, pois você pode cumprir-los parcialmente e durante a avaliação vamos bater um papo a respeito do que faltou.

* Conhecimentos sobre REST
* Uso do Git
* Capacidade analítica
* Apresentação de código limpo e organizado

* Aderência a recomendações de implementação como as PSRs
* Aplicação e conhecimentos de SOLID
* Identificação e aplicação de Design Patterns
* Noções de funcionamento e uso de Cache
* Conhecimentos sobre conceitos de containers (Docker, Podman etc)
* Documentação e descrição de funcionalidades e manuseio do projeto
* Implementação e conhecimentos sobre testes de unidade e integração
* Identificar e propor melhorias
* Boas noções de bancos de dados relacionais
* Aplicação de conhecimentos de observabilidade
* Utilização de CI para rodar testes e análises estáticas
* Conhecimentos sobre bancos de dados não-relacionais
* Aplicação de arquiteturas (CQRS, Event-sourcing, Microsserviços, Monolito modular)
* Uso e implementação de mensageria
* Noções de escalabilidade
* Boas habilidades na aplicação do conhecimento do negócio no software
* Implementação margeada por ferramentas de qualidade (análise estática, PHPMD, PHPStan, PHP-CS-Fixer etc)
* Noções de PHP assíncrono