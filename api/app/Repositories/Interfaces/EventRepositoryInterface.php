<?php

namespace App\Repositories\Interfaces;

use App\Models\Event;

interface EventRepositoryInterface
{
    public function save(Event $event): Event;

    public function getBalanceEventsForUser(int $userId): \Illuminate\Support\Collection;
}
