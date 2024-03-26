from typing import Optional

from fastapi import Depends
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.shared import request_object, response_object, use_case
from app.models.lecturer import LecturerModel


class DeleteLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str):
        self.id = id

    @classmethod
    def builder(cls, id: str,) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteLecturerRequestObject(id=id)


class DeleteLecturerUseCase(use_case.UseCase):
    def __init__(self,
                 lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.lecturer_repository = lecturer_repository

    def process_request(self, req_object: DeleteLecturerRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(
            req_object.id)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")
        try:
            self.lecturer_repository.delete(id=lecturer.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
