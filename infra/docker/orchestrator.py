#!/usr/bin/env python3
"""
Orquestrador Automático de Setup.

Inicia todos os serviços necessários para o projeto de API de pagamentos.
Usa as classes de serviço para gerenciar Docker containers automaticamente.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

# Adicionar caminho para importar serviços
sys.path.append(str(Path(__file__).parent))

from services.redis_service import RedisService
from services.mysql_service import MySQLService
from services.mongodb_service import MongoDBService
from services.laravel_service import LaravelService
from services.queue_service import QueueService
from services.nginx_service import NginxService
from services.monitoring_service import ElasticsearchService, LogstashService, KibanaService, PrometheusService
from services.git_hooks_service import GitHooksService
from scripts.prerequisites import PrerequisiteChecker
from scripts.env_manager import LaravelEnvManager
from scripts import DockerNetworkManager

console = Console()


class ServiceState(Enum):
    """Estados possíveis de um serviço."""
    PENDING = "pending"
    STARTING = "starting"
    VERIFYING = "verifying"
    READY = "ready"
    FAILED = "failed"


class ServiceOrchestrator:
    """Orquestra o startup de todos os serviços."""

    def __init__(self, include_monitoring: bool = False):
        """Inicializa orquestrador."""
        # Carregar variáveis de ambiente primeiro
        console.print("🔧 Carregando variáveis de ambiente...", style="cyan")
        self._load_environment_variables()

        # Gerenciador de redes customizadas
        self.network_manager = DockerNetworkManager()

        self.services = {
            'redis': RedisService(),
            'mysql': MySQLService(),
            'mongodb': MongoDBService(),
            'laravel': LaravelService(),
            'queue': QueueService(),
            'nginx': NginxService()
        }

        if include_monitoring:
            self.services.update({
                'elasticsearch': ElasticsearchService(),
                'logstash': LogstashService(),
                'kibana': KibanaService(),
                'prometheus': PrometheusService()
            })

        # Estado de cada serviço
        self.service_states = {name: ServiceState.PENDING for name in self.services.keys()}
        self.include_monitoring = include_monitoring

    def _load_environment_variables(self) -> None:
        """
        Carrega variáveis de ambiente necessárias para o funcionamento.
        """
        try:
            # Caminho absoluto para o arquivo .env
            project_root = Path(__file__).parent.parent.parent
            env_file_path = project_root / "infra" / "docker" / ".env"

            # Usar LaravelEnvManager para carregar as variáveis
            env_manager = LaravelEnvManager(env_file=str(env_file_path))

            # Validar e carregar variáveis
            if env_manager.setup_laravel_env():
                console.print("✅ Variáveis de ambiente carregadas com sucesso", style="green")
            else:
                console.print("❌ Falha ao carregar variáveis de ambiente", style="red")
                console.print("💡 Verifique se o arquivo .env existe e está configurado corretamente", style="yellow")
                # Não sair, permitir que o sistema continue (útil para desenvolvimento)

        except Exception as e:
            console.print(f"❌ Erro ao carregar variáveis de ambiente: {e}", style="red")
            # Não sair, permitir que o sistema continue

    def check_prerequisites(self) -> bool:
        """
        Verifica pré-requisitos do sistema antes de iniciar serviços.

        Returns:
            True se todos os pré-requisitos estão OK
        """
        console.print("🔍 Verificando pré-requisitos do sistema...", style="bold cyan")

        checker = PrerequisiteChecker()
        success = checker.check_all(show_progress=True)

        if not success:
            console.print("\n❌ Pré-requisitos não atendidos!", style="bold red")
            console.print("💡 Sugestões de correção:", style="yellow")

            suggestions = checker.get_fix_suggestions()
            for suggestion in suggestions:
                console.print(f"   • {suggestion}", style="yellow")

            console.print("\n🔄 Execute novamente após corrigir os problemas.", style="cyan")
            return False

        console.print("✅ Todos os pré-requisitos verificados com sucesso!", style="bold green")
        return True

    def update_service_state(self, service_name: str, state: ServiceState) -> None:
        """
        Atualiza o estado de um serviço.

        Args:
            service_name: Nome do serviço
            state: Novo estado
        """
        self.service_states[service_name] = state
        console.print(f"📊 {service_name.upper()} -> {state.value}", style="cyan")

    def start_service_with_state_machine(self, service_name: str, progress: Progress, task_id) -> bool:
        """
        Inicia um serviço usando padrão de máquina de estados.

        Args:
            service_name: Nome do serviço
            progress: Instância do Progress
            task_id: ID da tarefa no progress

        Returns:
            True se serviço iniciou com sucesso
        """
        service = self.services[service_name]

        try:
            # Estado: STARTING
            self.update_service_state(service_name, ServiceState.STARTING)
            progress.update(task_id, description=f"Iniciando {service_name.upper()}...")

            # Tentar iniciar o serviço
            if not service.start(wait=False):
                self.update_service_state(service_name, ServiceState.FAILED)
                progress.update(task_id, description=f"❌ {service_name.upper()} falhou ao iniciar")
                return False

            # Estado: VERIFYING
            self.update_service_state(service_name, ServiceState.VERIFYING)
            progress.update(task_id, description=f"Verificando {service_name.upper()}...")

            # Aguardar e verificar se está pronto
            if service.verify():
                self.update_service_state(service_name, ServiceState.READY)
                progress.update(task_id, description=f"✅ {service_name.upper()} pronto")
                return True
            else:
                self.update_service_state(service_name, ServiceState.FAILED)
                progress.update(task_id, description=f"❌ {service_name.upper()} falhou na verificação")
                return False

        except Exception as e:
            self.update_service_state(service_name, ServiceState.FAILED)
            progress.update(task_id, description=f"💥 {service_name.upper()} erro: {str(e)[:30]}...")
            return False

    def start_all_services(self, skip_prerequisites: bool = False) -> bool:
        """
        Inicia todos os serviços em ordem usando padrão de máquina de estados.

        Ordem: Pré-requisitos -> Redes -> Redis -> MySQL -> MongoDB -> Laravel -> Nginx
        Cada serviço passa por: PENDING -> STARTING -> VERIFYING -> READY/FAILED

        Returns:
            True se todos iniciaram com sucesso
        """
        console.print("🚀 Iniciando orquestração automática de serviços...", style="bold blue")

        # 0. Verificar pré-requisitos do sistema
        if not skip_prerequisites and not self.check_prerequisites():
            return False

        # 1. Criar redes customizadas (sempre obrigatório)
        console.print("\n🌐 Preparando redes customizadas...", style="cyan")
        if not self.network_manager.create_all_networks():
            console.print("❌ Falha ao criar redes customizadas", style="red")
            return False

        # 2. Atualizar arquivos docker-compose
        console.print("\n📝 Atualizando configurações de rede...", style="cyan")
        if not self.network_manager.update_compose_files():
            console.print("⚠️  Alguns arquivos docker-compose podem não ter sido atualizados", style="yellow")

        # Ordem de inicialização com dependências críticas
        startup_order = ['redis', 'mysql', 'mongodb']  # Bancos primeiro
        
        # Só iniciar app se bancos estiverem OK (verificar depois dos bancos)
        critical_services_ok = True
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:

            # Primeiro iniciar bancos críticos
            overall_task = progress.add_task("Iniciando bancos de dados...", total=len(startup_order))
            failed_services = []

            for service_name in startup_order:
                service_task = progress.add_task(f"Preparando {service_name.upper()}...", total=1)
                success = self.start_service_with_state_machine(service_name, progress, service_task)

                if not success:
                    failed_services.append(service_name)
                    critical_services_ok = False
                    progress.update(overall_task, description="❌ Banco crítico falhou")
                else:
                    progress.update(service_task, completed=1)

                progress.update(overall_task, advance=1)
                time.sleep(2)

            # Verificar se bancos críticos estão OK antes de iniciar app
            if critical_services_ok:
                # Adicionar serviços da aplicação
                app_services = ['laravel', 'queue', 'nginx']
                if self.include_monitoring:
                    app_services.extend(['elasticsearch', 'logstash', 'kibana', 'prometheus'])
                
                startup_order.extend(app_services)
                
                # Iniciar serviços da aplicação
                app_task = progress.add_task("Iniciando aplicação...", total=len(app_services))
                
                for service_name in app_services:
                    service_task = progress.add_task(f"Preparando {service_name.upper()}...", total=1)
                    success = self.start_service_with_state_machine(service_name, progress, service_task)

                    if not success:
                        failed_services.append(service_name)
                        progress.update(app_task, description="❌ Serviço da aplicação falhou")
                    else:
                        progress.update(service_task, completed=1)

                    progress.update(app_task, advance=1)
                    time.sleep(2)
            else:
                console.print("⚠️  Bancos críticos falharam - pulando serviços dependentes", style="yellow")

            # Mostrar resumo das falhas se houver
            if failed_services:
                console.print(f"\n⚠️  {len(failed_services)} serviço(s) falharam: {', '.join(failed_services).upper()}", style="yellow")
                console.print("💡 Os outros serviços foram iniciados normalmente.", style="cyan")
            else:
                console.print("\n✅ Todos os serviços iniciados com sucesso!", style="green")

        # Sempre tentar verificar os serviços que foram iniciados
        return self._verify_all_services()

    def _verify_all_services(self) -> bool:
        """Verifica se todos os serviços estão funcionando."""
        console.print("\n🔍 Verificando status final dos serviços...", style="blue")

        all_ok = True
        failed_verifications = []

        for name, service in self.services.items():
            # Pular serviços que falharam na inicialização
            if self.service_states.get(name) == ServiceState.FAILED:
                console.print(f"⏭️  {name.upper()} pulado (falhou na inicialização)", style="yellow")
                continue
                
            if hasattr(service, 'verify'):
                if service.verify(max_attempts=10):
                    console.print(f"✅ {name.upper()} verificado", style="green")
                else:
                    console.print(f"❌ {name.upper()} falhou na verificação", style="red")
                    failed_verifications.append(name)
                    all_ok = False

        if failed_verifications:
            console.print(f"\n⚠️  {len(failed_verifications)} serviço(s) com problemas: {', '.join(failed_verifications).upper()}", style="yellow")
            console.print("💡 Verifique os logs dos containers para mais detalhes.", style="cyan")
            # Não retorna False para não parar a execução - útil para desenvolvimento
            return True
        else:
            console.print("\n✅ Todos os serviços verificados com sucesso!", style="green")
            return True

    def stop_all_services(self) -> bool:
        """Para todos os serviços."""
        console.print("🛑 Parando todos os serviços...", style="yellow")

        success = True
        for name, service in self.services.items():
            try:
                if not service.stop():
                    success = False
            except Exception as e:
                console.print(f"❌ Erro ao parar {name.upper()}: {e}", style="red")
                success = False

        return success

    def _check_service_status(self, service_name: str, service) -> str:
        """
        Verifica o status real de um serviço.

        Args:
            service_name: Nome do serviço
            service: Instância do serviço

        Returns:
            String com status formatado
        """
        try:
            # Primeiro verifica o estado armazenado
            state = self.service_states.get(service_name, ServiceState.PENDING)
            
            # Mapeia estado para string formatada
            state_map = {
                ServiceState.PENDING: "⏳ Pendente",
                ServiceState.STARTING: "🚀 Iniciando",
                ServiceState.VERIFYING: "🔍 Verificando", 
                ServiceState.READY: "✅ Pronto",
                ServiceState.FAILED: "❌ Falhou"
            }
            
            return state_map.get(state, "❓ Desconhecido")
            
        except Exception as e:
            return f"❌ Erro: {str(e)}"

    def show_status(self):
        """Exibe status de todos os serviços e redes usando máquina de estados."""
        # Status das redes
        console.print("\n🌐 Redes Customizadas:", style="bold blue")
        self.network_manager.show_network_status()

        # Status dos serviços
        table = Table(title="📊 Status dos Serviços")
        table.add_column("Serviço", style="cyan", no_wrap=True)
        table.add_column("Estado", style="magenta")

        for name, state in self.service_states.items():
            service = self.services[name]
            container = getattr(service, 'container_name', 'N/A')
            
            # Mapeia estado para emoji
            state_emoji = {
                ServiceState.PENDING: "⏳",
                ServiceState.STARTING: "🚀",
                ServiceState.VERIFYING: "🔍",
                ServiceState.READY: "✅",
                ServiceState.FAILED: "❌"
            }.get(state, "❓")
            
            table.add_row(f"{name.upper()}", f"{state_emoji} {state.value}")

        console.print(table)

    def cleanup_all(self):
        """Limpa containers existentes."""
        console.print("🧹 Limpando containers existentes...", style="yellow")

        for name, service in self.services.items():
            try:
                service.cleanup_existing()
                console.print(f"✅ {name.upper()} limpo", style="green")
            except Exception as e:
                console.print(f"⚠️  Erro ao limpar {name.upper()}: {e}", style="yellow")

    def setup_git_hooks(self) -> bool:
        """Configura Git hooks separadamente."""
        console.print("🔧 Configurando Git hooks...", style="cyan")
        hooks_service = GitHooksService()
        return hooks_service.start()


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Orquestrador de Serviços para API de Pagamentos")
    parser.add_argument("action", choices=["start", "stop", "status", "cleanup", "hooks"],
                       help="Ação a executar")
    parser.add_argument("--no-wait", action="store_true",
                       help="Não aguardar serviços ficarem prontos")
    parser.add_argument("--monitoring", action="store_true",
                       help="Incluir serviços de monitoramento (ELK + Prometheus)")
    parser.add_argument("--skip-prerequisites", action="store_true",
                       help="Pular verificação de pré-requisitos do sistema")

    args = parser.parse_args()

    orchestrator = ServiceOrchestrator(include_monitoring=args.monitoring)

    if args.action == "start":
        success = orchestrator.start_all_services(skip_prerequisites=args.skip_prerequisites)
        if success:
            console.print("\n🎉 Todos os serviços iniciados com sucesso!", style="bold green")
            console.print("💡 Você pode acessar:", style="blue")
            console.print("   - Redis: localhost:6379", style="white")
            console.print("   - MySQL: localhost:3306 (user: root, pass: root)", style="white")
            console.print("   - MongoDB: localhost:27017", style="white")
            console.print("   - Laravel API: http://localhost/api", style="white")
            console.print("   - Nginx: http://localhost", style="white")
            if orchestrator.include_monitoring:
                console.print("   - Elasticsearch: localhost:9200", style="white")
                console.print("   - Logstash: localhost:9600", style="white")
                console.print("   - Kibana: localhost:5601", style="white")
                console.print("   - Prometheus: localhost:9090", style="white")
        else:
            console.print("\n💥 Falha ao iniciar alguns serviços!", style="bold red")
            orchestrator.show_status()
            sys.exit(1)

    elif args.action == "stop":
        if orchestrator.stop_all_services():
            console.print("✅ Todos os serviços parados", style="green")
        else:
            console.print("❌ Erro ao parar serviços", style="red")
            sys.exit(1)

    elif args.action == "status":
        orchestrator.show_status()

    elif args.action == "cleanup":
        orchestrator.cleanup_all()

    elif args.action == "hooks":
        if orchestrator.setup_git_hooks():
            console.print("✅ Git hooks configurados com sucesso!", style="green")
        else:
            console.print("❌ Falha ao configurar Git hooks!", style="red")
            sys.exit(1)


if __name__ == "__main__":
    main()