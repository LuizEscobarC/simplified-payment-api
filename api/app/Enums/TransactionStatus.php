<?php

namespace App\Enums;

enum TransactionStatus: string
{
    case PENDING = 'pending';
    case APPROVED = 'approved';
    case FAILED = 'failed';
}
