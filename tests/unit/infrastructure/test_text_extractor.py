import pytest

from app.infrastructure.text_extraction.extractor import TextExtractor


@pytest.mark.asyncio
class TestTextExtractor:
    async def test_extract_txt(self) -> None:
        content = b"Hello, this is a text file content."
        result = await TextExtractor.extract(content, "txt")
        assert result == "Hello, this is a text file content."

    async def test_extract_txt_with_encoding_issues(self) -> None:
        content = b"Hello \xff world"
        result = await TextExtractor.extract(content, "txt")
        assert "Hello" in result
        assert "world" in result

    async def test_unsupported_file_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            await TextExtractor.extract(b"content", "docx")
