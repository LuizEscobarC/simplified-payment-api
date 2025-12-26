<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class CircuitBreaker
{
    private int $failureCount = 0;

    private bool $isOpen = false;

    private const FAILURE_THRESHOLD = 5;

    public function authorizeTransfer(): bool
    {
        if ($this->isOpen) {
            return false;
        }

        for ($attempt = 1; $attempt <= 3; $attempt++) {
            try {
                $response = Http::timeout(5)->get('https://util.devi.tools/api/v2/authorize');

                if ($response->successful() && isset($response->json()['status'], $response->json()['data']['authorization']) && $response->json()['status'] === 'success' && $response->json()['data']['authorization']) {
                    $this->failureCount = 0;

                    return true;
                }
            } catch (\Exception $e) {
                if ($attempt < 3) {
                    sleep(2 ** ($attempt - 1));

                    continue;
                }
            }
        }

        $this->recordFailure();

        return false;
    }

    private function recordFailure(): void
    {
        $this->failureCount++;
        if ($this->failureCount >= self::FAILURE_THRESHOLD) {
            $this->isOpen = true;
        }
    }
}
