<?php

namespace App\Repositories\Mongo;

use App\Models\Event;
use App\Repositories\Interfaces\EventRepositoryInterface;

class MongoEventRepository implements EventRepositoryInterface
{
    public function save(Event $event): Event
    {
        $event->save();

        return $event;
    }
}
