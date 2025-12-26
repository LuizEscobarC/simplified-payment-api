<?php

namespace Tests\Feature;

use App\Services\CircuitBreaker;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class CircuitBreakerTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
    }

    public function test_authorize_transfer_success(): void
    {
        Http::fake([
            'https://util.devi.tools/api/v2/authorize' => Http::response(['status' => 'success', 'data' => ['authorization' => true]], 200),
        ]);

        $circuitBreaker = new CircuitBreaker;
        $result = $circuitBreaker->authorizeTransfer();

        $this->assertTrue($result);
    }

    public function test_authorize_transfer_failure_opens_circuit(): void
    {
        Http::fake([
            'https://util.devi.tools/api/v2/authorize' => Http::response(['status' => 'fail'], 200),
        ]);

        $circuitBreaker = new CircuitBreaker;

        for ($i = 0; $i < 5; $i++) {
            $result = $circuitBreaker->authorizeTransfer();
            $this->assertFalse($result);
        }

        // Now circuit should be open
        $result = $circuitBreaker->authorizeTransfer();
        $this->assertFalse($result); // Should return false because circuit is open
    }

    public function test_authorize_transfer_exception_opens_circuit(): void
    {
        Http::fake([
            'https://util.devi.tools/api/v2/authorize' => Http::response('', 500),
        ]);

        $circuitBreaker = new CircuitBreaker;

        for ($i = 0; $i < 5; $i++) {
            $result = $circuitBreaker->authorizeTransfer();
            $this->assertFalse($result);
        }

        // Circuit open
        $result = $circuitBreaker->authorizeTransfer();
        $this->assertFalse($result);
    }
}
