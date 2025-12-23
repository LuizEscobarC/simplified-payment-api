<?php

namespace App\Services;

use App\Repositories\TransferRepository;

class TransferService
{
    protected $repository;

    public function __construct(TransferRepository $repository)
    {
        $this->repository = $repository;
    }

    public function executeTransfer(array $data) {}
}
