# /// script
# dependencies = ["mcp"]
# ///
import subprocess
import os
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate tramite camsnap."""
    bin_path = shutil.which("camsnap") or "camsnap"
    return subprocess.check_output([bin_path, "list"], text=True)

@mcp.tool()
def capture_snap_direct(camera_rtsp_url: str, camera_name: str) -> str:
    """Bypassa camsnap e invoca direttamente FFmpeg per evitare deadlock."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"
    
    cmd = [
        ffmpeg_bin,
        "-y",
        "-rtsp_transport", "tcp",
        "-i", camera_rtsp_url,
        "-frames:v", "1",
        "-q:v", "2",
        target_path
    ]
    
    try:
        # Buffer puliti: niente deadlock
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        
        if os.path.exists(target_path):
            return f"Snapshot OK (FFmpeg diretto): {target_path}"
        return "Errore: FFmpeg non ha prodotto il file."
    except Exception as e:
        return f"Errore durante l'invocazione diretta di FFmpeg: {str(e)}"

# Questa è la funzione che uvx cercherà grazie al pyproject.toml
def main():
    mcp.run()

if __name__ == "__main__":
    main()