<?php

namespace App\Http\Controllers;

use App\Http\Requests\TransferRequest;
use App\Services\TransferService;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Log;

class TransferController extends Controller
{
    protected $transferService;

    public function __construct(TransferService $transferService)
    {
        $this->transferService = $transferService;
    }

    public function transfer(TransferRequest $request): JsonResponse
    {
        $data = $request->validated();

        try {
            $result = $this->transferService->executeTransfer($data);

            return response()->json(['message' => 'Transfer successful', 'data' => $result], 200);
        } catch (\Exception $e) {
            Log::error('Transfer failed: '.$e->getMessage());

            $status = in_array($e->getMessage(), [
                'Transfer not authorized by external service',
                'Duplicate transfer',
                'Insufficient balance',
                'Payer not found',
                'Payee not found',
                'Only common users can make transfers',
            ]) ? 422 : 500;

            return response()->json(['message' => $e->getMessage()], $status);
        }
    }
}
