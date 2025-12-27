# scripts/env_manager.py
"""
Módulo para gerenciamento de arquivos .env durante o build do Laravel.

Este módulo fornece funções para validar e carregar variáveis de ambiente
necessárias para o funcionamento do Laravel no Docker.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv, dotenv_values
from rich.console import Console

console = Console()


class LaravelEnvManager:
    """Gerenciador de .env para Laravel no Docker."""

    def __init__(self, env_file: str = ".env", example_file: str = ".env.example"):
        """
        Inicializa gerenciador de .env para Laravel.

        Args:
            env_file: Caminho do arquivo .env
            example_file: Caminho do arquivo .env.example
        """
        self.env_file = Path(env_file)
        self.example_file = Path(example_file)
        self.required_vars = [
            # Banco de dados principal
            'DB_CONNECTION', 'DB_HOST', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD',
            # Banco de dados MongoDB
            'DB_DADOS_CONNECTION', 'DB_DADOS_HOST', 'DB_DADOS_DATABASE',
            'DB_DADOS_USERNAME', 'DB_DADOS_PASSWORD',
            # Redis
            'REDIS_HOST', 'REDIS_PORT',
            # Aplicação
            'APP_ENV', 'APP_ROOT',
            # Filas
            'QUEUE_CONNECTION'
        ]
        
        # Variáveis que podem ser vazias
        self.optional_vars = ['QUEUE_OPTIONS', 'REDIS_PASSWORD']

    def validate_env_file(self) -> bool:
        """
        Valida se o arquivo .env existe e tem as variáveis necessárias.
        Se não existir, copia do .env.example.
        Se existir, verifica se todas as variáveis do .env.example estão presentes.

        Returns:
            True se válido
        """
        if not self.env_file.exists():
            if self.example_file.exists():
                console.print(f"[yellow]⚠ Arquivo .env não encontrado, copiando de {self.example_file}...[/yellow]")
                import shutil
                shutil.copy(self.example_file, self.env_file)
                console.print(f"[green]✓[/green] Arquivo .env criado a partir de {self.example_file}")
            else:
                console.print(f"[red]✗ Arquivo .env e .env.example não encontrados[/red]")
                return False
        else:
            # Arquivo .env existe, verificar se tem todas as variáveis necessárias
            self._ensure_all_env_vars()

        console.print(f"[green]✓[/green] Arquivo .env encontrado: {self.env_file}")
        return True

    def _ensure_all_env_vars(self) -> None:
        """
        Garante que o .env tenha todas as variáveis do .env.example.
        Adiciona as faltantes ao final do arquivo.
        """
        if not self.example_file.exists():
            return

        # Carregar variáveis do .env.example
        example_vars = dotenv_values(self.example_file)
        
        # Carregar variáveis do .env atual
        current_vars = dotenv_values(self.env_file)
        
        # Encontrar variáveis faltantes
        missing_vars = []
        for key, value in example_vars.items():
            if key not in current_vars:
                missing_vars.append((key, value))
        
        if not missing_vars:
            return
        
        console.print(f"[yellow]⚠ Encontradas {len(missing_vars)} variáveis faltando no .env, adicionando...[/yellow]")
        
        # Adicionar variáveis faltantes ao final do arquivo
        with open(self.env_file, 'a', encoding='utf-8') as f:
            f.write("\n# Variáveis adicionadas automaticamente do .env.example\n")
            for key, value in missing_vars:
                f.write(f"{key}={value}\n")
        
        console.print(f"[green]✓[/green] {len(missing_vars)} variáveis adicionadas ao .env")

    def validate_required_vars(self) -> Dict[str, bool]:
        """
        Valida se todas as variáveis do .env.example estão presentes no .env.

        Returns:
            Dicionário com status de cada variável
        """
        if not self.validate_env_file():
            return {}

        # Carregar todas as variáveis do .env.example como obrigatórias
        if not self.example_file.exists():
            console.print(f"[red]✗ Arquivo .env.example não encontrado[/red]")
            return {}

        example_vars = dotenv_values(self.example_file)
        current_vars = dotenv_values(self.env_file)
        
        validation = {}
        missing = []

        # Lista de variáveis que podem ser vazias
        optional_empty_vars = [
            'APP_KEY',  # Será gerado
            'QUEUE_OPTIONS',
            'REDIS_PASSWORD',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY', 
            'AWS_DEFAULT_REGION',
            'AWS_BUCKET',
            'AWS_USE_PATH_STYLE_ENDPOINT',
            'PUSHER_APP_ID',
            'PUSHER_APP_KEY',
            'PUSHER_APP_SECRET',
            'PUSHER_HOST',
            'VITE_PUSHER_APP_KEY',
            'VITE_PUSHER_HOST',
            'VITE_PUSHER_PORT',
            'VITE_PUSHER_SCHEME',
            'VITE_PUSHER_APP_CLUSTER'
        ]

        # Validar todas as variáveis do .env.example
        for var in example_vars.keys():
            value = current_vars.get(var)
            if var in optional_empty_vars:
                exists = value is not None  # Permite vazio
            elif var == 'APP_KEY':
                exists = value is not None  # APP_KEY pode ser vazio inicialmente
            else:
                exists = value is not None and value.strip() != ""
            validation[var] = exists

            if not exists:
                missing.append(var)

        if missing:
            console.print(f"[red]✗ Variáveis faltando no .env:[/red]")
            for var in missing:
                console.print(f"  - {var}")
            return validation

        console.print(f"[green]✓[/green] Todas as variáveis do .env.example estão presentes no .env")
        return validation

    def load_env_vars(self) -> bool:
        """
        Carrega as variáveis do .env para o ambiente.

        Returns:
            True se carregou com sucesso
        """
        if not self.validate_env_file():
            return False

        try:
            load_dotenv(self.env_file, override=True)
            console.print(f"[green]✓[/green] Variáveis carregadas de {self.env_file}")

            # Verificar se algumas variáveis críticas foram carregadas
            db_host = os.getenv('DB_HOST')
            redis_host = os.getenv('REDIS_HOST')

            if db_host:
                console.print(f"[blue]ℹ[/blue] DB_HOST: {db_host}")
            if redis_host:
                console.print(f"[blue]ℹ[/blue] REDIS_HOST: {redis_host}")

            return True

        except Exception as e:
            console.print(f"[red]✗ Erro ao carregar {self.env_file}: {e}[/red]")
            return False

    def get_env_summary(self) -> Dict[str, str]:
        """
        Retorna resumo das variáveis de ambiente importantes.

        Returns:
            Dicionário com variáveis importantes
        """
        summary = {}
        important_vars = [
            'APP_NAME', 'APP_ENV', 'APP_KEY', 'APP_DEBUG', 'APP_URL',
            'DB_CONNECTION', 'DB_HOST', 'DB_DATABASE', 'DB_USERNAME',
            'DB_DADOS_CONNECTION', 'DB_DADOS_HOST', 'DB_DADOS_DATABASE',
            'REDIS_HOST', 'REDIS_PORT', 'QUEUE_CONNECTION',
            'MAIL_MAILER', 'CACHE_DRIVER', 'SESSION_DRIVER'
        ]

        for var in important_vars:
            value = os.getenv(var, 'NOT_SET')
            # Mascarar senhas
            if 'PASSWORD' in var or 'PASS' in var or 'SECRET' in var or 'KEY' in var:
                value = '***' if value and value != 'NOT_SET' else value
            summary[var] = value

        return summary

    def setup_laravel_env(self) -> bool:
        """
        Configura o ambiente Laravel validando e carregando .env.

        Returns:
            True se configurado com sucesso
        """
        console.print("[cyan]🔧 Configurando ambiente Laravel...[/cyan]")

        # Validar arquivo
        if not self.validate_env_file():
            return False

        # Validar variáveis obrigatórias
        validation = self.validate_required_vars()
        if not all(validation.values()):
            # Tentar adicionar variáveis faltantes
            self._ensure_all_env_vars()
            # Re-validar após adicionar
            validation = self.validate_required_vars()
            if not all(validation.values()):
                return False

        # Carregar variáveis
        if not self.load_env_vars():
            return False

        # Exibir resumo
        summary = self.get_env_summary()
        console.print("[cyan]📋 Resumo da configuração:[/cyan]")
        for key, value in summary.items():
            console.print(f"  {key}: {value}")

        console.print("[green]✓ Ambiente Laravel configurado com sucesso[/green]")
        return True