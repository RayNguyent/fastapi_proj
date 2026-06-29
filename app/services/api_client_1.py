# app/services/api_client.py

import httpx
import asyncio
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def fetch_with_retry(client, url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            logger.info("Sending request", extra={
                "url": url,
                "attempt": attempt
            })

            response = await client.get(url, timeout=3.0)

            logger.info("Request success", extra={
                "url": url,
                "status": response.status_code
            })

            return {
                "url": url,
                "status": response.status_code
            }

        except Exception as e:
            logger.error("Request failed", extra={
                "url": url,
                "attempt": attempt,
                "error": str(e)
            })

            if attempt == retries - 1:
                return {"url": url, "error": "failed"}

            await asyncio.sleep(1) #wait for 1 second before retrying
#calls an API (GET request). If fails -> retry 3 times, if still fails -> raise exception

async def fetch_all(urls: List[str]) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(verify=False,timeout=5.0) as client:
        tasks = [fetch_with_retry(client, url) for url in urls]
        return await asyncio.gather(*tasks)
#takes a list of URLs and fetches them concurrently with retry logic
#httpx.AsyncClient is used to make asynchronous HTTP requests, allowing multiple requests to be made concurrently.
# gather is used to run all the tasks concurrently and wait for their completion, returning the results as a list of dictionaries containing the URL and its corresponding status code.
