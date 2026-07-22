# test_qdrant.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_engine import RAGEngine
from models import init_db, SessionLocal, Document

def test_qdrant():
    """Test Qdrant integration"""
    init_db()
    db = SessionLocal()
    rag = RAGEngine()

    print("\n" + "="*60)
    print("🔍 TESTING QDRANT VECTOR SEARCH")
    print("="*60)

    # Test queries
    test_queries = [
        "What is the technical stack?",
        "Tell me about employee benefits",
        "Company leave policy",
        "What are the salary ranges?",
        "Describe the project methodology",
        "Who is the CEO?",
        "What technologies do we use?"
    ]

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        results = rag.search(query, top_k=3)

        if results:
            print(f"   Found {len(results)} relevant chunks:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. Score: {result['score']:.3f}")
                print(f"      Content: {result['content'][:150]}...")
        else:
            print("   ❌ No results found")

    print("\n" + "="*60)

if __name__ == "__main__":
    test_qdrant()
