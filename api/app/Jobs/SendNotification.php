<?php

namespace App\Jobs;

use App\Enums\EventType;
use App\Models\Event;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Http;

class SendNotification implements ShouldQueue
{
    use Queueable;

    public $data;

    public function __construct(array $data)
    {
        $this->data = $data;
    }

    public function handle(): void
    {
        try {
            $response = Http::post('https://util.devi.tools/api/v1/notify', [
                'transaction_id' => $this->data['transaction_id'],
                'message' => $this->data['message'],
            ]);

            if ($response->successful()) {
                $this->logNotificationLocally('sent');
            } else {
                $this->logNotificationLocally('failed');
            }
        } catch (\Exception $e) {
            $this->logNotificationLocally('error');
        }
    }

    private function logNotificationLocally(string $status): void
    {
        $event = new Event([
            'type' => $status === 'failed' ? EventType::NOTIFICATION_FAILED : EventType::NOTIFICATION_SENT,
            'data' => $this->data,
            'correlation_id' => 'notification-'.$this->data['transaction_id'],
            'timestamp' => now(),
        ]);

        $event->save();
    }
}
