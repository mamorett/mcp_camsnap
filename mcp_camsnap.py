# /// script
# dependencies = ["mcp"]
# ///
import asyncio
import os
import shutil
import datetime
import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

@mcp.tool()
async def list_cameras() -> str:
    """Elenca le telecamere forzando il caricamento dell'ambiente utente."""
    bin_path = shutil.which("camsnap") or "camsnap"
    
    # Prendiamo l'ambiente attuale e assicuriamoci che HOME sia corretta
    # camsnap cerca la config in $HOME/.config/camsnap/ o percorsi simili
    env = os.environ.copy()
    
    process = await asyncio.create_subprocess_exec(
        bin_path, "list",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    stdout, stderr = await process.communicate()
    
    out_text = stdout.decode().strip()
    err_text = stderr.decode().strip()
    
    if process.returncode == 0:
        if not out_text:
            return f"Camsnap eseguito, ma lista vuota. Path: {bin_path}\nEnv HOME: {env.get('HOME')}"
        return out_text
    
    return f"Errore {process.returncode}: {err_text}"

@mcp.tool()
async def capture_snap(camera_name: str) -> str:
    """Cattura uno snapshot (Headless Async)."""
    bin_path = shutil.which("camsnap") or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Eseguiamo con protezione totale dei log per non rompere il JSON-RPC
    process = await asyncio.create_subprocess_exec(
        bin_path, "snap", camera_name, "--out", target_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        env=os.environ.copy()
    )
    
    try:
        await asyncio.wait_for(process.wait(), timeout=45)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot creato: {target_path}"
        return "Errore: File non generato. Controlla se 'camsnap list' vede la camera."
    except asyncio.TimeoutExpired:
        process.kill()
        return "Errore: Timeout (45s)."

def main():
    mcp.run()

if __name__ == "__main__":
    main()