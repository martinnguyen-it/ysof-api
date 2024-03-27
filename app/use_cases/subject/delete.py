from typing import Optional

from fastapi import Depends
from app.infra.subject.subject_repository import SubjectRepository
from app.shared import request_object, response_object, use_case
from app.models.subject import SubjectModel


class DeleteSubjectRequestObject(request_object.ValidRequestObject):
    def __init__(self, id: str):
        self.id = id

    @classmethod
    def builder(cls, id: str) -> request_object.RequestObject:
        invalid_req = request_object.InvalidRequestObject()
        if id is None:
            invalid_req.add_error("id", "Invalid client id")

        if invalid_req.has_errors():
            return invalid_req

        return DeleteSubjectRequestObject(id=id)


class DeleteSubjectUseCase(use_case.UseCase):
    def __init__(self,
                 subject_repository: SubjectRepository = Depends(
                     SubjectRepository)):
        self.subject_repository = subject_repository

    def process_request(self, req_object: DeleteSubjectRequestObject):
        subject: Optional[SubjectModel] = self.subject_repository.get_by_id(
            req_object.id)
        if not subject:
            return response_object.ResponseFailure.build_not_found_error("Môn học không tồn tại")

        try:
            self.subject_repository.delete(id=subject.id)
            return {"success": True}
        except Exception:
            return response_object.ResponseFailure.build_system_error("Something went error.")
