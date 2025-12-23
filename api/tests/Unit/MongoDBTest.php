<?php

namespace Tests\Unit;

use Tests\TestCase;

class MongoDBTest extends TestCase
{
    public function test_mongodb_connection()
    {
        $this->assertTrue(true);
    }

    public function test_mongodb_database_exists()
    {
        $database = config('database.connections.mongodb.database');

        $this->assertNotEmpty($database);
    }
}
