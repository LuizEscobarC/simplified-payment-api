<?php

namespace App\Models;

use App\Enums\EventType;
use MongoDB\Laravel\Eloquent\Model;

class Event extends Model
{
    protected $connection = 'mongodb';

    protected $collection = 'events';

    protected $fillable = [
        'type',
        'data',
        'correlation_id',
        'timestamp',
    ];

    protected $casts = [
        'data' => 'array',
        'timestamp' => 'datetime',
        'type' => EventType::class,
    ];
}
