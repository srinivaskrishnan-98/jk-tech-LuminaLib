import asyncio
import io

import structlog

logger = structlog.get_logger()


class TextExtractor:
    """Extracts text content from uploaded book files (PDF and TXT)."""

    @staticmethod
    async def extract(file_content: bytes, file_type: str) -> str:
        """Extract text from file content based on file type.

        Args:
            file_content: Raw bytes of the uploaded file.
            file_type: File extension (pdf, txt).

        Returns:
            Extracted text content as a string.
        """
        if file_type == "pdf":
            return await TextExtractor._extract_pdf(file_content)
        elif file_type == "txt":
            return file_content.decode("utf-8", errors="replace")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    async def _extract_pdf(content: bytes) -> str:
        """Extract text from PDF bytes using pdfplumber in a thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, TextExtractor._sync_extract_pdf, content)

    @staticmethod
    def _sync_extract_pdf(content: bytes) -> str:
        """Synchronous PDF text extraction using pdfplumber."""
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts)
        logger.info("pdf_text_extracted", pages=len(text_parts), chars=len(full_text))
        return full_text
