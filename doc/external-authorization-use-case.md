### Caso de Uso: Autorização Externa de Transferência

Antes de concluir uma transferência, o sistema consulta um serviço autorizador externo via GET para validar a operação.
Utiliza o mock https://util.devi.tools/api/v2/authorize, verificando resposta com status 'success' e autorização positiva.
Em caso de falha, impede a transferência e registra erro para proteção contra indisponibilidades.