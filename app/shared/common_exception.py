from fastapi import HTTPException, status


forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Bạn không có quyền",
)
