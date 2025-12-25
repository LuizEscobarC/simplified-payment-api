<?php

namespace App\Repositories\Mysql;

use App\Models\User;
use App\Repositories\Interfaces\UserRepositoryInterface;

class EloquentUserRepository implements UserRepositoryInterface
{
    public function findById(int $id): ?User
    {
        return User::find($id);
    }
}
