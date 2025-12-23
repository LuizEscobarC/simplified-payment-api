<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Notification>
 */
class NotificationFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'transaction_id' => \App\Models\Transaction::factory(),
            'user_id' => \App\Models\User::factory(),
            'type' => $this->faker->randomElement(['email', 'sms']),
            'status' => $this->faker->randomElement(['queued', 'sent', 'failed']),
            'message' => $this->faker->sentence(),
            'sent_at' => $this->faker->optional()->dateTime(),
        ];
    }
}
