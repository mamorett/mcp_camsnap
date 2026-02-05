# /// script
# dependencies = ["mcp"]
# ///
import asyncio
import os
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

@mcp.tool()
async def list_cameras() -> str:
    """Ritorna la lista delle telecamere (Logica originale)."""
    bin_path = shutil.which("camsnap") or "camsnap"
    # Usiamo asyncio per non bloccare il canale JSON-RPC dell'MCP
    process = await asyncio.create_subprocess_exec(
        bin_path, "list",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        return stdout.decode().strip() or "Nessuna camera trovata."
    return f"Errore lista: {stderr.decode()}"

@mcp.tool()
async def capture_snap(camera_name: str) -> str:
    """Cattura uno snapshot (Axiom Zero: No hardcoding)."""
    bin_path = shutil.which("camsnap") or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # DEVNULL protegge lo stdout dell'MCP dai log di FFmpeg
    process = await asyncio.create_subprocess_exec(
        bin_path, "snap", camera_name, "--out", target_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    
    try:
        await asyncio.wait_for(process.wait(), timeout=45)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot creato: {target_path}"
        return "Errore: File non generato correttamente."
    except asyncio.TimeoutExpired:
        process.kill()
        return "Errore: Timeout (45s) durante lo snap."

def main():
    """Funzione chiamata da uvx tramite l'entry point del TOML."""
    mcp.run()

if __name__ == "__main__":
    main()