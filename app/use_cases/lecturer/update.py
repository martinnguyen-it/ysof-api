from typing import Optional
from fastapi import Depends
from app.models.lecturer import LecturerModel
from app.shared import request_object, use_case, response_object

from app.domain.lecturer.entity import (Lecturer, LecturerInDB, LecturerInUpdate,
                                        LecturerInUpdateTime)
from app.infra.lecturer.lecturer_repository import LecturerRepository
from app.infra.document.document_repository import DocumentRepository


class UpdateLecturerRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str,
                 obj_in: LecturerInUpdate) -> None:
        self.id = id
        self.obj_in = obj_in

    @classmethod
    def builder(cls, id: str,
                payload: Optional[LecturerInUpdate] = None
                ) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if payload is None:
            invalid_req.add_error("payload", "Invalid payload")

        if invalid_req.has_errors():
            return invalid_req

        return UpdateLecturerRequestObject(id=id, obj_in=payload)


class UpdateLecturerUseCase(use_case.UseCase):
    def __init__(self,
                 document_repository: DocumentRepository = Depends(
                     DocumentRepository),
                 lecturer_repository: LecturerRepository = Depends(LecturerRepository)):
        self.lecturer_repository = lecturer_repository
        self.document_repository = document_repository

    def process_request(self, req_object: UpdateLecturerRequestObject):
        lecturer: Optional[LecturerModel] = self.lecturer_repository.get_by_id(
            req_object.id)
        if not lecturer:
            return response_object.ResponseFailure.build_not_found_error("Giảng viên không tồn tại")

        self.lecturer_repository.update(id=lecturer.id, data=LecturerInUpdateTime(
            **req_object.obj_in.model_dump()))

        lecturer.reload()

        return Lecturer(**LecturerInDB.model_validate(lecturer).model_dump())
