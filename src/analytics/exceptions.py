from fastapi import HTTPException, status


class EventNotFound(Exception):
    pass


class InvalidDate(Exception):
    pass


class DocumentNotFound(Exception):
    pass


class Unauthorized(Exception):
    pass


class PermissionDenied(Exception):
    pass


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionDeniedException(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class DocumentNotFoundException(HTTPException):
    def __init__(self, detail: str = "Document not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
