from pydantic import BaseModel, Field


class TextSnippet(BaseModel):
    """Represents a snippet of text extracted via OCR."""
    text: str = Field(..., description="The raw extracted text.")
    confidence: float | None = Field(default=None,
                                     description="Confidence score from the OCR engine.")


class Document(BaseModel):
    """Represents an entire document processed by the pipeline."""
    raw_text: str = Field(..., description="The complete raw text extracted from the image.")
    corrected_text: str = Field(..., description="The complete text after NLP correction.")
    detected_language: str = Field(
        ...,
        description="The detected or provided language code used.")
    snippets: list[TextSnippet] = Field(
        default_factory=list,
        description="Individual text snippets making up the document.")
