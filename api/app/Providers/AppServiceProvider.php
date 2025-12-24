<?php

namespace App\Providers;

use App\Cache\TransferRepositoryCacheDecorator;
use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use App\Repositories\Mongo\MongoEventRepository;
use App\Repositories\Mysql\EloquentTransferRepository;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->bind(TransferRepositoryInterface::class, function ($app) {
            return new TransferRepositoryCacheDecorator($app->make(EloquentTransferRepository::class));
        });
        $this->app->bind(EventRepositoryInterface::class, MongoEventRepository::class);
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
