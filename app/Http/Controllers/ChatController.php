<?php

namespace App\Http\Controllers;

use App\Models\Conversation;
use App\Services\AIService;
use DeepSeek\DeepSeekClient;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use LucianoTonet\GroqPHP\Groq;

class ChatController extends Controller
{

    public function index()
    {
        return view('chat.index');
    }


    // public function chat(Request $request, AIService $ai)
    // public function chat(Request $request)
    // {
    //     // ============open ai=============
    //     // $reply = $ai->ask($request->message);

    //     // ============deepseek=============
    //     // $deepseek = app(DeepSeekClient::class);
    //     // $reply = $deepseek
    //     //     // ->query('You are a helpful assistant.', 'system')
    //     //     ->query($request->message, 'user')
    //     //     ->withModel("deepseek-v4-flash")  // Try this instead
    //     //     ->setTemperature(0.7)
    //     //     ->run();
    //     return response()->json([
    //         'reply' => $reply
    //     ]);
    // }


    public function chat(Request $request)
    {
        $request->validate([
            'message' => 'required|string|max:1000'
        ]);

        $sessionId = session()->getId();

        try {
            // Get or create conversation
            $conversation = Conversation::firstOrCreate(
                ['session_id' => $sessionId],
                ['messages' => '[]']
            );

            // ✅ FIX: Decode JSON string to array
            $messages = json_decode($conversation->messages, true);

            // If it's null or empty, initialize as empty array
            if (!is_array($messages) || empty($messages)) {
                $messages = [];

                // Add system prompt for new conversations
                $messages[] = [
                    'role' => 'system',
                    'content' => 'You are a helpful assistant. Remember the user\'s name and details throughout the conversation.'
                ];
            }

            // Add user's new message
            $messages[] = ['role' => 'user', 'content' => $request->message];

            // Make API call
            $groq = new Groq(env('GROQ_API_KEY'));

            $response = $groq->chat()->completions()->create([
                'model' => 'llama-3.1-8b-instant',
                'messages' => $messages,
                'temperature' => 0.7,
            ]);

            $reply = $response['choices'][0]['message']['content'];

            // Add AI's response to history
            $messages[] = ['role' => 'assistant', 'content' => $reply];

            // ✅ FIX: Encode back to JSON string for storage
            $conversation->messages = json_encode($messages);
            $conversation->save();

            return response()->json([
                'success' => true,
                'reply' => $reply
            ]);

        } catch (\Exception $e) {
            Log::error('Chat Error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => $e->getMessage()
            ], 500);
        }
    }


}
