# /// script
# dependencies = ["mcp"]
# ///
import subprocess
import os
import shutil
import datetime
import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str]) -> str:
    """La tua funzione originale che garantisce il funzionamento della lista."""
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
    """Elenca le telecamere (Usa la tua logica originale)."""
    return run_executable_stream(["list"])

@mcp.tool()
async def capture_snap(camera_rtsp_url: str, camera_name: str) -> str:
    """
    Cattura un frame usando FFmpeg DIRETTO e ASINCRONO (Ispirato a ffmpeg-mcp).
    Evita il deadlock dei buffer e il segnale 'killed'.
    """
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"

    # Comando ottimizzato: TCP forzato e niente audio per massima velocità
    cmd = [
        "-y",
        "-rtsp_transport", "tcp",
        "-i", camera_rtsp_url,
        "-frames:v", "1",
        "-q:v", "2",
        target_path
    ]

    try:
        # Esecuzione asincrona: non blocca il server MCP
        process = await asyncio.create_subprocess_exec(
            ffmpeg_bin, *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await asyncio.wait_for(process.communicate(), timeout=45)

        if process.returncode == 0 and os.path.exists(target_path):
            return f"Snapshot creato con successo: {target_path}"
        else:
            err_msg = stderr.decode() if stderr else "Errore sconosciuto"
            return f"FFmpeg fallito (Code {process.returncode}): {err_msg}"
            
    except asyncio.TimeoutExpired:
        return "Errore: Timeout FFmpeg durante la cattura."
    except Exception as e:
        return f"Errore critico FFmpeg: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()