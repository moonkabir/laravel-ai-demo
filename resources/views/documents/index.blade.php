{{-- resources/views/documents/index.blade.php --}}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>Document Management</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body class="bg-gray-50">
    <div class="max-w-6xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-2xl font-bold text-gray-800">
                    <i class="fas fa-folder-open text-blue-500"></i> Document Management
                </h1>
                <p class="text-sm text-gray-500">Upload and manage your company documents</p>
            </div>
            <div class="flex space-x-3">
                <a href="{{ route('chat.index') }}"
                   class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition">
                    <i class="fas fa-comment"></i> Chat with AI
                </a>
            </div>
        </div>

        <!-- Upload Form -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h2 class="text-lg font-semibold mb-4">Upload Document</h2>
            <form id="uploadForm" class="space-y-4">
                @csrf
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Document Title</label>
                    <input type="text" name="title" id="docTitle" required
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                           placeholder="Enter document title">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Select File</label>
                    <input type="file" name="file" id="docFile"
                           accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.docx,.txt" required
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg file:mr-4 file:py-2 file:px-4 file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                    <p class="text-xs text-gray-500 mt-1">Supported: PDF, Images (JPG, PNG, GIF, BMP), DOCX, TXT (Max 20MB)</p>
                </div>
                <button type="submit" id="uploadBtn"
                        class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50">
                    <i class="fas fa-upload"></i> Upload & Process
                </button>
            </form>
            <div id="uploadStatus" class="mt-4 hidden"></div>
        </div>

        <!-- Document List -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-semibold">Uploaded Documents</h2>
                <span class="text-sm text-gray-500">{{ count($documents) }} documents</span>
            </div>
            <div id="documentList" class="space-y-3">
                @forelse($documents as $doc)
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 rounded-lg flex items-center justify-center
                                {{ $doc['file_type'] == 'pdf' ? 'bg-red-100' : ($doc['file_type'] == 'docx' ? 'bg-blue-100' : 'bg-green-100') }}">
                                <i class="fas
                                    {{ $doc['file_type'] == 'pdf' ? 'fa-file-pdf text-red-500' :
                                       ($doc['file_type'] == 'docx' ? 'fa-file-word text-blue-500' : 'fa-file-image text-green-500') }}">
                                </i>
                            </div>
                            <div>
                                <p class="font-medium text-gray-800">{{ $doc['title'] }}</p>
                                <p class="text-xs text-gray-500">{{ $doc['filename'] }} • {{ \Carbon\Carbon::parse($doc['created_at'])->diffForHumans() }}</p>
                            </div>
                        </div>
                        <button onclick="deleteDocument({{ $doc['id'] }})"
                                class="text-gray-400 hover:text-red-500 transition">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                @empty
                    <div class="text-center text-gray-400 py-8">
                        <i class="fas fa-file-circle-plus text-3xl block mb-2"></i>
                        <p>No documents uploaded yet</p>
                        <p class="text-xs mt-1">Upload your first document above</p>
                    </div>
                @endforelse
            </div>
        </div>
    </div>

    <script>
        // Upload form
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const status = document.getElementById('uploadStatus');
            const btn = document.getElementById('uploadBtn');

            status.className = 'mt-4 p-3 rounded-lg bg-blue-50 text-blue-700';
            status.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing document...';
            status.classList.remove('hidden');
            btn.disabled = true;

            try {
                const response = await fetch('{{ route("documents.upload") }}', {
                    method: 'POST',
                    headers: {
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    status.className = 'mt-4 p-3 rounded-lg bg-green-50 text-green-700';
                    status.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                    setTimeout(() => location.reload(), 1500);
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                status.className = 'mt-4 p-3 rounded-lg bg-red-50 text-red-700';
                status.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + error.message;
            } finally {
                btn.disabled = false;
            }
        });

        // Delete document
        async function deleteDocument(id) {
            if (!confirm('Delete this document?')) return;

            try {
                const response = await fetch(`/documents/${id}`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    }
                });

                const data = await response.json();
                if (data.success) {
                    location.reload();
                }
            } catch (error) {
                alert('Error deleting document');
            }
        }
    </script>
</body>
</html>

