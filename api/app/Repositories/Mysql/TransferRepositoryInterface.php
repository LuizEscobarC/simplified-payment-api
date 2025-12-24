<?php

namespace App\Repositories\Mysql;

use App\Models\Transaction;

interface TransferRepositoryInterface
{
    public function findById(int $id): ?Transaction;

    public function save(Transaction $transaction): Transaction;

    public function findByCorrelationId(string $correlationId): ?Transaction;
}
