<?php

namespace App\Repositories;

interface TransferRepositoryInterface
{
    public function findById($id);
    public function create(array $data);
}