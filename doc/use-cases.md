# Casos de Uso e Regras - API de Pagamentos Simplificada

## Casos de Uso
- [ ] Transferência bem-sucedida entre usuários comuns (payer envia, payee recebe, saldo atualizado)
- [ ] Transferência bem-sucedida de usuário comum para lojista (payer envia, lojista recebe)
- [ ] Falha na transferência por saldo insuficiente (validação antes de autorizar)
- [ ] Falha na transferência por rejeição do autorizador externo (rollback automático)
- [ ] Falha na transferência por erro interno (rollback da transação)
- [ ] Envio de notificação para o recebedor após transferência bem-sucedida (email ou SMS)
- [ ] Idempotência na transferência (mesmo correlation_id não duplica a operação)
- [ ] Logs de auditoria para todas as tentativas de transferência (sucesso ou falha)

## Regras de Negócio
- [ ] CPF/CNPJ e e-mails devem ser únicos no sistema
- [ ] Apenas usuários comuns podem enviar dinheiro
- [ ] Lojistas só podem receber transferências
- [ ] Saldo insuficiente impede a transferência
- [ ] Autorização externa deve ser aprovada antes de finalizar
- [ ] Transação deve ser revertida em qualquer inconsistência
- [ ] Notificação deve ser enviada após recebimento de pagamento
- [ ] Endpoint POST /transfer com campos: value, payer, payee, correlation_id
- [ ] Respostas padronizadas: 200 (sucesso), 400 (erro de validação), 422 (regra violada), 500 (erro interno)