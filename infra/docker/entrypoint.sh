#!/bin/bash

huskyInit() {
    if [ ! -d .husky ]; then
        npx husky init
    fi

    if [ -f .husky/pre-commit ] || ! grep -q "STAGED_FILES" .husky/pre-commit; then
        cat > .husky/pre-commit <<EOF
# Formatar cada arquivo alterado usando o Laravel Pint
STAGED_FILES=\$(git diff --cached --name-only --diff-filter=ACM | grep ".php\{0,1\}\$") || true

if [ -n "\$STAGED_FILES" ]; then
    for FILE in \$STAGED_FILES
    do
        docker exec backend-api ./vendor/bin/pint "\$FILE" > /dev/null >&1;
        git add "\$FILE";
    done;
fi
EOF
        chmod +x .husky/pre-commit
    fi
}

composerInit() {
    if [ ! -d vendor ] || [ composer.json -nt vendor/composer/autoload_classmap.php ]; then
        composer install --optimize-autoloader --ignore-platform-req=ext-rdkafka
    fi
}

packageNpmInit() {
    if [ ! -d node_modules ]; then
        npm install
    fi
}

laravelInit() {
    php artisan view:cache
    php artisan route:cache
    php artisan config:cache
    php artisan optimize
    php artisan key:generate
}

gitInit() {
    git config --global --add safe.directory /var/www
}

###########################################################
# faz o husky funcionar corretamente                      #
# instala as dependências do composer caso não existam_   #
# ou caso exista alterações no composer.json              #
# faz o cache das views, rotas e configurações do Laravel #
###########################################################
gitInit
composerInit
# huskyInit
laravelInit

php-fpm -F