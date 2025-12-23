<?php

namespace App\Repositories;

use App\Models\Transaction;
use App\Repositories\TransferRepositoryInterface;

class TransferRepository implements TransferRepositoryInterface
{
    protected $model;

    public function __construct(Transaction $model)
    {
        $this->model = $model;
    }

    public function findById($id)
    {
        return $this->model->find($id);
    }

    public function create(array $data)
    {
        return $this->model->create($data);
    }
}
