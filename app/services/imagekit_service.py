import asyncio
from typing import Any
from app.aimge import imagekit

async def upload_with_retry(file, file_name, retries=3):
    loop = asyncio.get_running_loop() #return current event loop

    for attempt in range(retries):
        try:
            result = await loop.run_in_executor( # run the blocking upload_file function in a separate thread to avoid blocking the event loop
                None,
                lambda: imagekit.upload_file({
                    "file": file,
                    "file_name": file_name,
                    "use_unique_file_name": True,
                })
            )
            return result

        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(1)