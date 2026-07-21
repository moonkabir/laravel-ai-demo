<?php

use App\Http\Controllers\ChatController;
use App\Http\Controllers\DocumentController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});


// Document routes
Route::get('/documents', [DocumentController::class, 'index'])->name('documents.index');
Route::post('/documents/upload', [DocumentController::class, 'upload'])->name('documents.upload');
Route::delete('/documents/{id}', [DocumentController::class, 'delete'])->name('documents.delete');
Route::get('/documents/search', [DocumentController::class, 'search'])->name('documents.search');

// Chat routes
Route::get('/chat', [ChatController::class, 'index'])->name('chat.index');
Route::post('/chat', [ChatController::class, 'chat'])->name('chat.send');
Route::delete('/chat/clear', [ChatController::class, 'clear'])->name('chat.clear');
Route::get('/chat/history', [ChatController::class, 'history'])->name('chat.history');
