<?php

namespace App\Repositories;

use App\Repositories\TransferRepositoryInterface;
use Illuminate\Support\Facades\Cache;

class CachedTransferRepository implements TransferRepositoryInterface
{
    protected $repository;

    public function __construct(TransferRepositoryInterface $repository)
    {
        $this->repository = $repository;
    }

    public function findById($id)
    {
        return Cache::remember("transaction_{$id}", 60, function () use ($id) {
            return $this->repository->findById($id);
        });
    }

    public function create(array $data)
    {
        $transaction = $this->repository->create($data);
        Cache::forget("transaction_{$transaction->id}");

        return $transaction;
    }
}