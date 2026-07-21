from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_optional_user
from app.models import User, VideoOpen
from app.schemas import VideoOpenIn

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/video-open", status_code=status.HTTP_204_NO_CONTENT)
def video_open(
    payload: VideoOpenIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    video_name = payload.video_name.strip()
    if not video_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="video_name is required",
        )
    db.add(
        VideoOpen(
            user_id=user.id if user else None,
            video_name=video_name,
            source=payload.source,
        )
    )
    db.commit()
