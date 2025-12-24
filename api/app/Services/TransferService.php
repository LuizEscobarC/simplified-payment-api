<?php

namespace App\Services;

use App\Jobs\SendNotification;
use App\Models\Event;
use App\Models\User;
use App\Repositories\EventRepositoryInterface;
use App\Repositories\TransferRepositoryInterface;
use Illuminate\Support\Facades\DB;

class TransferService
{
    protected $repository;

    protected $eventRepository;

    public function __construct(TransferRepositoryInterface $repository, EventRepositoryInterface $eventRepository)
    {
        $this->repository = $repository;
        $this->eventRepository = $eventRepository;
    }

    public function executeTransfer(array $data)
    {
        $payer = User::find($data['payer']);
        if (! $payer) {
            throw new \Exception('Payer not found');
        }
        if ($payer->type !== 'common') {
            throw new \Exception('Only common users can make transfers');
        }

        if ($payer->balance < $data['value']) {
            throw new \Exception('Insufficient balance');
        }

        // TODO: call external authorizer service (mock during tests)
        // TODO: save immutable events to MongoDB and wrap DB updates in transaction
        // TODO: dispatch notification job to Redis queue

        $payee = User::find($data['payee']);
        if (! $payee) {
            throw new \Exception('Payee not found');
        }

        // Check if correlation_id already exists
        if ($this->repository->findByCorrelationId($data['correlation_id'])) {
            throw new \Exception('Duplicate transfer');
        }

        // Call authorizer
        if (! $this->authorizeTransfer($data)) {
            throw new \Exception('Transfer not authorized by external service');
        }

        // Save TransferInitiated event
        $transferInitiatedEvent = new Event([
            'type' => 'TransferInitiated',
            'data' => [
                'payer_id' => $data['payer'],
                'payee_id' => $data['payee'],
                'value' => $data['value'],
                'correlation_id' => $data['correlation_id'],
            ],
            'correlation_id' => $data['correlation_id'],
            'timestamp' => now(),
        ]);
        $this->eventRepository->save($transferInitiatedEvent);

        $transaction = DB::transaction(function () use ($data, $payer, $payee) {
            // Capture old balances
            $oldPayerBalance = floatval($payer->balance);
            $oldPayeeBalance = floatval($payee->balance);

            // Update balances
            $payer->balance = $oldPayerBalance - floatval($data['value']);
            $payee->balance = $oldPayeeBalance + floatval($data['value']);
            $payer->save();
            $payee->save();

            // Save BalanceUpdated events
            $payerBalanceUpdatedEvent = new Event([
                'type' => 'BalanceUpdated',
                'data' => [
                    'user_id' => $payer->id,
                    'old_balance' => $oldPayerBalance,
                    'new_balance' => $payer->balance,
                    'change' => -$data['value'],
                ],
                'correlation_id' => $data['correlation_id'],
                'timestamp' => now(),
            ]);
            $this->eventRepository->save($payerBalanceUpdatedEvent);

            $payeeBalanceUpdatedEvent = new Event([
                'type' => 'BalanceUpdated',
                'data' => [
                    'user_id' => $payee->id,
                    'old_balance' => $oldPayeeBalance,
                    'new_balance' => $payee->balance,
                    'change' => $data['value'],
                ],
                'correlation_id' => $data['correlation_id'],
                'timestamp' => now(),
            ]);
            $this->eventRepository->save($payeeBalanceUpdatedEvent);

            // Save transaction
            $transaction = new \App\Models\Transaction([
                'payer_id' => $data['payer'],
                'payee_id' => $data['payee'],
                'value' => $data['value'],
                'correlation_id' => $data['correlation_id'],
                'status' => 'approved', // or whatever
            ]);

            return $this->repository->save($transaction);
        });

        // Dispatch notification job
        SendNotification::dispatch([
            'transaction_id' => $transaction->id,
            'message' => 'Transfer completed successfully',
        ]);

        return $transaction;
    }

    protected function authorizeTransfer(array $data): bool
    {
        // Mock implementation - in real app, call external service
        // For tests, this can be overridden
        return true;
    }
}
