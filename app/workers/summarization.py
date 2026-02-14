from uuid import UUID

import structlog

from app.config import Settings
from app.core.database import async_session_factory
from app.infrastructure.llm.factory import create_llm_provider
from app.infrastructure.storage.factory import create_storage_backend
from app.infrastructure.text_extraction.extractor import TextExtractor
from app.repositories.book_repository import BookRepository

logger = structlog.get_logger()


async def summarize_book(book_id: UUID) -> None:
    """Background task: extract text from uploaded book and generate LLM summary.

    Pipeline: Download file → Extract text → LLM summarize → Update DB.
    Updates summary_status throughout to track progress.
    """
    settings = Settings()
    storage = create_storage_backend(settings)
    llm = create_llm_provider(settings)

    async with async_session_factory() as session:
        try:
            repo = BookRepository(session)
            book = await repo.get_by_id(book_id)
            if not book:
                logger.error("summarization_book_not_found", book_id=str(book_id))
                return

            # Mark as processing
            book.summary_status = "processing"
            await session.commit()

            logger.info("summarization_started", book_id=str(book_id), file_type=book.file_type)

            # Download file from storage
            file_content = await storage.download_file(book.file_path)

            # Extract text
            text = await TextExtractor.extract(file_content, book.file_type)
            if not text.strip():
                book.summary = "No readable text content found in the uploaded file."
                book.summary_status = "completed"
                await session.commit()
                return

            # Generate summary via LLM
            summary = await llm.generate_summary(text)

            book.summary = summary
            book.summary_status = "completed"
            await session.commit()

            logger.info("summarization_completed", book_id=str(book_id))

        except Exception:
            logger.exception("summarization_failed", book_id=str(book_id))
            # Update status to failed
            try:
                book = await repo.get_by_id(book_id)
                if book:
                    book.summary_status = "failed"
                    await session.commit()
            except Exception:
                logger.exception("summarization_status_update_failed", book_id=str(book_id))
