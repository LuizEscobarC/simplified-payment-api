<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class TransferRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'value' => 'required|numeric|min:0.01',
            'payer' => 'required|integer|exists:users,id',
            'payee' => 'required|integer|exists:users,id|different:payer',
            'correlation_id' => 'required|string|unique:transactions,correlation_id',
        ];
    }
}
