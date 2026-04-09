"""Camera snapshot capture for Bambu Lab printers."""

from __future__ import annotations

import os


async def capture_snapshot(
    camera: str = "liveview",
    mock: bool = False,
    workspace: str = "/tmp",
) -> dict:
    if mock:
        img_path = os.path.join(workspace, f"snapshot_{camera}.png")
        try:
            from PIL import Image

            img = Image.new("RGB", (100, 100), color=(128, 128, 128))
            img.save(img_path)
        except ImportError:
            with open(img_path, "w") as f:
                f.write(f"[Mock snapshot from {camera} camera]")

        return {
            "status": "success",
            "camera": camera,
            "file_path": img_path,
            "message": f"Mock snapshot captured from {camera} camera",
        }

    return {
        "status": "error",
        "error_code": "NOT_IMPLEMENTED",
        "message": "Real camera capture requires TUTK P2P protocol (future work)",
    }
