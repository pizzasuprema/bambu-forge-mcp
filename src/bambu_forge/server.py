from fastmcp import FastMCP

mcp = FastMCP(
    "bambu-forge",
    instructions="All-in-one MCP server for Bambu Lab 3D printers",
)


@mcp.tool()
async def ping() -> dict:
    """Health check — returns server version and status."""
    from bambu_forge import __version__

    return {"status": "ok", "version": __version__}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
