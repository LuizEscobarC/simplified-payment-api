<?php

namespace Tests\Feature;

use App\Http\Controllers\TransferController;
use Tests\TestCase;

class TransferControllerTest extends TestCase
{
    public function test_transfer_controller_exists(): void
    {
        $this->assertTrue(class_exists(TransferController::class));
    }
}
