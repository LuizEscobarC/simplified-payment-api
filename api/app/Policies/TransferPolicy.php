<?php

namespace App\Policies;

use App\Enums\UserType;
use App\Models\Transaction;
use App\Models\User;

class TransferPolicy
{
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

    /**
     * TODO: Authorize the transfer with external service.
     * Mock implementation - in real app, call external service.
     */
    public function isAuthorized(array $data): bool
    {
        // Mock implementation
        return true;
    }
}
