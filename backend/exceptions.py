class DatabaseError(Exception):
    """
    Custom exception for database-related errors.

    This exception helps distinguish database errors from other types of errors
    in the application, making error handling and debugging more specific.

    Attributes:
        message: A human-readable explanation of what went wrong
        original_error: The underlying exception that caused this error (optional)
    """
    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)