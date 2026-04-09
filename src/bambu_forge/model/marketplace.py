"""MakerWorld marketplace search with mock mode and graceful degradation."""

from __future__ import annotations

import httpx

_MOCK_RESULTS = [
    {
        "name": "Phone Stand",
        "creator": "DesignPro",
        "thumbnail_url": "https://makerworld.com/thumb/1.jpg",
        "download_url": "https://makerworld.com/dl/1",
        "license": "CC BY",
        "print_count": 4523,
    },
    {
        "name": "Cable Organizer",
        "creator": "PrintMaster",
        "thumbnail_url": "https://makerworld.com/thumb/2.jpg",
        "download_url": "https://makerworld.com/dl/2",
        "license": "CC BY-SA",
        "print_count": 2891,
    },
]


async def search_marketplace(
    query: str, mock: bool = False, max_results: int = 10
) -> dict:
    """Search MakerWorld for printable models."""
    if mock:
        filtered = [
            r for r in _MOCK_RESULTS if query.lower() in r["name"].lower()
        ]
        return {
            "status": "success",
            "results": filtered[:max_results],
            "source": "makerworld",
            "count": len(filtered[:max_results]),
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://makerworld.com/api/v1/design",
                params={"keyword": query, "limit": max_results},
            )
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "error_code": "MARKETPLACE_UNAVAILABLE",
                    "message": f"MakerWorld returned {resp.status_code}",
                }
            data = resp.json()
            results = data.get("hits", data.get("designs", []))
            return {
                "status": "success",
                "results": results[:max_results],
                "source": "makerworld",
                "count": len(results[:max_results]),
            }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "MARKETPLACE_UNAVAILABLE",
            "message": f"MakerWorld unreachable: {e}",
        }
