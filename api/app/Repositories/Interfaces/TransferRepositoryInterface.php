<?php

namespace App\Repositories\Interfaces;

interface TransferRepositoryInterface
{
    public function findById($id);
    public function create(array $data);
}