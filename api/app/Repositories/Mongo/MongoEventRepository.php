<?php

namespace App\Repositories\Mongo;

use App\Enums\EventType;
use App\Models\Event;
use App\Repositories\Interfaces\EventRepositoryInterface;
use Illuminate\Support\Collection;

class MongoEventRepository implements EventRepositoryInterface
{
    public function save(Event $event): Event
    {
        $event->save();

        return $event;
    }

    public function getBalanceEventsForUser(int $userId): Collection
    {
        return Event::where('type', EventType::BALANCE_UPDATED)
            ->where('data.user_id', $userId)
            ->orderBy('timestamp')
            ->get();
    }
}
