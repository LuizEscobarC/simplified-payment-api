<?php

namespace Tests\Feature;

use App\Models\AuditLog;
use App\Models\Transaction;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AuditLogModelTest extends TestCase
{
    use RefreshDatabase;

    protected $connection = 'testing';

    public function test_audit_log_creation(): void
    {
        $auditLog = AuditLog::factory()->create();

        $this->assertDatabaseHas('audit_logs', [
            'id' => $auditLog->id,
            'action' => $auditLog->action,
        ]);
    }

    public function test_audit_log_relationships(): void
    {
        $auditLog = AuditLog::factory()->create();

        $this->assertInstanceOf(User::class, $auditLog->user);
        $this->assertInstanceOf(Transaction::class, $auditLog->transaction);
    }
}
