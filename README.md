# Simplified Payment API

Uma API RESTful para transferências financeiras simplificadas, desenvolvida com foco em práticas de fintech, segurança e escalabilidade. Implementada em Laravel 11 (PHP).

## Visão Geral

Este projeto simula um sistema de pagamentos onde usuários podem transferir dinheiro para outros usuários ou lojistas. Inclui validações de saldo, autorizações externas, notificações e auditoria completa, seguindo padrões de compliance (LGPD, PCI-DSS).

### Funcionalidades Principais

### Endpoint Principal
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

## Instalação e Setup

## Uso

## Desenvolvimento

### Estrutura de Pastas

## Segurança e Compliance

## Melhorias Futuras

## Justificativas Técnicas

## Licença

Este projeto é para fins educacionais.