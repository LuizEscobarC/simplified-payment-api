<?php

namespace App\Repositories\Mongo;

use App\Models\Event;

interface EventRepositoryInterface
{
    public function save(Event $event): Event;
}
