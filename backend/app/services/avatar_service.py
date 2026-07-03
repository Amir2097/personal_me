"""Avatar file upload and storage."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserProfile

UPLOAD_PATH_PREFIX = "/api/v1/uploads/avatars/"
ALLOWED_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)


def user_to_profile(user: User) -> UserProfile:
    """Собрать DTO профиля из модели пользователя."""
    return UserProfile(
        username=user.username,
        is_admin=user.is_admin,
        role=user.role,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        location=user.location,
        website=user.website,
        telegram=user.telegram,
        github=user.github,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def get_avatars_dir() -> Path:
    """Ensure avatar storage exists and return its path."""
    path = Path(settings.uploads_dir) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_managed_avatar_url(avatar_url: str) -> bool:
    """Return True when avatar_url points to a file we host."""
    if not avatar_url:
        return False
    return UPLOAD_PATH_PREFIX in avatar_url


def avatar_filename_from_url(avatar_url: str) -> str | None:
    """Extract stored filename from a managed avatar URL."""
    if not is_managed_avatar_url(avatar_url):
        return None
    filename = avatar_url.rsplit("/avatars/", 1)[-1].split("?")[0]
    safe = Path(filename).name
    if not safe or safe != filename or ".." in filename:
        return None
    return safe


def delete_avatar_file(avatar_url: str) -> None:
    """Remove avatar file from disk if it is managed by this app."""
    filename = avatar_filename_from_url(avatar_url)
    if not filename:
        return
    path = get_avatars_dir() / filename
    if path.is_file():
        path.unlink()


def detect_image_ext(content: bytes) -> str | None:
    """Detect image type from magic bytes."""
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return ".gif"
    if len(content) > 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def clear_managed_avatar_if_replaced(user: User, new_url: str) -> None:
    """Delete old uploaded file when avatar URL changes."""
    if user.avatar_url and user.avatar_url != new_url and is_managed_avatar_url(user.avatar_url):
        delete_avatar_file(user.avatar_url)


async def save_avatar_upload(session: Session, user: User, file: UploadFile) -> UserProfile:
    """Store uploaded avatar and update user profile."""
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


def remove_user_avatar(session: Session, user: User) -> UserProfile:
    """Remove avatar file and clear profile field."""
    delete_avatar_file(user.avatar_url)
    user.avatar_url = ""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user_to_profile(user)
