<?php

namespace App\Enums;

enum EventType: string
{
    case TRANSFER_INITIATED = 'TransferInitiated';
    case BALANCE_UPDATED = 'BalanceUpdated';
    case NOTIFICATION_SENT = 'NotificationSent';
    case NOTIFICATION_FAILED = 'NotificationFailed';
}
