from flask import jsonify
from enum import Enum


class ErrorType(str, Enum):
    SYNTACTIC = "Syntactic Error"  #! 400
    SEMANTIC = "Semantic Error"  #! 422
    NOT_FOUND = "Not found"  #! 404
    METHOD_NOT_ALLOWED = "Method is not allowed"  #! 405
    UNAUTHORIZED = "Unauthorized access try"  #! 401
    FORBIDDEN = "Access Forbidden"  #! 403
    DB_ERROR = "DATABASE ERROR"  #! 500


class Error:

    def __init__(
        self,
        # error,
        type: ErrorType,
        message,
    ) -> None:
        # self.error = error
        self.type = type
        self.message = message

    def __repr__(self) -> str:
        return f"Error: , Title: {self.type},  Message: {self.message}"

    def serialize(self) -> iter:
        if not isinstance(self.type, ErrorType):
            raise TypeError(
                "First Parameter on TabuError must be from enum TabuErrorType."
            )

        data = {
            "title": self.type,
            "message": self.message,
        }
        return data