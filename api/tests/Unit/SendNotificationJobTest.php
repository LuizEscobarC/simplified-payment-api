<?php

namespace Tests\Unit;

use App\Jobs\SendNotification;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class SendNotificationJobTest extends TestCase
{
    use RefreshDatabase;

    public function test_send_notification_job_handles_successfully(): void
    {
        Log::spy();

        $data = [
            'transaction_id' => 123,
            'message' => 'Test message',
        ];

        $job = new SendNotification($data);
        $job->handle();

        Log::shouldHaveReceived('info')
            ->once()
            ->with('Sending notification for transaction 123: Test message');
    }

    public function test_send_notification_job_with_data(): void
    {
        Log::spy();

        $data = [
            'transaction_id' => 123,
            'message' => 'Transfer completed',
        ];

        $job = new SendNotification($data);
        $job->handle();

        Log::shouldHaveReceived('info')
            ->once()
            ->with('Sending notification for transaction 123: Transfer completed');
    }
}
