<?php

namespace App\Services;

use App\Enums\EventType;
use App\Enums\TransactionStatus;
use App\Enums\UserType;
use App\Jobs\SendNotification;
use App\Models\Event;
use App\Models\User;
use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use App\Repositories\Interfaces\UserRepositoryInterface;
use Illuminate\Support\Facades\DB;

class TransferService
{
    public function __construct(private TransferRepositoryInterface $repository, private EventRepositoryInterface $eventRepository, private UserRepositoryInterface $userRepository) {}

    public function executeTransfer(array $data)
    {
        $payer = $this->validatePayer($data);
        $payee = $this->validatePayee($data);
        $this->checkIdempotency($data);
        $this->authorizeTransferOrFail($data);
        $this->saveTransferInitiatedEvent($data);

        $transaction = $this->performTransferInTransaction($data, $payer, $payee);
        $this->dispatchNotification($transaction);

        return $transaction;
    }

    private function validatePayer(array $data): User
    {
        $payer = $this->userRepository->findById($data['payer']);
        if (! $payer) {
            throw new \Exception('Payer not found');
        }
        if ($payer->type !== UserType::COMMON) {
            throw new \Exception('Only common users can make transfers');
        }
        if ($payer->balance < $data['value']) {
            throw new \Exception('Insufficient balance');
        }

        return $payer;
    }

    private function validatePayee(array $data): User
    {
        $payee = $this->userRepository->findById($data['payee']);
        if (! $payee) {
            throw new \Exception('Payee not found');
        }

        return $payee;
    }

    private function checkIdempotency(array $data): void
    {
        if ($this->repository->findByCorrelationId($data['correlation_id'])) {
            throw new \Exception('Duplicate transfer');
        }
    }

    private function authorizeTransferOrFail(array $data): void
    {
        if (! $this->authorizeTransfer($data)) {
            throw new \Exception('Transfer not authorized by external service');
        }
    }

    private function saveTransferInitiatedEvent(array $data): void
    {
        $event = new Event([
            'type' => EventType::TRANSFER_INITIATED,
            'data' => [
                'payer_id' => $data['payer'],
                'payee_id' => $data['payee'],
                'value' => $data['value'],
                'correlation_id' => $data['correlation_id'],
            ],
            'correlation_id' => $data['correlation_id'],
            'timestamp' => now(),
        ]);
        $this->eventRepository->save($event);
    }

    private function performTransferInTransaction(array $data, User $payer, User $payee): \App\Models\Transaction
    {
        return DB::transaction(function () use ($data, $payer, $payee) {
            $oldPayerBalance = floatval($payer->balance);
            $oldPayeeBalance = floatval($payee->balance);

            $payer->balance = $oldPayerBalance - floatval($data['value']);
            $payee->balance = $oldPayeeBalance + floatval($data['value']);
            $payer->save();
            $payee->save();

            $this->saveBalanceUpdatedEvent($payer->id, $oldPayerBalance, $payer->balance, -$data['value'], $data['correlation_id']);
            $this->saveBalanceUpdatedEvent($payee->id, $oldPayeeBalance, $payee->balance, $data['value'], $data['correlation_id']);

            $transaction = new \App\Models\Transaction([
                'payer_id' => $data['payer'],
                'payee_id' => $data['payee'],
                'value' => $data['value'],
                'correlation_id' => $data['correlation_id'],
                'status' => TransactionStatus::APPROVED,
            ]);

            return $this->repository->save($transaction);
        });
    }

    private function saveBalanceUpdatedEvent(int $userId, float $oldBalance, float $newBalance, float $change, string $correlationId): void
    {
        $event = new Event([
            'type' => EventType::BALANCE_UPDATED,
            'data' => [
                'user_id' => $userId,
                'old_balance' => $oldBalance,
                'new_balance' => $newBalance,
                'change' => $change,
            ],
            'correlation_id' => $correlationId,
            'timestamp' => now(),
        ]);
        $this->eventRepository->save($event);
    }

    private function dispatchNotification(\App\Models\Transaction $transaction): void
    {
        SendNotification::dispatch([
            'transaction_id' => $transaction->id,
            'message' => 'Transfer completed successfully',
        ]);
    }

    protected function authorizeTransfer(array $data): bool
    {
        // Mock implementation - in real app, call external service
        return true;
    }
}
