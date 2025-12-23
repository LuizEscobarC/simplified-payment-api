<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseMigrations;
use Tests\TestCase;

class UserModelTest extends TestCase
{
    use DatabaseMigrations;

    protected $connection = 'testing';

    public function test_user_creation(): void
    {
        $user = User::factory()->create();

        $this->assertDatabaseHas('users', [
            'id' => $user->id,
            'name' => $user->name,
            'email' => $user->email,
        ]);
    }

    public function test_user_unique_email(): void
    {
        $this->expectException(\Illuminate\Database\QueryException::class);

        User::factory()->create(['email' => 'test@example.com']);
        User::factory()->create(['email' => 'test@example.com']);
    }

    public function test_user_unique_cpf_cnpj(): void
    {
        $this->expectException(\Illuminate\Database\QueryException::class);

        User::factory()->create(['cpf_cnpj' => '12345678901']);
        User::factory()->create(['cpf_cnpj' => '12345678901']);
    }
}
