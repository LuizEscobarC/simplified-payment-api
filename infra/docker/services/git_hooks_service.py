# infra/docker/services/git_hooks_service.py
"""
Git Hooks Service.

Configura Git hooks para qualidade de código: PHPStan, Laravel Pint, PHPMD, PHP-CS-Fixer.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
from urllib.request import urlretrieve
import stat

from rich.console import Console

from .base_service import BaseDockerService

console = Console()


class GitHooksService(BaseDockerService):
    """Serviço para configurar Git hooks de qualidade de código."""

    def __init__(self):
        """Inicializa serviço de Git hooks."""
        self.project_root = Path(__file__).parent.parent.parent.parent  # /home/luizescobal/study/simplified-payment-api
        self.hooks_dir = self.project_root / ".husky"
        self.tools_dir = self.project_root / "infra" / "tools"
        self.tools_dir.mkdir(exist_ok=True)

    def start(self, wait: bool = True) -> bool:
        """Instala ferramentas e configura hooks."""
        console.print("🔧 Configurando Git hooks para qualidade de código...")

        try:
            # Instalar ferramentas
            self._install_tools()

            # Configurar Husky
            self._setup_husky()

            # Criar hooks
            self._create_pre_commit_hook()
            self._create_pre_push_hook()

            console.print("✅ Git hooks configurados com sucesso!")
            return True

        except Exception as e:
            console.print(f"❌ Falha ao configurar Git hooks: {e}")
            return False

    def stop(self) -> bool:
        """Remove hooks (não remove ferramentas)."""
        console.print("🧹 Removendo Git hooks...")

        try:
            if self.hooks_dir.exists():
                shutil.rmtree(self.hooks_dir)
            console.print("✅ Git hooks removidos!")
            return True
        except Exception as e:
            console.print(f"❌ Falha ao remover hooks: {e}")
            return False

    def verify(self, max_attempts: int = 1) -> bool:
        """Verifica se hooks estão configurados."""
        console.print("🔍 Verificando configuração dos Git hooks...")

        checks = [
            self._check_tool("php-cs-fixer"),
            self._check_tool("phpmd"),
            self._check_tool("phpstan"),
            self._check_husky_setup(),
            self._check_pre_commit_hook(),
        ]

        if all(checks):
            console.print("✅ Todos os Git hooks estão configurados!")
            return True
        else:
            console.print("❌ Alguns Git hooks não estão configurados.")
            return False

    def logs(self, follow: bool = False) -> None:
        """Mostra status das ferramentas."""
        console.print("📋 Status das ferramentas de qualidade:")

        tools = ["php-cs-fixer", "phpmd", "phpstan"]
        for tool in tools:
            if self._check_tool(tool):
                console.print(f"✅ {tool}: instalado")
            else:
                console.print(f"❌ {tool}: não encontrado")

        if self.hooks_dir.exists():
            console.print("✅ Husky: configurado")
        else:
            console.print("❌ Husky: não configurado")

    def cleanup(self) -> None:
        """Remove ferramentas instaladas."""
        console.print("🧹 Removendo ferramentas de qualidade...")

        try:
            if self.tools_dir.exists():
                shutil.rmtree(self.tools_dir)
            console.print("✅ Ferramentas removidas!")
        except Exception as e:
            console.print(f"❌ Falha ao remover ferramentas: {e}")

    def _install_tools(self) -> None:
        """Instala ferramentas necessárias."""
        console.print("📦 Instalando ferramentas de qualidade...")

        # PHP-CS-Fixer
        self._download_phar(
            "https://cs.symfony.com/download/php-cs-fixer-v3.phar",
            "php-cs-fixer"
        )

        # PHPMD
        self._download_phar(
            "https://phpmd.org/static/latest/phpmd.phar",
            "phpmd"
        )

        # PHPStan
        self._download_phar(
            "https://github.com/phpstan/phpstan/releases/download/1.10.50/phpstan.phar",
            "phpstan"
        )

    def _download_phar(self, url: str, name: str) -> None:
        """Download e instalação de PHAR."""
        phar_path = self.tools_dir / name

        if phar_path.exists():
            console.print(f"✅ {name}: já instalado")
            return

        console.print(f"⬇️ Baixando {name}...")
        try:
            urlretrieve(url, phar_path)
            # Tornar executável
            phar_path.chmod(phar_path.stat().st_mode | stat.S_IEXEC)
            console.print(f"✅ {name}: instalado em {phar_path}")
        except Exception as e:
            console.print(f"❌ Falha ao baixar {name}: {e}")

    def _setup_husky(self) -> None:
        """Configura Husky para Git hooks."""
        console.print("🔧 Configurando Husky...")

        # Instalar Husky se não estiver
        package_json = self.project_root / "api" / "package.json"
        if package_json.exists():
            try:
                subprocess.run(
                    ["npm", "install", "--save-dev", "husky"],
                    cwd=self.project_root / "api",
                    check=True
                )
                console.print("✅ Husky: instalado via npm")
            except subprocess.CalledProcessError:
                console.print("⚠️ Husky: não conseguiu instalar via npm")

        # Criar diretório .husky
        self.hooks_dir.mkdir(exist_ok=True)

        # Criar .huskyrc se não existir
        huskyrc = self.project_root / ".huskyrc"
        if not huskyrc.exists():
            huskyrc_content = '{"hooks": {}}'
            huskyrc.write_text(huskyrc_content)
            console.print("✅ Husky: configurado")

    def _create_pre_commit_hook(self) -> None:
        """Cria hook pre-commit."""
        hook_path = self.hooks_dir / "pre-commit"

        hook_content = """#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "🔍 Executando verificações de qualidade de código..."

