<?php

namespace Tests\Unit;

use App\Http\Requests\TransferRequest;
use Tests\TestCase;

class TransferRequestTest extends TestCase
{
    public function test_transfer_request_validation_fails_with_invalid_data(): void
    {
        $request = new TransferRequest;
        $validator = validator([
            'value' => 'invalid',
            'payer' => 'not_int',
            'payee' => 'not_int',
            'correlation_id' => '',
        ], $request->rules());

        $this->assertTrue($validator->fails());
    }
}
