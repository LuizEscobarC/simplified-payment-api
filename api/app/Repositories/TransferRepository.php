<?php

namespace App\Repositories;

use App\Models\Transaction;
use Illuminate\Support\Facades\Cache;

class TransferRepository
{
    protected $model;

    public function __construct(Transaction $model)
    {
        $this->model = $model;
    }

    public function findById($id)
    {
        return Cache::remember("transaction_{$id}", 60, function () use ($id) {
            return $this->model->find($id);
        });
    }

    public function create(array $data)
    {
        $transaction = $this->model->create($data);
        Cache::forget("transaction_{$transaction->id}");

        return $transaction;
    }
}
