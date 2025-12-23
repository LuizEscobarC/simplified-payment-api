<?php

namespace Tests\Unit;

use App\Repositories\TransferRepositoryInterface;
use App\Services\TransferService;
use Tests\TestCase;

class TransferServiceTest extends TestCase
{
    public function test_execute_transfer_fails_with_insufficient_balance(): void
    {
        $repository = $this->createMock(TransferRepositoryInterface::class);
        $service = new TransferService($repository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Insufficient balance');

        $service->executeTransfer(['value' => 100.0, 'payer' => 1, 'payee' => 2, 'correlation_id' => 'correlation-123']);
    }
}
