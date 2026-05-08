import os
from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pydantic import Field

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    path: str = Field(description="Absolute or relative path to a .docx or .pdf file"),
) -> str:
    """Convert a PDF or DOCX file at the given path to markdown.

    Reads the file from disk and converts its content to markdown-formatted text.

    When to use:
    - When you have a local file path and want its content as markdown
    - Supports .docx and .pdf files (case-insensitive extension)

    Examples:
    >>> document_path_to_markdown("/docs/report.pdf")
    "# Report\\n\\nContent here..."
    >>> document_path_to_markdown("/docs/spec.docx")
    "# Spec\\n\\nContent here..."
    """
    if not path:
        raise ValueError("Path must not be empty")

    if not os.path.exists(path):
        raise FileNotFoundError(f"No such file: '{path}'")

    if os.path.isdir(path):
        raise ValueError(f"Path is a directory, not a file: '{path}'")

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
        )

    with open(path, "rb") as f:
        binary_data = f.read()

    return binary_document_to_markdown(binary_data, ext.lstrip("."))
