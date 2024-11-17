from app.shared import response_object
from fastapi import APIRouter, Body, Depends, Query, HTTPException, Path
from typing import Optional

from app.domain.subject.entity import (
    Subject,
    SubjectInCreate,
    SubjectInUpdate,
    SubjectShortResponse,
)
from app.domain.shared.enum import AdminRole, Sort
from app.infra.security.security_service import (
    authorization,
    get_current_active_admin,
    get_current_admin,
)
from app.shared.decorator import response_decorator
from app.use_cases.subject.list import ListSubjectsUseCase, ListSubjectsRequestObject
from app.use_cases.subject.update import UpdateSubjectUseCase, UpdateSubjectRequestObject
from app.use_cases.subject.get import (
    GetSubjectRequestObject,
    GetSubjectCase,
)
from app.use_cases.subject.create import (
    CreateSubjectRequestObject,
    CreateSubjectUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.subject.delete import DeleteSubjectRequestObject, DeleteSubjectUseCase
from app.domain.subject.enum import StatusSubjectEnum
from app.use_cases.subject.get_next_most_recent import GetSubjectNextMostRecentUseCase
from app.use_cases.subject.get_last_sent_evaluation import GetSubjectLastSentEvaluationUseCase
from app.use_cases.subject.get_last_sent_notification import GetSubjectLastSentNotificationUseCase
from app.use_cases.subject.send_notification import (
    SubjectSendNotificationRequestObject,
    SubjectSendNotificationUseCase,
)
from app.use_cases.subject.send_evaluation import (
    SubjectSendEvaluationRequestObject,
    SubjectSendEvaluationUseCase,
)
from app.use_cases.subject.list_short import (
    ListSubjectsShortRequestObject,
    ListSubjectsShortUseCase,
)

router = APIRouter()


@router.get(
    "/next-most-recent",
    dependencies=[Depends(get_current_active_admin)],
    response_model=Subject,
)
@response_decorator()
def get_subject_next_most_recent(
    get_subject_next_most_recent_use_case: GetSubjectNextMostRecentUseCase = Depends(
        GetSubjectNextMostRecentUseCase
    ),
):
    response = get_subject_next_most_recent_use_case.process_request()
    return response


@router.get(
    "/last-sent-student",
    dependencies=[Depends(get_current_active_admin)],
    response_model=Subject,
)
@response_decorator()
def get_subject_last_sent_notification(
    get_subject_last_sent_notification_use_case: GetSubjectLastSentNotificationUseCase = Depends(
        GetSubjectLastSentNotificationUseCase
    ),
):
    response = get_subject_last_sent_notification_use_case.process_request()
    return response


@router.get(
    "/last-sent-evaluation",
    dependencies=[Depends(get_current_active_admin)],
    response_model=Subject,
)
@response_decorator()
def get_subject_last_sent_evaluation(
    get_subject_last_sent_evaluation_use_case: GetSubjectLastSentEvaluationUseCase = Depends(
        GetSubjectLastSentEvaluationUseCase
    ),
):
    response = get_subject_last_sent_evaluation_use_case.process_request()
    return response


@router.post(
    "/send-notification/{subject_id}",
    response_model=Subject,
)
@response_decorator()
def send_subject_notification(
    subject_id: str = Path(..., title="Subject id"),
    current_admin: AdminModel = Depends(get_current_active_admin),
    subject_send_notification_use_case: SubjectSendNotificationUseCase = Depends(
        SubjectSendNotificationUseCase
    ),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    subject_send_notification_request_object = SubjectSendNotificationRequestObject.builder(
        subject_id=subject_id, current_admin=current_admin
    )
    response = subject_send_notification_use_case.execute(
        request_object=subject_send_notification_request_object
    )
    return response


@router.post(
    "/send-evaluation/{subject_id}",
    response_model=Subject,
)
@response_decorator()
def get_subject_evaluation(
    subject_id: str = Path(..., title="Subject id"),
    current_admin: AdminModel = Depends(get_current_active_admin),
    subject_send_evaluation_use_case: SubjectSendEvaluationUseCase = Depends(
        SubjectSendEvaluationUseCase
    ),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    subject_send_evaluation_request_object = SubjectSendEvaluationRequestObject.builder(
        subject_id=subject_id, current_admin=current_admin
    )
    response = subject_send_evaluation_use_case.execute(
        request_object=subject_send_evaluation_request_object
    )
    return response


@router.get("/list-short", response_model=list[SubjectShortResponse])
@response_decorator()
def get_list_subjects_short(
    list_subjects_short_use_case: ListSubjectsShortUseCase = Depends(ListSubjectsShortUseCase),
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.ASCE,
    sort_by: Optional[str] = "start_at",
    subdivision: Optional[str] = None,
    status: Optional[list[StatusSubjectEnum]] = Query(None, title="Status"),
    season: Optional[int] = None,
    current_admin: AdminModel = Depends(get_current_admin),
):
    annotations = {}
    for base in reversed(Subject.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListSubjectsShortRequestObject.builder(
        search=search,
        season=season,
        sort=sort_query,
        subdivision=subdivision,
        current_admin=current_admin,
        status=status,
    )
    response = list_subjects_short_use_case.execute(request_object=req_object)
    return response


@router.get(
    "/{subject_id}",
    dependencies=[Depends(get_current_admin)],
    response_model=Subject,
)
@response_decorator()
def get_subject_by_id(
    subject_id: str = Path(..., title="Subject id"),
    get_subject_use_case: GetSubjectCase = Depends(GetSubjectCase),
):
    get_subject_request_object = GetSubjectRequestObject.builder(subject_id=subject_id)
    response = get_subject_use_case.execute(request_object=get_subject_request_object)
    return response


@router.post(
    "",
    response_model=Subject,
)
@response_decorator()
def create_subject(
    payload: SubjectInCreate = Body(..., title="Subject In Create payload"),
    create_subject_use_case: CreateSubjectUseCase = Depends(CreateSubjectUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = CreateSubjectRequestObject.builder(payload=payload, current_admin=current_admin)
    response = create_subject_use_case.execute(request_object=req_object)
    return response


@router.get("", response_model=list[Subject])
@response_decorator()
def get_list_subjects(
    list_subjects_use_case: ListSubjectsUseCase = Depends(ListSubjectsUseCase),
    search: Optional[str] = Query(None, title="Search"),
    sort: Optional[Sort] = Sort.ASCE,
    sort_by: Optional[str] = "start_at",
    subdivision: Optional[str] = None,
    status: Optional[list[StatusSubjectEnum]] = Query(None, title="Status"),
    season: Optional[int] = None,
    current_admin: AdminModel = Depends(get_current_admin),
):
    annotations = {}
    for base in reversed(Subject.__mro__):
        annotations.update(getattr(base, "__annotations__", {}))
    if sort_by not in annotations:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListSubjectsRequestObject.builder(
        search=search,
        season=season,
        sort=sort_query,
        subdivision=subdivision,
        current_admin=current_admin,
        status=status,
    )
    response = list_subjects_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Subject,
)
@response_decorator()
def update_subject(
    id: str = Path(..., title="Subject Id"),
    payload: SubjectInUpdate = Body(..., title="Subject updated payload"),
    update_subject_use_case: UpdateSubjectUseCase = Depends(UpdateSubjectUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV, AdminRole.BKT])
    if AdminRole.BKT in current_admin.roles and AdminRole.BHV not in current_admin.roles:
        if payload.zoom is None:
            return response_object.ResponseFailure.build_parameters_error(
                message="Vui lòng điền thông tin zoom"
            )
        payload = SubjectInUpdate(zoom=payload.zoom)
    req_object = UpdateSubjectRequestObject.builder(
        id=id, payload=payload, current_admin=current_admin
    )
    response = update_subject_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_subject(
    id: str = Path(..., title="Subject Id"),
    delete_subject_use_case: DeleteSubjectUseCase = Depends(DeleteSubjectUseCase),
    current_admin: AdminModel = Depends(get_current_active_admin),
):
    authorization(current_admin, [*SUPER_ADMIN, AdminRole.BHV])
    req_object = DeleteSubjectRequestObject.builder(id=id, current_admin=current_admin)
    response = delete_subject_use_case.execute(request_object=req_object)
    return response
