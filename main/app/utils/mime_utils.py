MIME_TYPES = {
    "pdf": ("application/pdf", True),
    "jpg": ("image/jpeg", True),
    "jpeg": ("image/jpeg", True),
    "png": ("image/png", True),
    "gif": ("image/gif", True),
    "txt": ("text/plain", True),
    "csv": ("text/csv", True),
    "md": ("text/markdown", True),
    "html": ("text/html", True),
    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # noqa
        False,
    ),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        False,
    ),
    "pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # noqa
        False,
    ),
}


def get_file_info(filename: str):
    ext = filename.split(".")[-1].lower()
    mime_type, viewable = MIME_TYPES.get(
        ext, ("application/octet-stream", False)
    )
    return {
        "file_extension": ext,
        "mime_type": mime_type,
        "is_viewable_in_browser": viewable,
    }
