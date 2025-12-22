#!/usr/bin/env python3
"""
Módulo para gerenciamento de redes Docker.

Este módulo fornece funções e classes para criar, listar,
inspecionar e remover redes Docker usando Docker SDK.
"""

import docker
from docker.errors import APIError, NotFound
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()


class DockerNetworkManager:
    """Gerenciador de redes Docker."""

    def __init__(self):
        """
        Inicializa conexão com Docker Engine.

        Raises:
            docker.errors.DockerException: Se não conseguir conectar ao Docker
        """
        try:
            self.client = docker.from_env()
            # Testa conexão
            self.client.ping()
        except docker.errors.DockerException as e:
            console.print(f"[red]✗ Erro ao conectar no Docker: {e}[/red]")
            raise

    def create_network(
        self,
        name: str,
        driver: str = "bridge",
        check_duplicate: bool = True
    ) -> Optional[docker.models.networks.Network]:
        """
        Cria uma rede Docker.

        Args:
            name: Nome da rede
            driver: Driver da rede (bridge, overlay, host, etc.)
            check_duplicate: Se True, verifica existência antes de criar

        Returns:
            Network object se criou, None se já existe

        Raises:
            docker.errors.APIError: Em caso de erro na API
        """
        try:
            network = self.client.networks.create(
                name=name,
                driver=driver,
                check_duplicate=check_duplicate
            )
            console.print(f"[green]✓[/green] Rede '{name}' criada com sucesso")
            return network

        except APIError as e:
            if "already exists" in str(e):
                console.print(f"[yellow]![/yellow] Rede '{name}' já existe")
                return None
            else:
                console.print(f"[red]✗ Erro ao criar rede '{name}': {e}[/red]")
                raise

    def get_network(self, name: str) -> Optional[docker.models.networks.Network]:
        """
        Busca uma rede por nome.

        Args:
            name: Nome da rede

        Returns:
            Network object se existe, None se não encontrada
        """
        try:
            network = self.client.networks.get(name)
            return network
        except NotFound:
            return None
        except APIError as e:
            console.print(f"[red]✗ Erro ao buscar rede '{name}': {e}[/red]")
            raise

    def network_exists(self, name: str) -> bool:
        """
        Verifica se uma rede existe.

        Args:
            name: Nome da rede

        Returns:
            True se existe, False caso contrário
        """
        return self.get_network(name) is not None

    def upsert_network(
        self,
        name: str,
        driver: str = "bridge"
    ) -> docker.models.networks.Network:
        """
        Cria rede se não existir, ou retorna existente.

        Args:
            name: Nome da rede
            driver: Driver da rede

        Returns:
            Network object (criado ou existente)
        """
        network = self.get_network(name)

        if network is None:
            network = self.create_network(name, driver)
        else:
            console.print(f"[cyan]→[/cyan] Usando rede existente '{name}'")

        return network

    def list_networks(self, filters: Optional[Dict[str, Any]] = None) -> List[docker.models.networks.Network]:
        """
        Lista todas as redes Docker.

        Args:
            filters: Filtros opcionais

        Returns:
            Lista de Network objects
        """
        try:
            return self.client.networks.list(filters=filters)
        except APIError as e:
            console.print(f"[red]✗ Erro ao listar redes: {e}[/red]")
            raise

    def remove_network(self, name: str, force: bool = False) -> bool:
        """
        Remove uma rede Docker.

        Args:
            name: Nome da rede
            force: Se True, desconecta containers antes de remover

        Returns:
            True se removeu, False se não existe

        Raises:
            docker.errors.APIError: Se rede está em uso e force=False
        """
        network = self.get_network(name)

        if network is None:
            console.print(f"[yellow]![/yellow] Rede '{name}' não existe")
            return False

        try:
            if force:
                # Desconectar todos os containers
                network.reload()
                for container in network.containers:
                    network.disconnect(container, force=True)

            network.remove()
            console.print(f"[green]✓[/green] Rede '{name}' removida")
            return True

        except APIError as e:
            if "has active endpoints" in str(e).lower():
                console.print(f"[red]✗ Rede '{name}' em uso. Use force=True para desconectar[/red]")
            else:
                console.print(f"[red]✗ Erro ao remover rede '{name}': {e}[/red]")
            raise

    def inspect_network(self, name: str) -> Dict[str, Any]:
        """
        Inspeciona uma rede e retorna detalhes.

        Args:
            name: Nome da rede

        Returns:
            Dicionário com atributos da rede
        """
        network = self.get_network(name)

        if network is None:
            raise NotFound(f"Network '{name}' not found")

        network.reload()
        return network.attrs

    def display_networks_table(self, filters: Optional[Dict[str, Any]] = None):
        """
        Exibe tabela formatada com redes Docker.

        Args:
            filters: Filtros opcionais
        """
        networks = self.list_networks(filters)

        table = Table(title="Redes Docker", show_header=True, header_style="bold magenta")
        table.add_column("Nome", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Driver", style="yellow")
        table.add_column("Subnet", style="green")
        table.add_column("Containers", style="blue")

        for network in networks:
            network.reload()

            # Extrair subnet (IPAM)
            subnet = "N/A"
            if network.attrs.get("IPAM", {}).get("Config"):
                config = network.attrs["IPAM"]["Config"]
                if config and len(config) > 0:
                    subnet = config[0].get("Subnet", "N/A")

            # Contar containers conectados
            container_count = len(network.attrs.get("Containers", {}))

            table.add_row(
                network.name,
                network.id[:12],
                network.attrs["Driver"],
                subnet,
                str(container_count)
            )

        console.print(table)

    # Métodos específicos para o projeto de pagamento

    def create_all_networks(self) -> bool:
        """
        Cria todas as redes necessárias para o projeto.

        Returns:
            True se todas as redes foram criadas com sucesso
        """
        console.print("🚀 Criando todas as redes customizadas...", style="bold blue")

        networks = [
            "payment-api-main",
            "payment-api-cache",
            "payment-api-monitoring"
        ]

        created = 0
        for network_name in networks:
            try:
                network = self.upsert_network(network_name)
                if network:
                    created += 1
            except Exception as e:
                console.print(f"❌ Erro ao criar rede {network_name}: {e}", style="red")
                return False

        console.print(f"✅ {created}/{len(networks)} redes criadas", style="green")
        return created == len(networks)

    def show_network_status(self) -> None:
        """
        Exibe status das redes do projeto.
        """
        console.print("🌐 Status das Redes do Projeto", style="bold cyan")
        console.print("=" * 50, style="cyan")

        project_networks = ["payment-api-main", "payment-api-cache", "payment-api-monitoring"]

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rede", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("ID", style="dim")
        table.add_column("Containers", style="blue")

        for network_name in project_networks:
            network = self.get_network(network_name)
            if network:
                network.reload()
                container_count = len(network.attrs.get("Containers", {}))
                table.add_row(
                    network_name,
                    "✅ Ativa",
                    network.id[:12],
                    str(container_count)
                )
            else:
                table.add_row(network_name, "❌ Inativa", "-", "0")

        console.print(table)

    def update_compose_files(self) -> bool:
        """
        Atualiza arquivos docker-compose para usar as redes customizadas.

        Returns:
            True se conseguiu atualizar
        """
        console.print("📝 Atualizando arquivos docker-compose...", style="yellow")

        # Por enquanto, apenas retorna True (placeholder)
        # TODO: Implementar atualização dos arquivos docker-compose
        console.print("ℹ️  Atualização de compose files não implementada ainda", style="yellow")
        return True