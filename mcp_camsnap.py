# /// script
# dependencies = ["mcp"]
# ///
import asyncio
import os
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

async def run_cmd_async(args: list[str], silence: bool = False):
    """Esegue il comando in modo asincrono per non bloccare il server MCP."""
    bin_path = shutil.which("camsnap") or "camsnap"
    
    # Prepariamo la redirezione degli stream
    stdout_target = asyncio.subprocess.DEVNULL if silence else asyncio.subprocess.PIPE
    stderr_target = asyncio.subprocess.DEVNULL if silence else asyncio.subprocess.PIPE

    process = await asyncio.create_subprocess_exec(
        bin_path, *args,
        stdout=stdout_target,
        stderr=stderr_target
    )

    try:
        # Aspettiamo il completamento con un timeout reale
        stdout_data, stderr_data = await asyncio.wait_for(process.communicate(), timeout=45.0)
        return process.returncode, (stdout_data.decode().strip() if stdout_data else ""), (stderr_data.decode().strip() if stderr_data else "")
    except asyncio.TimeoutExpired:
        process.kill()
        return -1, "", "Timeout asincrono scaduto"
    except Exception as e:
        return -1, "", str(e)

@mcp.tool()
async def list_cameras() -> str:
    """Recupera la lista telecamere in modo asincrono (Non blocca l'MCP)."""
    code, out, err = await run_cmd_async(["list"])
    if code == 0:
        return out if out else "Lista vuota."
    return f"Errore lista: {err}"

@mcp.tool()
async def capture_snap(camera_name: str) -> str:
    """Cattura un frame usando l'esecuzione asincrona isolata."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Per lo snap usiamo silence=True per evitare che i log di FFmpeg intasino le pipe
    code, out, err = await run_cmd_async(["snap", camera_name, "--out", target_path], silence=True)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return f"Snapshot creato: {target_path}"
    
    return f"Cattura fallita (Code {code}). Verifica log sistema o URL RTSP."

if __name__ == "__main__":
    mcp.run()