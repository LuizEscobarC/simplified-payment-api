<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "api" middleware group. Make something great!
|
*/

// API routes here

// Rota de teste para verificar se a API está funcionando
Route::get('/test', function () {
    return response()->json([
        'status' => 'success',
        'message' => 'API Laravel está funcionando!',
        'timestamp' => now()->toISOString()
    ]);
});