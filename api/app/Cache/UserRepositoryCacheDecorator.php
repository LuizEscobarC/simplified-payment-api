<?php

namespace App\Cache;

use App\Models\User;
use App\Repositories\Interfaces\UserRepositoryInterface;
use Illuminate\Support\Facades\Cache;

class UserRepositoryCacheDecorator implements UserRepositoryInterface
{
    protected $repository;

    public function __construct(UserRepositoryInterface $repository)
    {
        $this->repository = $repository;
    }

    public function findById(int $id): ?User
    {
        return Cache::remember("user_{$id}", 60, function () use ($id) {
            return $this->repository->findById($id);
        });
    }
}
