async def extract_and_index_pdf(file_doc, user_id):
    loader = PyPDFLoader(file_doc["path"])
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(docs)

    add_chunks_to_chroma(
        chunks,
        doc_id=str(file_doc["_id"]),
        user_id=user_id,
    )

    await db.chunks.insert_one({
        "metadata_id": str(file_doc["_id"]),
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "chunk_count": len(chunks),
    })
