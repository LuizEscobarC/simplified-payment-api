<?php

namespace App\Providers;

use App\Cache\TransferRepositoryCacheDecorator;
use App\Cache\UserRepositoryCacheDecorator;
use App\Policies\TransferPolicy;
use App\Repositories\Interfaces\EventRepositoryInterface;
use App\Repositories\Interfaces\TransferRepositoryInterface;
use App\Repositories\Interfaces\UserRepositoryInterface;
use App\Repositories\Mongo\MongoEventRepository;
use App\Repositories\Mysql\EloquentTransferRepository;
use App\Repositories\Mysql\EloquentUserRepository;
use App\Services\CircuitBreaker;
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

        $this->app->bind(UserRepositoryInterface::class, function ($app) {
            return new UserRepositoryCacheDecorator($app->make(EloquentUserRepository::class));
        });
        $this->app->bind(EventRepositoryInterface::class, MongoEventRepository::class);
        $this->app->bind(TransferPolicy::class, function ($app) {
            return new TransferPolicy($app->make(CircuitBreaker::class));
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
