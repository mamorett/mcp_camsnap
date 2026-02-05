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
async def capture_snap(camera_name: str) -> str:
    """
    Cattura uno snapshot usando il NOME della camera.
    Recupera l'URL corretto automaticamente per evitare il 404.
    """
    # 1. Recuperiamo l'URL chiamando 'camsnap list' tramite la tua funzione sicura
    # Cerchiamo di capire qual è l'URL per quella camera specifica
    lista = run_executable_stream(["list"])
    
    # Cerchiamo la riga della camera (logica semplice di parsing)
    target_url = ""
    for line in lista.splitlines():
        if camera_name in line and "rtsp://" in line:
            # Estraiamo l'URL dalla riga (solitamente è l'ultima parte)
            parts = line.split()
            for part in parts:
                if part.startswith("rtsp://"):
                    target_url = part
                    break
    
    if not target_url:
        return f"Errore: non ho trovato l'URL RTSP per la camera '{camera_name}' nella lista."

    # 2. Ora chiamiamo FFmpeg con l'URL COMPLETO (incluso path e auth se presenti nella lista)
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"

    cmd = [
        "-y", "-rtsp_transport", "tcp",
        "-i", target_url,
        "-frames:v", "1", "-q:v", "2",
        target_path
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            ffmpeg_bin, *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

        if process.returncode == 0 and os.path.exists(target_path):
            return f"Snapshot OK: {target_path}"
        else:
            return f"Errore FFmpeg (URL usato: {target_url}): {stderr.decode()}"
    except Exception as e:
        return f"Errore critico: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()