<?php
namespace App\Services;

use OpenAI\Laravel\Facades\OpenAI;

class AIService
{
    /**
     * Create a new class instance.
     */
    public function __construct()
    {
        //
    }

    public function ask(string $message)
    {
        $response = OpenAI::chat()->create([
            // 'model' => 'gpt-4.1',
            'model' => 'gpt-3.5-turbo',
            'messages' => [
                [
                    'role' => 'user',
                    'content' => $message
                ]
            ]
        ]);

        return $response->choices[0]->message->content;
    }
}
