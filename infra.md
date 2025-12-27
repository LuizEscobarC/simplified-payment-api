# Infra Makefiles

Aqui vai uma explicação simples do que cada comando dos Makefiles faz. Temos dois Makefiles: um na raiz do projeto e outro em infra/docker. Eles ajudam a automatizar tarefas de desenvolvimento e infraestrutura.

## Makefile na Raiz

- **help**: Mostra uma lista de comandos disponíveis com descrições.
- **setup**: Prepara o ambiente Python criando um virtual environment e instalando dependências.
- **start**: Inicia os serviços básicos usando o orquestrador Python.
- **start-force**: Inicia os serviços ignorando falhas parciais.
- **start-monitoring**: Inicia os serviços incluindo monitoramento.
- **hooks**: Configura hooks do Git para qualidade de código.
- **status**: Mostra o status dos serviços.
- **stop**: Para todos os serviços.
- **clean**: Limpa containers e volumes do Docker.
- **test**: Roda os testes PHP usando PHPUnit.
- **lint**: Executa linters PHP (Pint e PHPStan) para verificar qualidade do código.
- **pint**: Usa Pint para corrigir o estilo do código PHP.
- **fix-permissions**: Ajusta permissões de arquivos para edição no host.
- **all**: Faz setup completo, inicia serviços e configura hooks em um comando só.

## Git Hooks Automáticos

O comando `make hooks` ou `make all` configura automaticamente os Git hooks usando Husky:

- **Pre-commit**: Executa Laravel Pint, PHP-CS-Fixer e PHPMD antes de cada commit
- **Pre-push**: Executa PHPStan antes de cada push

Os hooks rodam dentro dos containers Docker para garantir consistência.

## Makefile em infra/docker

- **help**: Mostra ajuda com comandos disponíveis.
- **setup**: Prepara ambiente Python (venv + dependências).
- **start**: Inicia serviços básicos via orquestrador.
- **start-force**: Inicia serviços ignorando falhas parciais.
- **start-monitoring**: Inicia serviços + monitoramento.
- **hooks**: Configura Git hooks para qualidade.
- **status**: Mostra status dos serviços.
- **stop**: Para serviços.
- **clean**: Limpa containers e volumes.
- **test**: Roda testes PHP.
- **lint**: Executa linters (Pint e PHPStan).
- **pint**: Corrige estilo com Pint.
- **fix-permissions**: Ajusta permissões de arquivos.
- **all**: Setup completo + serviços + hooks.

Esses comandos facilitam a vida no desenvolvimento, deixando tudo mais automático e organizado.