<?php

namespace Tests\Unit;

use App\Enums\TransactionStatus;
use App\Enums\UserType;
use App\Jobs\SendNotification;
use App\Models\Event;
use App\Models\Transaction;
use App\Models\User;
use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use App\Repositories\Interfaces\UserRepositoryInterface;
use App\Services\TransferService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class TransferServiceTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Queue::fake();
    }

    public function test_execute_transfer_successful(): void
    {
        // Create users
        $payer = User::factory()->create(['type' => UserType::COMMON, 'balance' => 100.0]);
        $payee = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 50.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->exactly(2))
            ->method('findById')
            ->willReturnCallback(function ($id) use ($payer, $payee) {
                if ($id == $payer->id) {
                    return $payer;
                }
                if ($id == $payee->id) {
                    return $payee;
                }
                return null;
            });

        $repository->expects($this->once())
            ->method('findByCorrelationId')
            ->with('correlation-123')
            ->willReturn(null);

        $transaction = new Transaction([
            'payer_id' => $payer->id,
            'payee_id' => $payee->id,
            'value' => 50.0,
            'correlation_id' => 'correlation-123',
            'status' => TransactionStatus::APPROVED,
        ]);
        $repository->expects($this->once())
            ->method('save')
            ->willReturn($transaction);

        $eventRepository->expects($this->exactly(3))
            ->method('save')
            ->with($this->isInstanceOf(Event::class));

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $result = $service->executeTransfer([
            'value' => 50.0,
            'payer' => $payer->id,
            'payee' => $payee->id,
            'correlation_id' => 'correlation-123'
        ]);

        $this->assertInstanceOf(Transaction::class, $result);
        $this->assertEquals(TransactionStatus::APPROVED, $result->status);

        // Check balances updated
        $payer->refresh();
        $payee->refresh();
        $this->assertEquals(50.0, $payer->balance);
        $this->assertEquals(100.0, $payee->balance);

        Queue::assertPushed(SendNotification::class);
    }

    public function test_execute_transfer_fails_payer_not_found(): void
    {
        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->once())
            ->method('findById')
            ->with(999)
            ->willReturn(null);

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Payer not found');

        $service->executeTransfer(['value' => 100.0, 'payer' => 999, 'payee' => 2, 'correlation_id' => 'correlation-123']);
    }

    public function test_execute_transfer_fails_payee_not_found(): void
    {
        $payer = User::factory()->create(['type' => UserType::COMMON, 'balance' => 100.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->exactly(2))
            ->method('findById')
            ->willReturnMap([
                [$payer->id, $payer],
                [999, null],
            ]);

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Payee not found');

        $service->executeTransfer(['value' => 100.0, 'payer' => $payer->id, 'payee' => 999, 'correlation_id' => 'correlation-123']);
    }

    public function test_execute_transfer_fails_payer_not_common(): void
    {
        $payer = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 100.0]);
        $payee = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 50.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->once())
            ->method('findById')
            ->with($payer->id)
            ->willReturn($payer);

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Only common users can make transfers');

        $service->executeTransfer(['value' => 50.0, 'payer' => $payer->id, 'payee' => $payee->id, 'correlation_id' => 'correlation-123']);
    }

    public function test_execute_transfer_fails_insufficient_balance(): void
    {
        $payer = User::factory()->create(['type' => UserType::COMMON, 'balance' => 10.0]);
        $payee = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 50.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->once())
            ->method('findById')
            ->with($payer->id)
            ->willReturn($payer);

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Insufficient balance');

        $service->executeTransfer(['value' => 50.0, 'payer' => $payer->id, 'payee' => $payee->id, 'correlation_id' => 'correlation-123']);
    }

    public function test_execute_transfer_fails_duplicate_correlation_id(): void
    {
        $payer = User::factory()->create(['type' => UserType::COMMON, 'balance' => 100.0]);
        $payee = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 50.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->exactly(2))
            ->method('findById')
            ->willReturnMap([
                [$payer->id, $payer],
                [$payee->id, $payee],
            ]);

        $existingTransaction = new Transaction(['correlation_id' => 'correlation-123']);
        $repository->expects($this->once())
            ->method('findByCorrelationId')
            ->with('correlation-123')
            ->willReturn($existingTransaction);

        $service = new TransferService($repository, $eventRepository, $userRepository);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Duplicate transfer');

        $service->executeTransfer(['value' => 50.0, 'payer' => $payer->id, 'payee' => $payee->id, 'correlation_id' => 'correlation-123']);
    }

    public function test_execute_transfer_fails_authorization(): void
    {
        $payer = User::factory()->create(['type' => UserType::COMMON, 'balance' => 100.0]);
        $payee = User::factory()->create(['type' => UserType::MERCHANT, 'balance' => 50.0]);

        $repository = $this->createMock(TransferRepositoryInterface::class);
        $eventRepository = $this->createMock(EventRepositoryInterface::class);
        $userRepository = $this->createMock(UserRepositoryInterface::class);

        $userRepository->expects($this->exactly(2))
            ->method('findById')
            ->willReturnMap([
                [$payer->id, $payer],
                [$payee->id, $payee],
            ]);

        $repository->expects($this->once())
            ->method('findByCorrelationId')
            ->willReturn(null);

        $service = $this->getMockBuilder(TransferService::class)
            ->setConstructorArgs([$repository, $eventRepository, $userRepository])
            ->onlyMethods(['authorizeTransfer'])
            ->getMock();

        $service->expects($this->once())
            ->method('authorizeTransfer')
            ->willReturn(false);

        $this->expectException(\Exception::class);
        $this->expectExceptionMessage('Transfer not authorized by external service');

        $service->executeTransfer(['value' => 50.0, 'payer' => $payer->id, 'payee' => $payee->id, 'correlation_id' => 'correlation-123']);
    }
}
