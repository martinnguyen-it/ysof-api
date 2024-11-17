from fastapi import Depends
from typing import Optional
from app.shared import request_object, response_object, use_case
from app.domain.lecturer.entity import Lecturer, LecturerInDB
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.models.lecturer import LecturerModel


class GetLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self, lecturer_id: str):
        self.lecturer_id = lecturer_id

    @classmethod
    def builder(cls, lecturer_id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if not id:
            invalid_req.add_error("id", "Invalid")

        if invalid_req.has_errors():
            return invalid_req

        return GetLecturerRequestObject(lecturer_id=lecturer_id)


class GetLecturerCase(use_case.UseCase):
    def __init__(self, lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.lecturer_repository = lecturer_repository

    def process_request(self, req_object: GetLecturerRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(
            lecturer_id=req_object.lecturer_id
        )
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error(
                message="Giảng viên không tồn tại"
            )

        return Lecturer(**LecturerInDB.model_validate(lecturer).model_dump())
