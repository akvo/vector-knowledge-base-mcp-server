import os
import time
import argparse
from utils.api_util import (
    create_knowledge_base,
    upload_documents,
    process_documents,
    create_api_key,
)

# Constants
KNOWLEDGE_BASE_DIR = "./downloads/living_income"
KB_TITLE = "Living Income"
KB_DESCRIPTION = "Living Income Knowledge Base documents"
DEFAULT_CHUNK_SIZE = 10


def get_pdf_files(directory: str):
    """List all PDF files in the given directory."""
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        return []

    pdfs = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".pdf")
    ]
    print(f"🔍 Found {len(pdfs)} PDF documents in {directory}")
    return pdfs


def chunk_files(file_list, chunk_size):
    """Yield successive n-sized chunks from file_list."""
    for i in range(0, len(file_list), chunk_size):
        yield file_list[i : i + chunk_size]


def main():
    parser = argparse.ArgumentParser(
        description="Living Income Knowledge Base Import Script"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List files without uploading"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Number of files per upload chunk",
    )
    args = parser.parse_args()

    print(f"=== {KB_TITLE} Knowledge Import Script ===")

    # 1. Discover local PDFs
    pdf_files = get_pdf_files(KNOWLEDGE_BASE_DIR)
    if not pdf_files:
        return

    if args.dry_run:
        print("🧪 Dry run mode: documents detected but not uploaded.")
        for f in pdf_files:
            print(f" - {os.path.basename(f)}")
        return

    # 2. Authenticate
    print("🔐 Authenticating with RAG backend...")
    access_token = create_api_key()
    if not access_token:
        print("❌ Auth failed. Check your ADMIN_API_KEY and RAG_MAIN_URL.")
        return
    print("✅ Authenticated successfully.")

    # 3. Create Knowledge Base
    print(f"📁 Creating Knowledge Base: {KB_TITLE}...")
    kb_id = create_knowledge_base(
        token=access_token, title=KB_TITLE, description=KB_DESCRIPTION
    )
    if not kb_id:
        print("❌ Failed to create knowledge base.")
        return
    print(f"✅ Knowledge Base created with ID: {kb_id}")

    # 4. Upload and Process in chunks
    total_chunks = (len(pdf_files) + args.chunk_size - 1) // args.chunk_size

    for idx, file_chunk in enumerate(
        chunk_files(pdf_files, args.chunk_size), 1
    ):
        print(
            f"\n📦 Uploading chunk {idx}/{total_chunks} "
            f"({len(file_chunk)} documents)..."
        )
        upload_results = upload_documents(access_token, kb_id, file_chunk)

        if upload_results:
            print(f"⚙️ Triggering processing for chunk {idx}...")
            # Wait a bit before processing to ensure backend handles the upload
            time.sleep(2)
            process_results = process_documents(
                access_token, kb_id, upload_results
            )
            if process_results:
                print(f"✅ Chunk {idx} processing started.")
            else:
                print(f"⚠️ Failed to trigger processing for chunk {idx}.")
        else:
            print(f"❌ Failed to upload chunk {idx}.")

        # Throttling between chunks
        if idx < total_chunks:
            print("⏳ Waiting before next chunk...")
            time.sleep(3)

    print("\n✅ Living Income Knowledge Base import process completed.")


if __name__ == "__main__":
    main()
