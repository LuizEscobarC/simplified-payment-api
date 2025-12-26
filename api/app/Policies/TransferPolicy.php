<?php

namespace App\Policies;

use App\Enums\UserType;
use App\Models\Transaction;
use App\Models\User;
use App\Services\CircuitBreaker;

class TransferPolicy
{
    public function __construct(private CircuitBreaker $circuitBreaker) {}

    public function canTransfer(User $user, float $amount): bool
    {
        return $user->type === UserType::COMMON && $user->hasSufficientBalance($amount);
    }

    public function canReceive(User $user): bool
    {
        return $user->type === UserType::MERCHANT;
    }

    public function isIdempotent(string $correlationId): bool
    {
        return ! Transaction::byCorrelationId($correlationId)->exists();
    }

    public function isAuthorized(array $data): bool
    {
        return $this->circuitBreaker->authorizeTransfer();
    }
}
