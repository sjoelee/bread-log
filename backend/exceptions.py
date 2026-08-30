from typing import Optional


class DatabaseError(Exception):
  """
  Custom exception for database-related errors.

  This exception helps distinguish database errors from other types of errors
  in the application, making error handling and debugging more specific.

  Attributes:
      message: A human-readable explanation of what went wrong
      original_error: The underlying exception that caused this error (optional)
  """

  def __init__(self, message: str, original_error: Optional[Exception] = None):
    self.message = message
    self.original_error = original_error
    super().__init__(self.message)


class NotFoundError(Exception):
  """Raised when a requested resource does not exist.

  Not wired to an HTTP status yet — the exception handler that maps this to
  404 arrives in Stage 6.
  """


class ConflictError(Exception):
  """Raised when an operation conflicts with current state.

  Example: deleting a recipe that another recipe imports. Maps to HTTP 409
  once the Stage 6 exception handler is in place.
  """


class DomainError(Exception):
  """Raised when a domain invariant is violated.

  Base class for the composition-feature errors (SubRecipeNotReady,
  CircularDependency, …) added in Part II.
  """
