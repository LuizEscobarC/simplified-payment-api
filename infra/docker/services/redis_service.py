"""
Redis Global Service.

Gerencia o serviço Redis global do ecossistema ET.
Substitui a parte do setup.sh que gerencia o Redis.
"""

import subprocess
from pathlib import Path
from typing import Optional
import time

from rich.console import Console

console = Console()


class RedisService:
    """Gerencia serviço Redis global."""
    
    def __init__(
        self,
        compose_file: Optional[Path] = None,
        container_name: str = "et-redis"
    ):
        """
        Inicializa serviço Redis.
        
        Args:
            compose_file: Caminho para docker-compose-global-redis.yml
            container_name: Nome do container Redis
        """
        self.container_name = container_name
        
        # Define caminho do compose file
        if compose_file is None:
            self.compose_file = Path("infra/docker/docker-compose-global-redis.yml")
        else:
            self.compose_file = Path(compose_file)
        
        if not self.compose_file.exists():
            raise FileNotFoundError(
                f"Compose file não encontrado: {self.compose_file}"
            )
    
    def cleanup_existing(self) -> None:
        """Remove container existente se houver conflito."""
        try:
            # Primeiro: tentar parar e remover via compose
            subprocess.run(
                [
                    "docker", "compose",
                    "-f", str(self.compose_file),
                    "down", "-v"
                ],
                capture_output=True
            )
            
            # Segundo: forçar remoção do container pelo nome
            subprocess.run(
                ["docker", "rm", "-f", self.container_name],
                capture_output=True
            )
            
            console.print(f"✓ Cleanup executado para {self.container_name}", style="yellow")
        except Exception as e:
            console.print(f"⚠️  Erro no cleanup: {e}", style="yellow")
    
    def start(self, wait: bool = True, cleanup_if_conflict: bool = True) -> bool:
        """
        Inicia serviço Redis.
        
        Args:
            wait: Aguardar serviço ficar pronto
            cleanup_if_conflict: Se True, remove container existente em caso de conflito
        
        Returns:
            True se iniciou com sucesso
        """
        console.print(f"🚀 Iniciando {self.container_name}...", style="blue")
        
        try:
            cmd = [
                "docker", "compose",
                "-f", str(self.compose_file),
                "up", "-d",
                "--build",
                "--remove-orphans"
            ]
            
            if wait:
                cmd.append("--wait")
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            console.print(f"✅ {self.container_name} iniciado", style="green")
            
            # Verificar se está rodando
            if wait:
                return self.verify()
            
            return True
            
        except subprocess.CalledProcessError as e:
            # Se erro de conflito de nome e cleanup_if_conflict=True, tentar limpar
            if "already in use" in e.stderr and cleanup_if_conflict:
                console.print(f"⚠️  Container já existe, fazendo cleanup...", style="yellow")
                self.cleanup_existing()
                
                # Tentar novamente
                try:
                    result = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    
                    console.print(f"✅ {self.container_name} iniciado após cleanup", style="green")
                    
                    if wait:
                        return self.verify()
                    
                    return True
                except subprocess.CalledProcessError as e2:
                    console.print(
                        f"❌ Erro ao iniciar após cleanup: {e2.stderr}",
                        style="red"
                    )
                    return False
            else:
                console.print(
                    f"❌ Erro ao iniciar {self.container_name}: {e.stderr}",
                    style="red"
                )
                return False
    
    def stop(self) -> bool:
        """
        Para serviço Redis.
        
        Returns:
            True se parou com sucesso
        """
        console.print(f"🛑 Parando {self.container_name}...", style="yellow")
        
        try:
            subprocess.run(
                [
                    "docker", "compose",
                    "-f", str(self.compose_file),
                    "down"
                ],
                check=True,
                capture_output=True
            )
            
            console.print(f"✅ {self.container_name} parado", style="green")
            return True
            
        except subprocess.CalledProcessError as e:
            console.print(
                f"❌ Erro ao parar {self.container_name}: {e}",
                style="red"
            )
            return False
    
    def verify(self, max_attempts: int = 30) -> bool:
        """
        Verifica se Redis está pronto.
        
        Args:
            max_attempts: Número máximo de tentativas
        
        Returns:
            True se Redis está respondendo
        """
        console.print(f"⏳ Verificando {self.container_name}...", style="cyan")
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Verificar se container está rodando
                result = subprocess.run(
                    [
                        "docker", "inspect",
                        "-f", "{{.State.Running}}",
                        self.container_name
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip() == "true":
                    # Container rodando, verificar healthcheck
                    health_result = subprocess.run(
                        [
                            "docker", "exec",
                            self.container_name,
                            "redis-cli", "ping"
                        ],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if "PONG" in health_result.stdout:
                        console.print(
                            f"✅ {self.container_name} está pronto!",
                            style="green"
                        )
                        return True
                
            except subprocess.CalledProcessError:
                pass
            
            # Aguardar antes de próxima tentativa
            console.print(".", end="", style="cyan")
            time.sleep(1)
        
        console.print(
            f"\n❌ {self.container_name} timeout após {max_attempts}s",
            style="red"
        )
        return False
    
    def logs(self, follow: bool = False, tail: int = 100) -> None:
        """
        Exibe logs do Redis.
        
        Args:
            follow: Seguir logs em tempo real
            tail: Número de linhas a exibir
        """
        cmd = [
            "docker", "compose",
            "-f", str(self.compose_file),
            "logs"
        ]
        
        if follow:
            cmd.append("-f")
        
        cmd.extend(["--tail", str(tail)])
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Erro ao exibir logs: {e}", style="red")
    
    def restart(self) -> bool:
        """
        Reinicia serviço Redis.
        
        Returns:
            True se reiniciou com sucesso
        """
        self.stop()
        time.sleep(2)
        return self.start()


# Exemplo de uso direto
if __name__ == "__main__":
    redis = RedisService()
    
    # Iniciar Redis
    if redis.start():
        print("Redis iniciado com sucesso!")
        
        # Verificar
        if redis.verify():
            print("Redis verificado!")
    else:
        print("Falha ao iniciar Redis")
