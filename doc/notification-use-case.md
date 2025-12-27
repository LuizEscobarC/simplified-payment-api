### Caso de Uso: Notificação de Transferência

Após transferência bem-sucedida, o sistema despacha job assíncrono para notificar o destinatário via serviço terceiro.
Utiliza mock https://util.devi.tools/api/v1/notify com POST, enviando ID da transação e mensagem.
Registra evento localmente em caso de sucesso ou falha, garantindo resiliência contra indisponibilidades do serviço.