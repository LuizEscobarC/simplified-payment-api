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

    def __init__(self, env_file: str = ".env"):
        """
        Inicializa gerenciador de .env para Laravel.

        Args:
            env_file: Caminho do arquivo .env
        """
        self.env_file = Path(env_file)
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

        Returns:
            True se válido
        """
        if not self.env_file.exists():
            console.print(f"[red]✗ Arquivo .env não encontrado: {self.env_file}[/red]")
            return False

        console.print(f"[green]✓[/green] Arquivo .env encontrado: {self.env_file}")
        return True

    def validate_required_vars(self) -> Dict[str, bool]:
        """
        Valida se todas as variáveis obrigatórias estão presentes.

        Returns:
            Dicionário com status de cada variável
        """
        if not self.validate_env_file():
            return {}

        vars_dict = dotenv_values(self.env_file)
        validation = {}
        missing = []

        # Validar obrigatórias (devem ter valor não vazio)
        for var in self.required_vars:
            value = vars_dict.get(var)
            exists = value is not None and value.strip() != ""
            validation[var] = exists

            if not exists:
                missing.append(var)

        # Validar opcionais (podem ser vazias)
        for var in self.optional_vars:
            value = vars_dict.get(var)
            exists = value is not None  # Apenas verifica se existe, pode ser vazio
            validation[var] = exists

            if not exists:
                missing.append(var)

        if missing:
            console.print(f"[red]✗ Variáveis obrigatórias faltando:[/red]")
            for var in missing:
                console.print(f"  - {var}")
            return validation

        console.print(f"[green]✓[/green] Todas as variáveis obrigatórias e opcionais presentes")
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
        Retorna resumo das variáveis de ambiente carregadas.

        Returns:
            Dicionário com variáveis importantes
        """
        summary = {}
        important_vars = [
            'DB_CONNECTION', 'DB_HOST', 'DB_DATABASE',
            'DB_DADOS_CONNECTION', 'DB_DADOS_HOST', 'DB_DADOS_DATABASE',
            'REDIS_HOST', 'REDIS_PORT',
            'APP_ENV', 'QUEUE_CONNECTION'
        ]

        for var in important_vars:
            value = os.getenv(var, 'NOT_SET')
            # Mascarar senhas
            if 'PASSWORD' in var or 'PASS' in var:
                value = '***' if value != 'NOT_SET' else value
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