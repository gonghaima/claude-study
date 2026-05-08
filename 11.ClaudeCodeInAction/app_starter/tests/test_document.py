import os
import pytest
from tools.document import binary_document_to_markdown, document_path_to_markdown


class TestBinaryDocumentToMarkdown:
    # Define fixture paths
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_fixture_files_exist(self):
        """Verify test fixtures exist."""
        assert os.path.exists(self.DOCX_FIXTURE), (
            f"DOCX fixture not found at {self.DOCX_FIXTURE}"
        )
        assert os.path.exists(self.PDF_FIXTURE), (
            f"PDF fixture not found at {self.PDF_FIXTURE}"
        )

    def test_binary_document_to_markdown_with_docx(self):
        """Test converting a DOCX document to markdown."""
        # Read binary content from the fixture
        with open(self.DOCX_FIXTURE, "rb") as f:
            docx_data = f.read()

        # Call function
        result = binary_document_to_markdown(docx_data, "docx")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result

    def test_binary_document_to_markdown_with_pdf(self):
        """Test converting a PDF document to markdown."""
        # Read binary content from the fixture
        with open(self.PDF_FIXTURE, "rb") as f:
            pdf_data = f.read()

        # Call function
        result = binary_document_to_markdown(pdf_data, "pdf")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result


class TestDocumentPathToMarkdown:
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    # --- Happy path ---

    def test_converts_docx(self):
        """Valid .docx path returns a non-empty markdown string."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_converts_pdf(self):
        """Valid .pdf path returns a non-empty markdown string."""
        result = document_path_to_markdown(self.PDF_FIXTURE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_content_accuracy(self):
        """Known content from the fixture appears in the output."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)
        assert "MCP" in result

    # --- File extension handling ---

    def test_uppercase_docx_extension(self):
        """Uppercase .DOCX extension is handled correctly."""
        import shutil, tempfile
        with tempfile.NamedTemporaryFile(suffix=".DOCX", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            shutil.copy(self.DOCX_FIXTURE, tmp_path)
            result = document_path_to_markdown(tmp_path)
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    def test_uppercase_pdf_extension(self):
        """Uppercase .PDF extension is handled correctly."""
        import shutil, tempfile
        with tempfile.NamedTemporaryFile(suffix=".PDF", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            shutil.copy(self.PDF_FIXTURE, tmp_path)
            result = document_path_to_markdown(tmp_path)
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    def test_unsupported_extension_raises(self, tmp_path):
        """Unsupported file extension raises ValueError."""
        fake_file = tmp_path / "document.txt"
        fake_file.write_bytes(b"hello")
        with pytest.raises(ValueError):
            document_path_to_markdown(str(fake_file))

    def test_no_extension_raises(self, tmp_path):
        """File with no extension raises ValueError."""
        fake_file = tmp_path / "document"
        fake_file.write_bytes(b"hello")
        with pytest.raises(ValueError):
            document_path_to_markdown(str(fake_file))

    # --- File path edge cases ---

    def test_nonexistent_file_raises(self):
        """Non-existent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            document_path_to_markdown("/nonexistent/path/file.pdf")

    def test_directory_path_raises(self, tmp_path):
        """Passing a directory path raises an error."""
        with pytest.raises((IsADirectoryError, ValueError)):
            document_path_to_markdown(str(tmp_path))

    def test_empty_file_raises(self, tmp_path):
        """Empty file raises an error."""
        empty_file = tmp_path / "empty.docx"
        empty_file.write_bytes(b"")
        with pytest.raises(Exception):
            document_path_to_markdown(str(empty_file))

    def test_empty_string_path_raises(self):
        """Empty string path raises an error."""
        with pytest.raises((FileNotFoundError, ValueError)):
            document_path_to_markdown("")
