<?php

namespace Tests\Unit;

use App\Models\Transaction;
use App\Repositories\Mysql\EloquentTransferRepository;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class TransferRepositoryTest extends TestCase
{
    use RefreshDatabase;

    public function test_find_by_id(): void
    {
        $transaction = Transaction::factory()->create();

        $repository = new EloquentTransferRepository;

        $found = $repository->findById($transaction->id);

        $this->assertInstanceOf(Transaction::class, $found);
        $this->assertEquals($transaction->id, $found->id);
    }

    public function test_find_by_id_not_found(): void
    {
        $repository = new EloquentTransferRepository;

        $found = $repository->findById(999);

        $this->assertNull($found);
    }

    public function test_save(): void
    {
        $payer = \App\Models\User::factory()->create();
        $payee = \App\Models\User::factory()->create();

        $transaction = new Transaction([
            'payer_id' => $payer->id,
            'payee_id' => $payee->id,
            'value' => 100.0,
            'status' => 'pending',
            'correlation_id' => 'test-123',
        ]);

        $repository = new EloquentTransferRepository;

        $saved = $repository->save($transaction);

        $this->assertInstanceOf(Transaction::class, $saved);
        $this->assertNotNull($saved->id);
        $this->assertEquals('test-123', $saved->correlation_id);
    }

    public function test_find_by_correlation_id(): void
    {
        $transaction = Transaction::factory()->create(['correlation_id' => 'unique-123']);

        $repository = new EloquentTransferRepository;

        $found = $repository->findByCorrelationId('unique-123');

        $this->assertInstanceOf(Transaction::class, $found);
        $this->assertEquals('unique-123', $found->correlation_id);
    }

    public function test_find_by_correlation_id_not_found(): void
    {
        $repository = new EloquentTransferRepository;

        $found = $repository->findByCorrelationId('nonexistent');

        $this->assertNull($found);
    }
}
