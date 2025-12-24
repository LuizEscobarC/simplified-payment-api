<?php

namespace App\Repositories\Mysql;

use App\Models\Transaction;
use App\Repositories\Interfaces\TransferRepositoryInterface;

class EloquentTransferRepository implements TransferRepositoryInterface
{
    public function findById(int $id): ?Transaction
    {
        return Transaction::find($id);
    }

    public function save(Transaction $transaction): Transaction
    {
        $transaction->save();

        return $transaction;
    }

    public function findByCorrelationId(string $correlationId): ?Transaction
    {
        return Transaction::where('correlation_id', $correlationId)->first();
    }
}
