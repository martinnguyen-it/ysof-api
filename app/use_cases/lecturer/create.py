from typing import Optional
from fastapi import Depends

from app.models.lecturer import LecturerModel
from app.shared import request_object, use_case

from app.domain.lecturer.entity import Lecturer, LecturerInCreate, LecturerInDB
from app.infra.lecturer.lecturer_repository import LecturerRepository


class CreateLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self,
                 lecturer_in: LecturerInCreate) -> None:
        self.lecturer_in = lecturer_in

    @classmethod
    def builder(cls,
                payload: Optional[LecturerInCreate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return CreateLecturerRequestObject(lecturer_in=payload)


class CreateLecturerUseCase(use_case.UseCase):
    def __init__(self,
                 lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.lecturer_repository = lecturer_repository

    def process_request(self, req_object: CreateLecturerRequestObject):
        lecturer: LecturerModel = self.lecturer_repository.create(
            lecturer=LecturerInDB(
                **req_object.lecturer_in.model_dump(),
            ))

        return Lecturer(**LecturerInDB.model_validate(lecturer).model_dump())