# Laravel Pint
echo "🎨 Executando Laravel Pint..."
cd api
./vendor/bin/pint --test || {
    echo "❌ Laravel Pint encontrou problemas. Corrigindo..."
    ./vendor/bin/pint
    git add .
}

# PHP-CS-Fixer
echo "🔧 Executando PHP-CS-Fixer..."
cd ..
infra/tools/php-cs-fixer fix api/ --dry-run --diff || {
    echo "❌ PHP-CS-Fixer encontrou problemas. Corrigindo..."
    infra/tools/php-cs-fixer fix api/
    git add .
}

# PHPMD
echo "📊 Executando PHPMD..."
infra/tools/phpmd api/app text cleancode,codesize,controversial,design,naming,unusedcode || {
    echo "⚠️ PHPMD encontrou problemas. Revise o código."
    exit 1
}

echo "✅ Verificações de qualidade concluídas!"
"""

        hook_path.write_text(hook_content)
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
        console.print("✅ Pre-commit hook: criado")

    def _create_pre_push_hook(self) -> None:
        """Cria hook pre-push."""
        hook_path = self.hooks_dir / "pre-push"

        hook_content = """#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "🔬 Executando análise estática completa..."

# PHPStan
echo "🔍 Executando PHPStan..."
cd api
../infra/tools/phpstan analyse app/ || {
    echo "❌ PHPStan encontrou erros. Corrija antes de fazer push."
    exit 1
}

echo "✅ Análise estática concluída!"
"""

        hook_path.write_text(hook_content)
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
        console.print("✅ Pre-push hook: criado")

    def _check_tool(self, tool_name: str) -> bool:
        """Verifica se ferramenta está instalada."""
        tool_path = self.tools_dir / tool_name
        return tool_path.exists() and tool_path.is_file()

    def _check_husky_setup(self) -> bool:
        """Verifica se Husky está configurado."""
        return self.hooks_dir.exists()

    def _check_pre_commit_hook(self) -> bool:
        """Verifica se pre-commit hook existe."""
        hook_path = self.hooks_dir / "pre-commit"
        return hook_path.exists() and hook_path.is_file()


# Exemplo de uso direto
if __name__ == "__main__":
    hooks = GitHooksService()

    # Configurar hooks
    if hooks.start():
        console.print("🎉 Git hooks configurados!")
    else:
        console.print("❌ Falha na configuração dos Git hooks")