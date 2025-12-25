# Casos de Uso e Regras - API de Pagamentos Simplificada

## Casos de Uso
- [x] Transferência bem-sucedida entre usuários comuns (payer envia, payee recebe, saldo atualizado)
- [x] Transferência bem-sucedida de usuário comum para lojista (payer envia, lojista recebe)
- [x] Falha na transferência por saldo insuficiente (validação antes de autorizar)
- [x] Falha na transferência por rejeição do autorizador externo (rollback automático)
- [x] Falha na transferência por erro interno (rollback da transação)
- [x] Envio de notificação para o recebedor após transferência bem-sucedida (email ou SMS)
- [x] Idempotência na transferência (mesmo correlation_id não duplica a operação)
- [x] Logs de auditoria para todas as tentativas de transferência (sucesso ou falha)

## Regras de Negócio
- [x] CPF/CNPJ e e-mails devem ser únicos no sistema
- [x] Apenas usuários comuns podem enviar dinheiro
- [x] Lojistas só podem receber transferências
- [x] Saldo insuficiente impede a transferência
- [x] Autorização externa deve ser aprovada antes de finalizar
- [x] Transação deve ser revertida em qualquer inconsistência
- [x] Notificação deve ser enviada após recebimento de pagamento
- [x] Endpoint POST /transfer com campos: value, payer, payee, correlation_id
- [x] Respostas padronizadas: 200 (sucesso), 400 (erro de validação), 422 (regra violada), 500 (erro interno)