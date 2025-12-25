<?php

namespace Tests\Feature;

use App\Jobs\SendNotification;
use App\Models\Event;
use App\Models\User;
use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Bus;
use Mockery;
use Tests\TestCase;

class TransferEndpointTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
    }


    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function test_transfer_successful(): void
    {
        Bus::fake();

        // Mock the repositories using Mockery
        $eventRepoMock = Mockery::mock(EventRepositoryInterface::class);
        $eventRepoMock->shouldReceive('save')->andReturn(new Event());
        $this->app->instance(EventRepositoryInterface::class, $eventRepoMock);

        $transferRepoMock = Mockery::mock(TransferRepositoryInterface::class);
        $transferRepoMock->shouldReceive('findByCorrelationId')->andReturn(null);
        $transferRepoMock->shouldReceive('save')->andReturn(new \App\Models\Transaction([
            'id' => 1,
            'payer_id' => 1,
            'payee_id' => 2,
            'value' => 50.00,
            'correlation_id' => 'unique-id-123',
            'status' => 'approved',
        ]));
        $this->app->instance(TransferRepositoryInterface::class, $transferRepoMock);

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
        // Mock the repositories using Mockery
        $eventRepoMock = Mockery::mock(EventRepositoryInterface::class);
        $eventRepoMock->shouldReceive('save')->andReturn(new Event());
        $this->app->instance(EventRepositoryInterface::class, $eventRepoMock);

        $transferRepoMock = Mockery::mock(TransferRepositoryInterface::class);
        $transferRepoMock->shouldReceive('findByCorrelationId')->andReturn(null);
        $this->app->instance(TransferRepositoryInterface::class, $transferRepoMock);

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
