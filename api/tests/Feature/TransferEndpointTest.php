<?php

namespace Tests\Feature;

use App\Jobs\SendNotification;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Bus;
use Tests\TestCase;

class TransferEndpointTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
    }

    public function test_transfer_successful(): void
    {
        Bus::fake();

        $payer = User::factory()->create(['type' => 'common', 'balance' => 100.00]);
        $payee = User::factory()->create(['type' => 'merchant', 'balance' => 0.00]);

        $data = [
            'value' => 50.00,
            'payer' => $payer->id,
            'payee' => $payee->id,
            'correlation_id' => 'unique-id-123',
        ];

        $response = $this->postJson('/api/transfer', $data);

        $response->assertStatus(200)
            ->assertJson(['message' => 'Transfer successful']);

        Bus::assertDispatched(SendNotification::class);
    }

    public function test_transfer_fails_with_insufficient_balance(): void
    {
        $payer = User::factory()->create(['type' => 'common', 'balance' => 10.00]);
        $payee = User::factory()->create(['type' => 'merchant', 'balance' => 0.00]);

        $data = [
            'value' => 50.00,
            'payer' => $payer->id,
            'payee' => $payee->id,
            'correlation_id' => 'unique-id-456',
        ];

        $response = $this->postJson('/api/transfer', $data);

        $response->assertStatus(422)
            ->assertJson(['message' => 'Insufficient balance']);
    }
}
