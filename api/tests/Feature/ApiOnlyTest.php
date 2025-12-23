<?php

namespace Tests\Feature;

use Tests\TestCase;

class ApiOnlyTest extends TestCase
{
    public function test_api_returns_json_response()
    {
        $response = $this->get('/api/nonexistent');

        $response->assertStatus(404);
        $response->assertHeader('Content-Type', 'application/json');
    }

    public function test_force_json_middleware()
    {
        $response = $this->get('/nonexistent');

        $response->assertStatus(404);
        $response->assertJson([
            'error' => 'route_not_found',
        ]);
    }
}
