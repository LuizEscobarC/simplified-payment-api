#!/usr/bin/env python3
"""
Entrypoint do container Laravel.

Executado do host, acessa o container Laravel remotamente via docker exec.
"""

import subprocess
import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class LaravelEntrypoint:
    """
    Gerencia inicialização do container Laravel via docker exec.

    Responsabilidades:
    - Instalar dependências (Composer, NPM)
    - Gerar chave Laravel
    - Rodar migrations
    - Limpar/cachear rotas, views, config
    - Ajustar permissões
    """

    def __init__(self, container_name: str, base_path: Optional[Path] = None):
        """
        Inicializa entrypoint.

        Args:
            container_name: Nome do container Docker
            base_path: Diretório base do Laravel (padrão: /var/www/html)
        """
        self.container_name = container_name
        self.base_path = base_path or "/var/www/html"

        console.print(f"🎯 Laravel Entrypoint Inicializado para container: {container_name}", style="blue")

    def docker_exec(self, cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Executa comando dentro do container via docker exec.

        Args:
            cmd: Comando a executar
            cwd: Diretório de trabalho dentro do container

        Returns:
            Resultado do subprocess.run
        """
        docker_cmd = ["docker", "exec"]

        if cwd:
            docker_cmd.extend(["-w", cwd])

        docker_cmd.append(self.container_name)
        docker_cmd.extend(cmd)

        return subprocess.run(
            docker_cmd,
            check=True,
            text=True,
            capture_output=True
        )

    def ensure_environment(self) -> None:
        """
        Garante que estamos no ambiente correto do container.
        """
        console.print("🐳 Verificando ambiente do container...", style="blue")

        try:
            self.docker_exec(["test", "-d", self.base_path])
            console.print("✅ Ambiente do container verificado", style="green")
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Diretório base {self.base_path} não existe no container")

    def composer_install(self) -> None:
        """
        Instala dependências Composer.
        """
        console.print("📦 Instalando Composer dependências...", style="blue")

        try:
            # Verificar se é ambiente de desenvolvimento
            app_env = self._get_app_env()
            is_dev = app_env in ['local', 'development', 'testing']
            
            cmd = ["composer", "install", "--optimize-autoloader", "--no-scripts"]
            
            if not is_dev:
                cmd.append("--no-dev")
            
            console.print(f"📋 Ambiente: {app_env}, instalando deps dev: {is_dev}", style="dim")
            
            self.docker_exec(cmd, cwd=self.base_path)
            console.print("✅ Composer install concluído", style="green")
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Erro no composer install: {e}", style="red")
            raise

    def _get_app_env(self) -> str:
        """
        Obtém o APP_ENV do container.
        """
        try:
            result = self.docker_exec([
                "sh", "-c", "grep '^APP_ENV=' /var/www/html/.env | cut -d'=' -f2"
            ], cwd=self.base_path)
            return result.stdout.strip() if result.stdout else "production"
        except:
            return "production"

    def npm_install(self) -> None:
        """
        Instala dependências NPM.
        """
        console.print("📦 Instalando NPM dependências...", style="blue")

        try:
            # Verificar se npm está disponível
            self.docker_exec(["which", "npm"], cwd=self.base_path)
        except subprocess.CalledProcessError:
            console.print("⚠️  NPM não encontrado, pulando instalação de dependências JS", style="yellow")
            return

        try:
            self.docker_exec(
                ["npm", "install", "--production"],
                cwd=self.base_path
            )
            console.print("✅ NPM install concluído", style="green")
        except subprocess.CalledProcessError as e:
            console.print(f"⚠️  NPM install falhou, mas continuando: {e}", style="yellow")

    def artisan(self, command: str, args: Optional[List[str]] = None) -> None:
        """
        Executa comando artisan.

        Args:
            command: Comando artisan
            args: Argumentos adicionais
        """
        cmd = ["php", "artisan", command]

        if args:
            cmd.extend(args)

        try:
            self.docker_exec(cmd, cwd=self.base_path)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Erro no artisan {command}: {e}", style="red")
            raise

    def generate_app_key(self) -> None:
        """
        Gera APP_KEY do Laravel se não existir.
        """
        console.print("🔑 Verificando APP_KEY...", style="blue")

        try:
            # Primeiro verifica se o arquivo .env existe
            env_file = f"{self.base_path}/.env"
            result = self.docker_exec([
                "test", "-f", env_file
            ], cwd=self.base_path)

            if result.returncode != 0:
                console.print(f"❌ Arquivo .env não encontrado: {env_file}", style="red")
                raise RuntimeError(f"Arquivo .env não existe: {env_file}")

            # Verifica se APP_KEY está vazia ou não definida
            result = self.docker_exec([
                "sh", "-c",
                f"grep '^APP_KEY=' {env_file} | cut -d'=' -f2"
            ], cwd=self.base_path)

            app_key = result.stdout.strip()

            if not app_key or app_key == "":
                console.print("🔑 APP_KEY vazia, gerando nova chave...", style="blue")
                self.artisan("key:generate")
                console.print("✅ APP_KEY gerada", style="green")
            else:
                console.print("✓ APP_KEY já existe", style="yellow")

        except subprocess.CalledProcessError as e:
            console.print(f"❌ Erro ao verificar APP_KEY: {e}", style="red")
            console.print("🔑 Tentando gerar APP_KEY...", style="blue")
            try:
                self.artisan("key:generate")
                console.print("✅ APP_KEY gerada após erro", style="green")
            except Exception as e2:
                console.print(f"❌ Falha crítica ao gerar APP_KEY: {e2}", style="red")
                raise
            except subprocess.CalledProcessError as e2:
                console.print(f"❌ Falha ao gerar APP_KEY: {e2}", style="red")
                raise

    def copy_env_for_testing(self) -> None:
        """
        Copia .env para .env.testing para garantir que testes funcionem.
        """
        console.print("📋 Copiando .env para .env.testing...", style="blue")

        try:
            self.docker_exec([
                "cp", "/var/www/html/.env", "/var/www/html/.env.testing"
            ])
            console.print("✅ .env.testing criado", style="green")
        except subprocess.CalledProcessError as e:
            console.print(f"⚠️  Falha ao copiar para .env.testing: {e}", style="yellow")

    def run_migrations(self) -> None:
        """
        Executa migrations do Laravel.
        """
        console.print("🗄️  Executando migrations...", style="blue")
        try:
            self.artisan("migrate", ["--force"])
            console.print("✅ Migrations executadas", style="green")
        except subprocess.CalledProcessError:
            console.print("⚠️  Migrations falharam, tentando reset e re-run...", style="yellow")
            try:
                # Tenta reset e migrate fresh
                self.artisan("migrate:reset", ["--force"])
                self.artisan("migrate", ["--force"])
                console.print("✅ Migrations executadas após reset", style="green")
            except subprocess.CalledProcessError:
                console.print("⚠️  Migrations ainda falharam, continuando...", style="yellow")

    def clear_caches(self) -> None:
        """
        Limpa caches do Laravel.
        """
        console.print("🧹 Limpando caches...", style="blue")

        caches = ["config", "cache", "route", "view"]

        for cache_type in caches:
            try:
                cmd = ["php", "artisan", f"{cache_type}:clear"]
                self.docker_exec(cmd, cwd=self.base_path)
                console.print(f"✓ {cache_type} limpo", style="green")
            except subprocess.CalledProcessError:
                console.print(f"⚠️  Erro ao limpar {cache_type}", style="yellow")

    def cache_optimizations(self) -> None:
        """
        Cacheia configurações para performance.
        """
        console.print("⚡ Cacheando otimizações...", style="blue")

        optimizations = ["config", "route", "view"]

        for opt_type in optimizations:
            try:
                self.artisan(f"{opt_type}:cache")
                console.print(f"✓ {opt_type} cacheado", style="green")
            except subprocess.CalledProcessError:
                console.print(f"⚠️  Erro ao cachear {opt_type}", style="yellow")

    def fix_permissions(self) -> None:
        """
        Ajusta permissões de storage e bootstrap/cache.
        """
        console.print("🔒 Ajustando permissões...", style="blue")

        dirs_to_fix = [
            f"{self.base_path}/storage",
            f"{self.base_path}/bootstrap/cache"
        ]

        for directory in dirs_to_fix:
            try:
                self.docker_exec(["chmod", "-R", "775", directory])
                self.docker_exec(["chown", "-R", "appuser:appuser", directory])
                console.print(f"✓ {directory.split('/')[-1]} OK", style="green")
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Erro ao ajustar {directory}: {e}", style="red")

    def start_php_fpm(self) -> None:
        """
        PHP-FPM já deve estar rodando no container.
        Este método não faz nada quando executado externamente.
        """
        console.print("ℹ️  PHP-FPM deve estar rodando no container (não iniciado aqui)", style="blue")

    def run(self) -> None:
        """
        Executa entrypoint completo.
        """
        console.print("\n" + "="*60, style="bold blue")
        console.print("🎯 LARAVEL ENTRYPOINT", style="bold blue")
        console.print("="*60 + "\n", style="bold blue")

        try:
            # 1. Verificar ambiente
            self.ensure_environment()

            # 1.5. Garantir que .env existe antes de qualquer coisa
            console.print("📄 Verificando se .env existe...", style="blue")
            env_file = f"{self.base_path}/.env"
            result = self.docker_exec(["test", "-f", env_file], cwd=self.base_path)
            if result.returncode != 0:
                console.print(f"❌ Arquivo .env não encontrado em {env_file}", style="red")
                console.print("📄 Criando .env básico...", style="blue")
                # Criar .env básico se não existir
                self.docker_exec([
                    "sh", "-c",
                    f"echo 'APP_NAME=Laravel' > {env_file} && echo 'APP_ENV=local' >> {env_file} && echo 'APP_KEY=' >> {env_file}"
                ], cwd=self.base_path)
                console.print("✅ .env básico criado", style="green")
            else:
                console.print("✅ .env encontrado", style="green")

            # 2. Dependências
            try:
                self.composer_install()
            except Exception as e:
                console.print(f"⚠️  Composer falhou: {e}", style="yellow")

            try:
                self.npm_install()
            except Exception as e:
                console.print(f"⚠️  NPM falhou: {e}", style="yellow")

            # 3. Chave Laravel
            try:
                self.generate_app_key()
                # Copiar .env para .env.testing para testes
                self.copy_env_for_testing()
            except Exception as e:
                console.print(f"⚠️  APP_KEY falhou: {e}", style="yellow")

            # 4. Limpar caches
            try:
                self.clear_caches()
            except Exception as e:
                console.print(f"⚠️  Limpeza de caches falhou: {e}", style="yellow")

            # 5. Migrations
            try:
                self.run_migrations()
            except Exception as e:
                console.print(f"⚠️  Migrations falharam: {e}", style="yellow")

            # 6. Otimizações
            try:
                self.cache_optimizations()
            except Exception as e:
                console.print(f"⚠️  Otimizações falharam: {e}", style="yellow")

            # 7. Permissões
            try:
                self.fix_permissions()
            except Exception as e:
                console.print(f"⚠️  Ajuste de permissões falhou: {e}", style="yellow")

            # 8. Sucesso
            console.print("\n" + "="*60, style="bold green")
            console.print("✅ ENTRYPOINT CONCLUÍDO", style="bold green")
            console.print("="*60 + "\n", style="bold green")

            # PHP-FPM já deve estar rodando no container

        except KeyboardInterrupt:
            console.print("\n⚠️  Entrypoint interrompido\n", style="yellow")
        except Exception as e:
            console.print(f"\n❌ Erro crítico no entrypoint: {e}\n", style="red bold")
            raise


# Ponto de entrada
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Laravel Entrypoint - executado do host")
    parser.add_argument(
        "--container",
        required=True,
        help="Nome do container Docker do Laravel"
    )

    args = parser.parse_args()

    entrypoint = LaravelEntrypoint(container_name=args.container)
    entrypoint.run()
