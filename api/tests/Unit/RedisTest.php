<?php

namespace Tests\Unit;

use App\Jobs\TestQueueJob;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Redis;
use Tests\TestCase;

class RedisTest extends TestCase
{
    public function test_redis_connection()
    {
        $result = Redis::ping();

        $this->assertEquals('PONG', $result);
    }

    public function test_redis_set_and_get()
    {
        Redis::set('test_key', 'test_value');

        $value = Redis::get('test_key');

        $this->assertEquals('test_value', $value);

        Redis::del('test_key');
    }

    public function test_redis_as_cache()
    {
        // Test cache functionality
        Redis::setex('cache_key', 60, 'cached_value');

        $value = Redis::get('cache_key');

        $this->assertEquals('cached_value', $value);

        // Test expiration (this might not work immediately, but tests the command)
        $ttl = Redis::ttl('cache_key');
        $this->assertGreaterThan(0, $ttl);
        $this->assertLessThanOrEqual(60, $ttl);

        Redis::del('cache_key');
    }

    public function test_redis_as_queue_broker()
    {
        // Test that Redis can be used as queue broker
        Queue::push(new TestQueueJob);

        // Check if job is in the queue
        $queuedJobs = Redis::lrange('queues:default', 0, -1);

        $this->assertNotEmpty($queuedJobs);

        // Clean up - remove the job from queue
        Redis::del('queues:default');
    }
}
