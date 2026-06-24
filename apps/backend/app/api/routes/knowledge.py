from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.knowledge import (
    ErrorReasonTagPayload,
    ErrorReasonTagRead,
    KnowledgeBaseImportResponse,
    KnowledgePointAliasPayload,
    KnowledgePointAliasRead,
    KnowledgePointPayload,
    KnowledgePointRead,
    KnowledgeTreeResponse,
)
from app.services import knowledge_base as service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/tree", response_model=KnowledgeTreeResponse)
def list_knowledge_tree(
    subject_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> KnowledgeTreeResponse:
    return service.list_knowledge_tree(session, subject_id=subject_id)


@router.get("/points", response_model=list[KnowledgePointRead])
def list_knowledge_points(
    subject_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[KnowledgePointRead]:
    return service.list_knowledge_points(session, subject_id=subject_id)


@router.post("/points", response_model=KnowledgePointRead)
def create_knowledge_point(
    payload: KnowledgePointPayload,
    session: Session = Depends(get_db_session),
) -> KnowledgePointRead:
    return service.create_knowledge_point(session, payload)


@router.put("/points/{point_id}", response_model=KnowledgePointRead)
def update_knowledge_point(
    point_id: int,
    payload: KnowledgePointPayload,
    session: Session = Depends(get_db_session),
) -> KnowledgePointRead:
    return service.update_knowledge_point(session, point_id, payload)


@router.delete("/points/{point_id}")
def delete_knowledge_point(
    point_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_knowledge_point(session, point_id)


@router.get("/aliases", response_model=list[KnowledgePointAliasRead])
def list_aliases(
    subject_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[KnowledgePointAliasRead]:
    return service.list_aliases(session, subject_id=subject_id)


@router.post("/aliases", response_model=KnowledgePointAliasRead)
def create_alias(
    payload: KnowledgePointAliasPayload,
    session: Session = Depends(get_db_session),
) -> KnowledgePointAliasRead:
    return service.create_alias(session, payload)


@router.put("/aliases/{alias_id}", response_model=KnowledgePointAliasRead)
def update_alias(
    alias_id: int,
    payload: KnowledgePointAliasPayload,
    session: Session = Depends(get_db_session),
) -> KnowledgePointAliasRead:
    return service.update_alias(session, alias_id, payload)


@router.delete("/aliases/{alias_id}")
def delete_alias(
    alias_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_alias(session, alias_id)


@router.get("/error-tags", response_model=list[ErrorReasonTagRead])
def list_error_tags(session: Session = Depends(get_db_session)) -> list[ErrorReasonTagRead]:
    return service.list_error_tags(session)


@router.post("/error-tags", response_model=ErrorReasonTagRead)
def create_error_tag(
    payload: ErrorReasonTagPayload,
    session: Session = Depends(get_db_session),
) -> ErrorReasonTagRead:
    return service.create_error_tag(session, payload)


@router.put("/error-tags/{tag_id}", response_model=ErrorReasonTagRead)
def update_error_tag(
    tag_id: int,
    payload: ErrorReasonTagPayload,
    session: Session = Depends(get_db_session),
) -> ErrorReasonTagRead:
    return service.update_error_tag(session, tag_id, payload)


@router.delete("/error-tags/{tag_id}")
def delete_error_tag(
    tag_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_error_tag(session, tag_id)


@router.post("/import", response_model=KnowledgeBaseImportResponse)
async def import_knowledge_base(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
) -> KnowledgeBaseImportResponse:
    content = await file.read()
    return service.import_knowledge_base(session, content)
