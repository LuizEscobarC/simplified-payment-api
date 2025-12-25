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
        Schema::create('users', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('email')->unique();
            $table->string('password');
            $table->string('cpf_cnpj', 14)->nullable()->unique();
            $table->bigInteger('balance')->default(0);
            $table->enum('type', ['common', 'merchant'])->default('common');
            $table->rememberToken();
            $table->timestamps();

            $table->index(['type', 'balance'], 'users_type_balance_index');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('users');
    }
};
