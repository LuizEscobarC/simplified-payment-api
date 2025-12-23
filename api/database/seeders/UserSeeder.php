<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class UserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        \App\Models\User::factory(10)->create([
            'type' => 'user',
            'balance' => 1000.00,
        ]);

        \App\Models\User::factory(5)->create([
            'type' => 'shopkeeper',
            'balance' => 0.00,
        ]);
    }
}
