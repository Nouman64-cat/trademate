import os
from dotenv import load_dotenv
from pinecone import Pinecone

def clear_pinecone():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "trademate-documents")
    
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env file.")
        return

    print(f"Connecting to Pinecone index: {index_name}...")
    
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        
        # Confirm with user (optional, but good practice for irreversible actions)
        confirm = input(f"Are you sure you want to delete ALL vectors in '{index_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return

        print(f"Deleting all vectors from {index_name}...")
        index.delete(delete_all=True)
        print("✅ Successfully deleted all vectors.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_pinecone()
