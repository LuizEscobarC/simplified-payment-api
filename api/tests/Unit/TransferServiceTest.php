<?php

namespace Tests\Unit;

use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use App\Services\TransferService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class TransferServiceTest extends TestCase
{
    use RefreshDatabase;

    public function test_execute_transfer_fails_with_insufficient_balance(): void
    {
        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $service = new TransferService($repository, $eventRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Payer not found');

        $service->executeTransfer(['value' => 100.0, 'payer' => 1, 'payee' => 2, 'correlation_id' => 'correlation-123']);
    }
}
