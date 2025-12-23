<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->string('cpf_cnpj', 14)->nullable()->unique();
            $table->string('email')->nullable()->change();
            $table->decimal('balance', 15, 2)->default(0);
            $table->enum('type', ['common', 'merchant'])->default('common');
            $table->index(['type', 'balance'], 'users_type_balance_index');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropIndex('users_type_balance_index');
            $table->dropColumn(['cpf_cnpj', 'balance', 'type']);
        });
    }
};
