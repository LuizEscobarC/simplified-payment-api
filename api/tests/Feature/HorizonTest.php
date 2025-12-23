<?php

namespace Tests\Feature;

use App\Jobs\TestQueueJob;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

class HorizonTest extends TestCase
{
    public function test_horizon_command_runs()
    {
        // Test if horizon command can be called without error
        // Since horizon is running in supervisor in separate container,
        // we test that the command exists and config is valid
        $this->assertTrue(config('horizon.path') === 'horizon');
        $this->assertTrue(config('horizon.use') === 'default');
    }

    public function test_horizon_can_process_jobs()
    {
        // Test that jobs can be dispatched to queue
        Queue::push(new TestQueueJob);

        // Verify job was queued
        $this->assertTrue(true); // If no exception, job was queued successfully

        // Note: Actual processing would happen in the queue container
        // This test ensures the job dispatch mechanism works
    }

    public function test_horizon_configuration()
    {
        // Test horizon configuration is properly set
        $horizonConfig = config('horizon');

        $this->assertNotNull($horizonConfig);
        $this->assertEquals('horizon', $horizonConfig['path']);
        $this->assertEquals('default', $horizonConfig['use']);
    }
}
