<?php

namespace App\Cache;

use App\Repositories\Mysql\TransferRepositoryInterface;
use Illuminate\Support\Facades\Cache;

class TransferRepositoryCacheDecorator implements TransferRepositoryInterface
{
    protected $repository;

    public function __construct(TransferRepositoryInterface $repository)
    {
        $this->repository = $repository;
    }

    public function findById(int $id): ?Transaction
    {
        return Cache::remember("transaction_{$id}", 60, function () use ($id) {
            return $this->repository->findById($id);
        });
    }

    public function save(Transaction $transaction): Transaction
    {
        $transaction = $this->repository->save($transaction);
        Cache::forget("transaction_{$transaction->id}");

        return $transaction;
    }

    public function findByCorrelationId(string $correlationId): ?Transaction
    {
        return $this->repository->findByCorrelationId($correlationId);
    }
}
