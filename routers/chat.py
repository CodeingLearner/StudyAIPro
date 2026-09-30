import os
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Header
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import AsyncGenerator, Optional
from services.db import get_db
from services.pdf_service import extract_text_from_pdf
from services.ai_service import stream_gemini
from models.user import User
from models.chat import ChatMessage
from sqlalchemy.orm import Session
from routers.auth import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

# Hardcoded Gemini API Key
GEMINI_API_KEY = "venv/GEMINI_API_KEY"

router = APIRouter()


class ChatIn(BaseModel):
    prompt: str
    mode: str = "Doubt Solver"
    context_text: str | None = None


async def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)) -> User:
    # This dependency expects a token in the Authorization header; FastAPI will pass None here when used implicitly.
    # For explicit header parsing in the frontend, we will decode manually in endpoints.
    raise HTTPException(status_code=401, detail="Not implemented")


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    content = await file.read()
    try:
        text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract PDF: {e}")
    return {"text": text}


@router.post("/chat")
async def chat_endpoint(payload: ChatIn, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    # Authorization header expected as: Bearer <token>
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    token = parts[1]
    try:
        payload_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload_token.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Store user message
    user_msg = ChatMessage(user_id=user.id, role="user", content=payload.prompt, mode=payload.mode)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        full_response = ""
        try:
            async for chunk in stream_gemini(payload.prompt, payload.mode, payload.context_text, GEMINI_API_KEY):
                decoded_chunk = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
                full_response += decoded_chunk
                yield chunk
            
            # Store the complete assistant response
            if full_response:
                assistant_msg = ChatMessage(user_id=user.id, role="assistant", content=full_response, mode=payload.mode)
                db.add(assistant_msg)
                db.commit()
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield error_msg.encode("utf-8")

    return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")


@router.get("/history")
async def get_history(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Get chat history for the authenticated user"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    token = parts[1]
    try:
        payload_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload_token.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all chat messages for this user
    messages = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at).all()
    return [{
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "mode": m.mode,
        "created_at": m.created_at.isoformat() if m.created_at else None
    } for m in messages]
