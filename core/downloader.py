import httpx
import os
import aiofiles

PAPER_API = "https://api.papermc.io/v2/projects/paper"
MODRINTH_API = "https://api.modrinth.com/v2"

async def fetch_paper_versions():
    async with httpx.AsyncClient() as client:
        resp = await client.get(PAPER_API)
        data = resp.json()
        return data["versions"] # List of versions ["1.20.4", "1.21", ...]

async def fetch_paper_builds(version: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PAPER_API}/versions/{version}")
        data = resp.json()
        return data["builds"] # List of build numbers

async def download_paper_jar(version: str, build: str, destination: str):
    jar_name = f"paper-{version}-{build}.jar"
    url = f"{PAPER_API}/versions/{version}/builds/{build}/downloads/{jar_name}"
    
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as resp:
            resp.raise_for_status()
            async with aiofiles.open(destination, 'wb') as f:
                async for chunk in resp.aiter_bytes():
                    await f.write(chunk)

async def search_mods(query: str, version: str):
    """Search mods on Modrinth"""
    facets = f'[["versions:{version}"], ["project_type:mod"]]'
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{MODRINTH_API}/search", 
            params={"query": query, "facets": facets}
        )
        return resp.json()["hits"]

async def install_mod_from_url(url: str, destination: str):
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as resp:
            resp.raise_for_status()
            async with aiofiles.open(destination, 'wb') as f:
                async for chunk in resp.aiter_bytes():
                    await f.write(chunk)
