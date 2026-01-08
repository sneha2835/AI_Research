from pydantic import BaseModel, Field

class AskPdfRequest(BaseModel):
    document_id: str
    query: str
    n_results: int = Field(5, ge=1, le=20)

class SummarizePdfRequest(BaseModel):
    document_id: str
