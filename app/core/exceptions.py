from uuid import UUID


class LuminaLibError(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ── Authentication ───────────────────────────────────────────

class UnauthorizedError(LuminaLibError):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, status_code=401)


class InvalidCredentialsError(LuminaLibError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password", status_code=401)


class UserAlreadyExistsError(LuminaLibError):
    def __init__(self, field: str) -> None:
        super().__init__(f"User with this {field} already exists", status_code=409)


class TokenRevokedError(LuminaLibError):
    def __init__(self) -> None:
        super().__init__("Token has been revoked", status_code=401)


# ── Books ────────────────────────────────────────────────────

class BookNotFoundError(LuminaLibError):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book {book_id} not found", status_code=404)


class BookNotAvailableError(LuminaLibError):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(
            f"Book {book_id} has no available copies", status_code=409
        )


class UnsupportedFileTypeError(LuminaLibError):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            f"Unsupported file type: {file_type}. Allowed: pdf, txt",
            status_code=400,
        )


# ── Borrows ──────────────────────────────────────────────────

class AlreadyBorrowedError(LuminaLibError):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(
            f"You already have an active borrow for book {book_id}",
            status_code=409,
        )


class NoBorrowFoundError(LuminaLibError):
    def __init__(self, book_id: UUID) -> None:
        super().__init__(
            f"No active borrow found for book {book_id}", status_code=404
        )


# ── Reviews ──────────────────────────────────────────────────

class MustBorrowBeforeReviewError(LuminaLibError):
    def __init__(self) -> None:
        super().__init__(
            "You must borrow this book before reviewing it", status_code=403
        )


class AlreadyReviewedError(LuminaLibError):
    def __init__(self) -> None:
        super().__init__(
            "You have already reviewed this book", status_code=409
        )
