<?php

namespace Tests\Feature;

use App\Models\Transaction;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class TransactionModelTest extends TestCase
{
    use RefreshDatabase;

    protected $connection = 'testing';

    public function test_transaction_creation(): void
    {
        $transaction = Transaction::factory()->create();

        $this->assertDatabaseHas('transactions', [
            'id' => $transaction->id,
            'correlation_id' => $transaction->correlation_id,
        ]);
    }

    public function test_transaction_relationships(): void
    {
        $transaction = Transaction::factory()->create();

        $this->assertInstanceOf(User::class, $transaction->payer);
        $this->assertInstanceOf(User::class, $transaction->payee);
    }

    public function test_transaction_unique_correlation_id(): void
    {
        $this->expectException(\Illuminate\Database\QueryException::class);

        Transaction::factory()->create(['correlation_id' => 'unique-id']);
        Transaction::factory()->create(['correlation_id' => 'unique-id']);
    }
}
