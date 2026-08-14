"""Avatar file upload and storage for Цифровое Сукно."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.config import settings
from app.models.sukno_user import SuknoUser
from app.schemas.auth import UserProfile
from app.services.auth_service import user_to_profile

UPLOAD_PATH_PREFIX = "/api/v1/billiards/uploads/avatars/"
ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})


def get_avatars_dir() -> Path:
    path = Path(settings.uploads_dir) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_managed_avatar_url(avatar_url: str) -> bool:
    if not avatar_url:
        return False
    return UPLOAD_PATH_PREFIX in avatar_url


def avatar_filename_from_url(avatar_url: str) -> str | None:
    if not is_managed_avatar_url(avatar_url):
        return None
    filename = avatar_url.rsplit("/avatars/", 1)[-1].split("?")[0]
    safe = Path(filename).name
    if not safe or safe != filename or ".." in filename:
        return None
    return safe


def delete_avatar_file(avatar_url: str) -> None:
    filename = avatar_filename_from_url(avatar_url)
    if not filename:
        return
    path = get_avatars_dir() / filename
    if path.is_file():
        path.unlink()


def detect_image_ext(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return ".gif"
    if len(content) > 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_avatar_upload(session: Session, user: SuknoUser, file: UploadFile) -> UserProfile:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не выбран.",
        )

    content = await file.read()
    if len(content) > settings.avatar_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой (макс. 2 МБ).",
        )
    if len(content) < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл пустой или повреждён.",
        )

    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допустимы JPEG, PNG, WebP и GIF.",
        )

    ext = detect_image_ext(content)
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый формат изображения.",
        )

    delete_avatar_file(user.avatar_url)

    filename = f"{user.id}_{uuid.uuid4().hex}{ext}"
    dest = get_avatars_dir() / filename
    dest.write_bytes(content)

    user.avatar_url = f"{UPLOAD_PATH_PREFIX}{filename}"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user_to_profile(user)


def remove_user_avatar(session: Session, user: SuknoUser) -> UserProfile:
    delete_avatar_file(user.avatar_url)
    user.avatar_url = ""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user_to_profile(user)
