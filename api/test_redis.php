<?php

require 'vendor/autoload.php';

$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

var_dump(getenv('REDIS_PASSWORD'));
var_dump(env('REDIS_PASSWORD'));

$config = config('database.redis.default');
var_dump($config['password']);
var_dump(empty($config['password']));

$redis = new Redis;
$redis->connect($config['host'], $config['port']);
echo $redis->ping();
