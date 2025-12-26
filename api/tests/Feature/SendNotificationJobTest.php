<?php

namespace Tests\Feature;

use App\Jobs\SendNotification;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class SendNotificationJobTest extends TestCase
{
    use RefreshDatabase;

    public function test_send_notification_job_handles_successfully(): void
    {
        Http::fake([
            'https://util.devi.tools/api/v1/notify' => Http::response([], 200),
        ]);

        $data = [
            'transaction_id' => 123,
            'message' => 'Test message',
        ];

        $job = new SendNotification($data);
        $job->handle();

        Http::assertSent(function ($request) {
            return $request->url() === 'https://util.devi.tools/api/v1/notify' &&
                   $request->method() === 'POST' &&
                   $request['transaction_id'] == 123 &&
                   $request['message'] === 'Test message';
        });
    }

    public function test_send_notification_job_with_failure_logs_locally(): void
    {
        Http::fake([
            'https://util.devi.tools/api/v1/notify' => Http::response([], 500),
        ]);

        $data = [
            'transaction_id' => 123,
            'message' => 'Transfer completed',
        ];

        $job = new SendNotification($data);
        $job->handle();

        Http::assertSent(function ($request) {
            return $request->url() === 'https://util.devi.tools/api/v1/notify' &&
                   $request->method() === 'POST' &&
                   $request['transaction_id'] == 123 &&
                   $request['message'] === 'Transfer completed';
        });
    }
}
