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
        Schema::create('transactions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('payer_id')->constrained('users');
            $table->foreignId('payee_id')->constrained('users');
            $table->decimal('value', 15, 2);
            $table->enum('status', ['pending', 'approved', 'rejected', 'failed'])->default('pending');
            $table->string('correlation_id', 36)->unique();
            $table->timestamps();

            $table->index(['status', 'created_at']);
            $table->index('correlation_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('transactions');
    }
};
