<?php
// app/Http/Controllers/DocumentController.php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class DocumentController extends Controller
{
    protected $pythonApiUrl;

    public function __construct()
    {
        $this->pythonApiUrl = env('PYTHON_API_URL', 'http://localhost:8001');
    }

    /**
     * Display the document management page
     */
    public function index()
    {
        // Fetch documents from Python service
        try {
            $response = Http::get("{$this->pythonApiUrl}/documents");
            $documents = $response->successful() ? $response->json()['documents'] ?? [] : [];
        } catch (\Exception $e) {
            Log::error('Failed to fetch documents: ' . $e->getMessage());
            $documents = [];
        }

        return view('documents.index', compact('documents'));
    }

    /**
     * Upload a document
     */
    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|file|max:20480|mimes:pdf,jpg,jpeg,png,gif,bmp,docx,txt',
            'title' => 'required|string|max:255'
        ]);

        try {
            $file = $request->file('file');

            // Send to Python service
            $response = Http::attach(
                'file',
                file_get_contents($file->getRealPath()),
                $file->getClientOriginalName()
            )->post("{$this->pythonApiUrl}/upload-document", [
                'title' => $request->title
            ]);

            if ($response->successful()) {
                $data = $response->json();
                return response()->json([
                    'success' => true,
                    'message' => $data['message'] ?? 'Document uploaded successfully',
                    'document_id' => $data['document_id'] ?? null,
                    'chunks' => $data['chunks'] ?? 0
                ]);
            } else {
                throw new \Exception($response->body() ?? 'Python service error');
            }

        } catch (\Exception $e) {
            Log::error('Document upload error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Failed to upload document: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Delete a document
     */
    public function delete($id)
    {
        try {
            $response = Http::delete("{$this->pythonApiUrl}/document/{$id}");

            if ($response->successful()) {
                return response()->json([
                    'success' => true,
                    'message' => 'Document deleted successfully'
                ]);
            } else {
                throw new \Exception($response->body() ?? 'Failed to delete document');
            }

        } catch (\Exception $e) {
            Log::error('Document delete error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Failed to delete document: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Search documents
     */
    public function search(Request $request)
    {
        $query = $request->get('q');

        try {
            $response = Http::get("{$this->pythonApiUrl}/documents?search={$query}");

            if ($response->successful()) {
                return response()->json($response->json());
            } else {
                throw new \Exception('Search failed');
            }

        } catch (\Exception $e) {
            Log::error('Document search error: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Search failed'
            ], 500);
        }
    }
}
