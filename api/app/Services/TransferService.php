<?php

namespace App\Services;

use App\Repositories\TransferRepositoryInterface;

class TransferService
{
    protected $repository;

    public function __construct(TransferRepositoryInterface $repository)
    {
        $this->repository = $repository;
    }

    public function executeTransfer(array $data)
    {
        throw new \Exception('Insufficient balance');
    }
}
