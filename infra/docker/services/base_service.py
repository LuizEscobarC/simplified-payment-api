# scripts/services/base_service.py
"""
Classe base para serviços do sistema.

Define a interface comum para todos os serviços do sistema,
incluindo inicialização, validação e execução.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import docker
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..env_manager import EnvManager
from ..docker_service import DockerService
from ..logger_setup import get_logger

console = Console()
logger = get_logger(__name__)


class BaseService(ABC):
    """
    Classe base abstrata para todos os serviços.

    Define a interface comum e funcionalidades compartilhadas
    entre todos os serviços do sistema.
    """

    def __init__(
        self,
        name: str,
        env_file: str = ".env",
        base_path: Optional[Path] = None
    ):
        """
        Inicializa serviço base.

        Args:
            name: Nome do serviço
            env_file: Arquivo .env a usar
            base_path: Diretório base do serviço
        """
        self.name = name
        self.base_path = base_path or Path.cwd()
        self.env_file = self.base_path / env_file

        # Componentes compartilhados
        self.env_manager = EnvManager(env_file)
        self.docker_client = docker.from_env()

        # Estado do serviço
        self._initialized = False
        self._validated = False

        logger.debug(f"Serviço {name} inicializado")

    @property
    def is_initialized(self) -> bool:
        """Retorna se o serviço foi inicializado."""
        return self._initialized

    @property
    def is_validated(self) -> bool:
        """Retorna se o serviço foi validado."""
        return self._validated

    @abstractmethod
    def get_required_vars(self) -> List[str]:
        """
        Retorna lista de variáveis de ambiente obrigatórias.

        Returns:
            Lista de nomes de variáveis obrigatórias
        """
        pass

    @abstractmethod
    def get_service_config(self) -> Dict[str, Any]:
        """
        Retorna configuração específica do serviço.

        Returns:
            Dicionário com configuração do serviço
        """
        pass

    def initialize(self) -> bool:
        """
        Inicializa o serviço.

        Returns:
            True se inicializou com sucesso
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Inicializando {self.name}..."),
                console=console
            ) as progress:
                task = progress.add_task("", total=3)

                # 1. Configurar ambiente
                progress.update(task, advance=1, description=f"[cyan]Configurando ambiente para {self.name}...")
                if not self._setup_environment():
                    return False

                # 2. Carregar variáveis
                progress.update(task, advance=1, description=f"[cyan]Carregando variáveis para {self.name}...")
                if not self._load_environment():
                    return False

                # 3. Validar pré-requisitos
                progress.update(task, advance=1, description=f"[cyan]Validando pré-requisitos para {self.name}...")
                if not self._validate_prerequisites():
                    return False

            self._initialized = True
            console.print(f"✅ {self.name} inicializado com sucesso", style="green")
            logger.info(f"Serviço {self.name} inicializado com sucesso")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao inicializar {self.name}: {e}", style="red")
            logger.error(f"Erro ao inicializar {self.name}: {e}")
            return False

    def validate(self) -> bool:
        """
        Valida configuração e estado do serviço.

        Returns:
            True se válido
        """
        try:
            if not self.is_initialized:
                console.print(f"⚠️  {self.name} não foi inicializado", style="yellow")
                return False

            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Validando {self.name}..."),
                console=console
            ) as progress:
                task = progress.add_task("", total=2)

                # 1. Validar variáveis obrigatórias
                progress.update(task, advance=1, description=f"[cyan]Validando variáveis para {self.name}...")
                if not self._validate_required_vars():
                    return False

                # 2. Validar configuração específica
                progress.update(task, advance=1, description=f"[cyan]Validando configuração para {self.name}...")
                if not self._validate_service_config():
                    return False

            self._validated = True
            console.print(f"✅ {self.name} validado com sucesso", style="green")
            logger.info(f"Serviço {self.name} validado com sucesso")
            return True

        except Exception as e:
            console.print(f"❌ Erro ao validar {self.name}: {e}", style="red")
            logger.error(f"Erro ao validar {self.name}: {e}")
            return False

    @abstractmethod
    def execute(self) -> bool:
        """
        Executa a lógica principal do serviço.

        Returns:
            True se executou com sucesso
        """
        pass

    def cleanup(self) -> bool:
        """
        Limpa recursos do serviço.

        Returns:
            True se limpou com sucesso
        """
        try:
            console.print(f"🧹 Limpando {self.name}...", style="cyan")
            # Implementação padrão - pode ser sobrescrita
            logger.info(f"Serviço {self.name} limpo")
            return True
        except Exception as e:
            console.print(f"❌ Erro ao limpar {self.name}: {e}", style="red")
            logger.error(f"Erro ao limpar {self.name}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do serviço.

        Returns:
            Dicionário com informações de status
        """
        return {
            "name": self.name,
            "initialized": self._initialized,
            "validated": self._validated,
            "base_path": str(self.base_path),
            "env_file": str(self.env_file),
            "env_file_exists": self.env_file.exists(),
            "config": self.get_service_config()
        }

    def display_status(self):
        """Exibe status do serviço formatado."""
        from rich.panel import Panel
        from rich.table import Table

        status = self.get_status()

        # Tabela principal
        table = Table(title=f"Status do Serviço: {self.name}")
        table.add_column("Propriedade", style="cyan")
        table.add_column("Valor", style="yellow")

        table.add_row("Inicializado", "✅" if status["initialized"] else "❌")
        table.add_row("Validado", "✅" if status["validated"] else "❌")
        table.add_row("Diretório Base", str(status["base_path"]))
        table.add_row("Arquivo .env", str(status["env_file"]))
        table.add_row("Arquivo .env existe", "✅" if status["env_file_exists"] else "❌")

        console.print(table)

        # Configuração específica
        if status["config"]:
            config_table = Table(title="Configuração do Serviço")
            config_table.add_column("Chave", style="cyan")
            config_table.add_column("Valor", style="yellow")

            for key, value in status["config"].items():
                config_table.add_row(key, str(value))

            console.print(config_table)

    # Métodos privados auxiliares

    def _setup_environment(self) -> bool:
        """
        Configura ambiente do serviço.

        Returns:
            True se configurou com sucesso
        """
        try:
            # Criar .env se não existir
            if not self.env_file.exists():
                example_file = self.base_path / ".env.example"
                if example_file.exists():
                    self.env_manager.setup_env(
                        source=example_file,
                        dest=self.env_file
                    )
                else:
                    console.print(f"⚠️  {example_file} não encontrado", style="yellow")

            return True
        except Exception as e:
            console.print(f"❌ Erro ao configurar ambiente: {e}", style="red")
            return False

    def _load_environment(self) -> bool:
        """
        Carrega variáveis de ambiente.

        Returns:
            True se carregou com sucesso
        """
        try:
            if self.env_file.exists():
                self.env_manager.load_env(self.env_file)
            return True
        except Exception as e:
            console.print(f"❌ Erro ao carregar ambiente: {e}", style="red")
            return False

    def _validate_prerequisites(self) -> bool:
        """
        Valida pré-requisitos básicos do serviço.

        Returns:
            True se válidos
        """
        # Implementação padrão - pode ser sobrescrita
        return True

    def _validate_required_vars(self) -> bool:
        """
        Valida variáveis obrigatórias.

        Returns:
            True se válidas
        """
        try:
            required = self.get_required_vars()
            if required:
                self.env_manager.validate_required(required)
            return True
        except Exception as e:
            console.print(f"❌ Erro ao validar variáveis: {e}", style="red")
            return False

    def _validate_service_config(self) -> bool:
        """
        Valida configuração específica do serviço.

        Returns:
            True se válida
        """
        # Implementação padrão - pode ser sobrescrita
        return True