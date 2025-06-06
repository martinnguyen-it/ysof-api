from fastapi import Depends, HTTPException

from app.models.student import StudentModel
from app.shared import request_object, use_case
from app.infra.roll_call.roll_call_repository import RollCallRepository
from app.shared.utils.general import get_current_season_value


class GetStudentRollCallResultsRequestObject(request_object.ValidRequestObject):
    def __init__(
        self,
        current_student: StudentModel,
        season: int | None = None,
    ):
        self.current_student = current_student
        self.season = season

    @classmethod
    def builder(
        cls,
        current_student: StudentModel,
        season: int | None = None,
    ):
        return GetStudentRollCallResultsRequestObject(
            current_student=current_student,
            season=season,
        )


class GetStudentRollCallResultsUseCase(use_case.UseCase):
    def __init__(self, roll_call_repository: RollCallRepository = Depends(RollCallRepository)):
        self.roll_call_repository = roll_call_repository

    def process_request(self, req_object: GetStudentRollCallResultsRequestObject):
        current_season = get_current_season_value()
        season: int

        if req_object.season:
            if req_object.season in [
                info.season for info in req_object.current_student.seasons_info
            ]:
                season = req_object.season
            else:
                raise HTTPException(
                    status_code=403, detail=f"Bạn không đăng ký mùa {req_object.season}"
                )
        else:
            season = current_season

        return self.roll_call_repository.get_student_roll_call_results(
            student_id=req_object.current_student.id,
            season=season,
        )
