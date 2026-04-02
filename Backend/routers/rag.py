from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from services.conversation_store import init_db, list_documents, upsert_document
from services.file_ingest import extract_text_from_upload
from services.prompt import generate_system_prompt
from services.rag_pipeline import rag_query
from services.store_faiss_vector import add_document, get_info

router = APIRouter()
init_db()


class IngestRequest(BaseModel):
    text: str = Field(..., description="Full document text to index.")
    source: str = Field("manual", description="Where this document came from.")
    doc_id: str = Field("doc_default", description="Unique identifier for this document.")


class IngestResponse(BaseModel):
    message: str
    chunks_created: int
    ids: list[int]


class UploadResponse(BaseModel):
    message: str
    doc_id: str
    filename: str
    file_type: str
    chunks_created: int
    ids: list[int]


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to answer using indexed documents.")
    system_prompt: Optional[str] = Field(None, description="Optional custom system prompt.")


class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[dict]
    sources: list[str]
    chunks_used: int
    hyde_answer: str


class GeneratePromptRequest(BaseModel):
    use_case: str = Field(..., description="Description of what the prompt should do.")


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    try:
        ids = add_document(
            text=request.text,
            metadata={"source": request.source, "doc_id": request.doc_id}
        )

        upsert_document(
            doc_id=request.doc_id,
            filename=request.source,
            source=request.source,
            file_type=Path(request.source).suffix.lower() or "text",
        )

        return IngestResponse(
            message=f"Successfully indexed {request.source}",
            chunks_created=len(ids),
            ids=ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        text, file_type = await extract_text_from_upload(file)

        if not text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in uploaded file.")

        filename = file.filename or "uploaded_file"
        doc_id = str(uuid4())

        ids = add_document(
            text=text,
            metadata={
                "source": filename,
                "doc_id": doc_id,
                "file_type": file_type,
            }
        )

        upsert_document(
            doc_id=doc_id,
            filename=filename,
            source=filename,
            file_type=file_type,
        )

        return UploadResponse(
            message=f"Successfully uploaded {filename}",
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            chunks_created=len(ids),
            ids=ids,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents")
async def documents():
    try:
        return {"documents": list_documents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document listing failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = rag_query(
            user_question=request.question,
            system_prompt=request.system_prompt
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/stats")
async def stats():
    try:
        return get_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


@router.post("/generate-prompt")
async def generate_prompt(request: GeneratePromptRequest):
    try:
        prompt = generate_system_prompt(request.use_case)
        return {"generated_prompt": prompt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt generation failed: {str(e)}")
