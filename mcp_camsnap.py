# /// script
# dependencies = ["mcp"]
# ///
import asyncio
import os
import shutil
import datetime
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str]) -> str:
    """La tua funzione originale - NON TOCCATA - garantisce la lista."""
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    try:
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        stdout, stderr = process.communicate(timeout=30)
        clean_stdout = stdout.strip()
        if process.returncode == 0:
            if not clean_stdout and stderr:
                return f"Output (da stderr): {stderr.strip()}"
            return clean_stdout or "Comando eseguito, ma output vuoto."
        else:
            return f"Errore {process.returncode}\nLOG: {stderr}\nOUT: {stdout}"
    except subprocess.TimeoutExpired:
        process.kill()
        return "Errore: Timeout."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate (Usa la tua logica originale)."""
    return run_executable_stream(["list"])

@mcp.tool()
async def capture_snap(camera_name: str) -> str:
    """
    Cattura un frame delegando a camsnap, ma in modo ASINCRONO (Stile ffmpeg-mcp).
    Questo previene il 'signal: killed' causato dai buffer di FFmpeg.
    """
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"

    try:
        # Usiamo asyncio.create_subprocess_exec per gestire lo snap in background.
        # Riduciamo il carico del protocollo MCP ignorando i log prolissi di FFmpeg/camsnap.
        process = await asyncio.create_subprocess_exec(
            camsnap_bin, "snap", camera_name, "--out", target_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        # Attendiamo il processo senza bloccare il server MCP (timeout 45s)
        await asyncio.wait_for(process.wait(), timeout=45)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot creato con successo: {target_path}"
        else:
            return f"Errore: Camsnap ha terminato ma il file {target_path} è mancante o vuoto."
            
    except asyncio.TimeoutExpired:
        if process: process.terminate()
        return f"Errore: Timeout durante lo snap di '{camera_name}'."
    except Exception as e:
        return f"Errore critico asincrono: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()