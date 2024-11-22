from fastapi import HTTPException, status


forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Bạn không có quyền",
)


class CustomException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
