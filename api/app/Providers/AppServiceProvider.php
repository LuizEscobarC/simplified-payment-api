<?php

namespace App\Providers;

use App\Cache\TransferRepositoryCacheDecorator;
use App\Repositories\Mongo\EventRepositoryInterface as MongoEventRepositoryInterface;
use App\Repositories\Mongo\MongoEventRepository;
use App\Repositories\Mysql\EloquentTransferRepository;
use App\Repositories\Mysql\TransferRepositoryInterface as MysqlTransferRepositoryInterface;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->bind(MysqlTransferRepositoryInterface::class, EloquentTransferRepository::class);
        $this->app->bind(MongoEventRepositoryInterface::class, MongoEventRepository::class);

        $this->app->bind(\App\Repositories\TransferRepositoryInterface::class, function ($app) {
            return new TransferRepositoryCacheDecorator($app->make(MysqlTransferRepositoryInterface::class));
        });

        $this->app->bind(\App\Repositories\Mongo\EventRepositoryInterface::class, MongoEventRepository::class);
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
