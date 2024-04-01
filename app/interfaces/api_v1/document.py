from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException, UploadFile, File
from typing import Annotated, Optional

from app.domain.document.entity import Document, DocumentInCreate, ManyDocumentsInResponse, \
    DocumentInUpdate, DocumentInCreatePayload
from app.domain.shared.enum import Sort
from app.infra.security.security_service import (authorization, get_current_active_admin,
                                                 get_current_admin)
from app.infra.services.google_drive_api import GoogleDriveApiService
from app.shared.decorator import response_decorator
from app.use_cases.document.list import ListDocumentsUseCase, ListDocumentsRequestObject
from app.use_cases.document.update import UpdateDocumentUseCase, UpdateDocumentRequestObject
from app.use_cases.document.get import (
    GetDocumentRequestObject,
    GetDocumentCase,
)
from app.use_cases.document.create import (
    CreateDocumentRequestObject,
    CreateDocumentUseCase,
)
from app.models.admin import AdminModel
from app.shared.constant import SUPER_ADMIN
from app.use_cases.document.delete import DeleteDocumentRequestObject, DeleteDocumentUseCase
from app.domain.document.enum import DocumentType

router = APIRouter()


@router.get(
    "/{document_id}",
    dependencies=[Depends(get_current_admin)],
    response_model=Document,
)
@response_decorator()
def get_document_by_id(
        document_id: str = Path(..., title="Document id"),
        get_document_use_case: GetDocumentCase = Depends(GetDocumentCase),
):
    get_document_request_object = GetDocumentRequestObject.builder(
        document_id=document_id)
    response = get_document_use_case.execute(
        request_object=get_document_request_object)
    return response


@router.post(
    "",
    response_model=Document,
)
@response_decorator()
def create_document(
        payload: DocumentInCreatePayload = Body(...,
                                                title="Document In Create payload"),
        file: UploadFile = File(...),
        create_document_use_case: CreateDocumentUseCase = Depends(
            CreateDocumentUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
        google_drive_service: GoogleDriveApiService = Depends(
            GoogleDriveApiService)
):
    if payload.role not in current_admin.roles:
        authorization(current_admin, SUPER_ADMIN)

    info_file = google_drive_service.create(file=file, name=payload.name)
    new_payload = DocumentInCreate(
        **payload.model_dump(),
        **info_file.model_dump(exclude={"name", "id"}),
        file_id=info_file.id,
        author=current_admin)
    req_object = CreateDocumentRequestObject.builder(payload=new_payload)
    response = create_document_use_case.execute(request_object=req_object)
    return response


@router.get(
    "",
    response_model=ManyDocumentsInResponse,
)
@response_decorator()
def get_list_documents(
        list_documents_use_case: ListDocumentsUseCase = Depends(
            ListDocumentsUseCase),
        page_index: Annotated[int, Query(title="Page Index")] = 1,
        page_size: Annotated[int, Query(title="Page size")] = 100,
        search: Optional[str] = Query(None, title="Search"),
        label: Optional[list[str]] = Query(None, title="Labels"),
        roles: Optional[list[str]] = Query(None, title="Roles"),
        sort: Optional[Sort] = Sort.DESC,
        sort_by: Optional[str] = 'id',
        season: Optional[int] = None,
        type: Optional[DocumentType] = None,
        current_admin: AdminModel = Depends(get_current_admin)
):
    annotations = {}
    for base in reversed(Document.__mro__):
        annotations.update(getattr(base, '__annotations__', {}))
    if sort_by not in annotations:
        raise HTTPException(
            status_code=400, detail=f"Invalid sort_by: {sort_by}")
    sort_query = {sort_by: 1 if sort is sort.ASCE else -1}

    req_object = ListDocumentsRequestObject.builder(current_admin=current_admin,
                                                    page_index=page_index,
                                                    page_size=page_size,
                                                    search=search,
                                                    label=label,
                                                    roles=roles,
                                                    season=season,
                                                    type=type,
                                                    sort=sort_query)
    response = list_documents_use_case.execute(request_object=req_object)
    return response


@router.put(
    "/{id}",
    response_model=Document,
)
@response_decorator()
def update_document(
        id: str = Path(..., title="Document Id"),
        payload: DocumentInUpdate = Body(...,
                                         title="Document updated payload"),
        update_document_use_case: UpdateDocumentUseCase = Depends(
            UpdateDocumentUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    if payload.role and payload.role not in current_admin.roles:
        authorization(current_admin, SUPER_ADMIN)

    req_object = UpdateDocumentRequestObject.builder(
        id=id, payload=payload, admin_roles=current_admin.roles)
    response = update_document_use_case.execute(request_object=req_object)
    return response


@router.delete("/{id}")
@response_decorator()
def delete_document(
        id: str = Path(..., title="Document Id"),
        delete_document_use_case: DeleteDocumentUseCase = Depends(
            DeleteDocumentUseCase),
        current_admin: AdminModel = Depends(get_current_active_admin),
):
    req_object = DeleteDocumentRequestObject.builder(
        id=id, admin_roles=current_admin.roles)
    response = delete_document_use_case.execute(request_object=req_object)
    return response
