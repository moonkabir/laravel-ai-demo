<?php
// app/Http/Controllers/ChatController.php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Session;
use App\Models\Conversation;
use App\Services\AIService;
use DeepSeek\DeepSeekClient;
use LucianoTonet\GroqPHP\Groq;

class ChatController extends Controller
{
    protected $pythonApiUrl;

    public function __construct()
    {
        $this->pythonApiUrl = env('PYTHON_API_URL', 'http://localhost:8001');
    }

    /**
     * Show the chat interface
     */
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


    /**
     * Send a chat message
     */
    public function chat(Request $request)
    {
        $request->validate([
            'message' => 'required|string|max:1000'
        ]);

        $sessionId = session()->getId();
        $message = $request->message;

        try {
            // Get conversation history from session
            $history = session('chat_history', []);

            // Send to Python service
            $response = Http::post("{$this->pythonApiUrl}/chat", [
                'message' => $message,
                'session_id' => $sessionId,
                'conversation_history' => $history
            ]);

            if ($response->successful()) {
                $data = $response->json();

                // Update session history
                $history[] = ['role' => 'user', 'content' => $message];
                $history[] = ['role' => 'assistant', 'content' => $data['reply']];
                session(['chat_history' => $history]);

                return response()->json([
                    'success' => true,
                    'reply' => $data['reply'],
                    'sources' => $data['sources'] ?? []
                ]);
            } else {
                throw new \Exception($response->body() ?? 'Python service error');
            }

        } catch (\Exception $e) {
            Log::error('Chat error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Failed to get response: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Clear chat history
     */
    public function clear()
    {
        session()->forget('chat_history');

        return response()->json([
            'success' => true,
            'message' => 'Chat history cleared'
        ]);
    }

    /**
     * Get chat history
     */
    public function history()
    {
        $history = session('chat_history', []);

        return response()->json([
            'success' => true,
            'history' => $history
        ]);
    }
}
