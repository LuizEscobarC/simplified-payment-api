<?php

namespace Tests\Unit;

use App\Enums\EventType;
use App\Models\Event;
use App\Repositories\Mongo\MongoEventRepository;
use Mockery;
use Tests\TestCase;

class EventRepositoryTest extends TestCase
{
    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function test_save_event(): void
    {
        $event = Mockery::mock(Event::class);
        $event->shouldReceive('save')->andReturn(true);
        $event->shouldReceive('getAttribute')
            ->with('correlation_id')
            ->andReturn('test-123');
        $event->shouldReceive('getAttribute')
            ->with('type')
            ->andReturn(EventType::TRANSFER_INITIATED);
        $event->shouldReceive('setAttribute')->andReturnSelf();

        $repository = new MongoEventRepository;

        $saved = $repository->save($event);

        $this->assertInstanceOf(Event::class, $saved);
        $this->assertEquals('test-123', $saved->correlation_id);
        $this->assertEquals(EventType::TRANSFER_INITIATED, $saved->type);
    }
}
