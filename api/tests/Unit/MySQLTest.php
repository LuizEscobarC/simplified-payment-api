<?php

namespace Tests\Unit;

use Illuminate\Support\Facades\DB;
use Tests\TestCase;

class MySQLTest extends TestCase
{
    public function test_mysql_connection()
    {
        $result = DB::select('SELECT 1 as test');

        $this->assertEquals(1, $result[0]->test);
    }

    public function test_mysql_database_exists()
    {
        $database = config('database.connections.mysql.database');

        $this->assertNotEmpty($database);
    }
}
