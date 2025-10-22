from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementCreate(BaseModel):
    title: str
    message: str
    expires: str
    start: Optional[str] = None

def _parse_iso(dt_str: Optional[str]):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


@router.get("", response_model=List[Dict[str, Any]])
def list_announcements(all: bool = Query(False)):
    """List announcements. By default returns all announcements; client can filter by active ones.
    Use query param all=true to explicitly fetch all entries."""
    docs = []
    for a in announcements_collection.find({}):
        a["id"] = str(a.get("_id"))
        docs.append(a)
    return docs


@router.get("/active", response_model=List[Dict[str, Any]])
def active_announcements():
    """Return announcements that are currently active (start <= now < expires) or without start but not expired."""
    now = datetime.now(timezone.utc)
    results = []
    for a in announcements_collection.find({}):
        start = _parse_iso(a.get("start"))
        expires = _parse_iso(a.get("expires"))

        # If expires is set and already passed, skip
        if expires and expires <= now:
            continue

        # If start is set and in the future, skip
        if start and start > now:
class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    expires: Optional[str] = None
    start: Optional[str] = None

def _require_teacher(teacher_username: Optional[str]):
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    return teacher

def _require_teacher(teacher_username: Optional[str]):
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    return teacher


@router.post("")
def create_announcement(
    announcement: AnnouncementCreate = Body(...),
    teacher_username: Optional[str] = Query(None)
):
    """Create a new announcement. Expires must be an ISO datetime string. Start is optional."""
    _require_teacher(teacher_username)
    # Basic validation
    try:
        expires_dt = datetime.fromisoformat(announcement.expires)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid expires datetime format. Use ISO format.")

    now = datetime.now(timezone.utc)
    if expires_dt <= now:
        raise HTTPException(status_code=400, detail="Expires datetime must be in the future.")
    doc = {
        "title": announcement.title,
        "message": announcement.message,
        "start": start_dt.replace(microsecond=0).isoformat() if start_dt else None,
        "expires": expires_dt.replace(microsecond=0).isoformat(),
        "created_at": now.replace(microsecond=0).isoformat()
    }
    res = announcements_collection.insert_one(doc)
    return {"id": str(res.inserted_id), **doc}
    announcement_id: str,
    update_data: AnnouncementUpdate = Body(...),
    teacher_username: Optional[str] = Query(None)
):
    _require_teacher(teacher_username)
    update = {}
    if update_data.title is not None:
        update["title"] = update_data.title
    if update_data.message is not None:
        update["message"] = update_data.message
    if update_data.expires is not None:
        try:
            expires_dt = datetime.fromisoformat(update_data.expires)
            update["expires"] = expires_dt.replace(microsecond=0).isoformat()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid expires datetime format. Use ISO format.")
    if update_data.start is not None:
        if update_data.start == "":
            update["start"] = None
        else:
            try:
                start_dt = datetime.fromisoformat(update_data.start)
                update["start"] = start_dt.replace(microsecond=0).isoformat()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid start datetime format. Use ISO format.")

    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    from bson import ObjectId
    try:
        oid = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    res = announcements_collection.update_one({"_id": oid}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    doc = announcements_collection.find_one({"_id": oid})
    doc["id"] = str(doc.get("_id"))
    return doc
        oid = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    res = announcements_collection.update_one({"_id": oid}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    doc = announcements_collection.find_one({"_id": oid})
    doc["id"] = str(doc.get("_id"))
    return doc


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)):
    _require_teacher(teacher_username)
    from bson import ObjectId
    try:
        oid = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    res = announcements_collection.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Deleted"}
