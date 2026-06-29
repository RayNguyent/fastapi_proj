from time import time

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate,PostResponse
from app.data import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.aimge import imagekit
#from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import shutil
import os
import uuid
import tempfile
from app.services.api_client_1 import fetch_all
from app.services.imagekit_service import upload_with_retry
import time
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def life_span(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=life_span)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), 
                    caption: str = Form(""),
                    session: AsyncSession = Depends(get_async_session)): 
    #dependency injection: we get the async session by calling depends() and pass it as
    #variable "session" inside of upload_file()
    
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
        

        with open(temp_file_path, "rb") as f:
            upload_result = await upload_with_retry(f, file.filename)


        
        if upload_result.response_metadata.https_status_code == 200:
            post = Post(
                caption = caption,
                url = upload_result.url,
                file_type = "video" if file.content_type.startswith("video/") else "photo",
                file_name = upload_result.name
            )
            session.add(post)
            await session.commit()
            await session.refresh(post)
            return post
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()
        

@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]
    
    posts_data = []
    for post in posts:
        posts_data.append(
            {
                "id":str(post .id),
                "caption": post.caption,
                "url": post.url,
                "file_type":post.file_type,
                "file_name":post.file_name,
                "created_at":post.created_at.isoformat()
                
            }
        )
    return {"posts":posts_data}

@app.post("/external-data")
async def get_external_data(urls: list[str]):
    print("START:", time.time())
    result = await fetch_all(urls)
    print("END:", time.time())
    return {"results": result}

