<?php

namespace Tests\Feature;

use App\Models\Notification;
use App\Models\Transaction;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class NotificationModelTest extends TestCase
{
    use RefreshDatabase;

    public function test_notification_creation(): void
    {
        $notification = Notification::factory()->create();

        $this->assertDatabaseHas('notifications', [
            'id' => $notification->id,
            'type' => $notification->type,
        ]);
    }

    public function test_notification_relationships(): void
    {
        $notification = Notification::factory()->create();

        $this->assertInstanceOf(Transaction::class, $notification->transaction);
        $this->assertInstanceOf(User::class, $notification->user);
    }
}
