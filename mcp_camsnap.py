# /// script
# dependencies = ["mcp"]
# ///
import subprocess
import os
import shutil
import datetime
import sys
from mcp.server.fastmcp import FastMCP

# Creiamo l'istanza FastMCP
mcp = FastMCP("Camsnap Manager")

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    bin_path = shutil.which("camsnap") or "camsnap"
    # Usiamo stderr=subprocess.DEVNULL per essere certi che nulla sporchi lo stream
    return subprocess.check_output([bin_path, "list"], text=True, stderr=subprocess.DEVNULL)

@mcp.tool()
def capture_snap_direct(camera_rtsp_url: str, camera_name: str) -> str:
    """Bypassa camsnap e invoca direttamente FFmpeg."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"
    
    cmd = [
        ffmpeg_bin, "-y", "-rtsp_transport", "tcp",
        "-i", camera_rtsp_url, "-frames:v", "1", "-q:v", "2",
        target_path
    ]
    
    try:
        # Reindirizziamo TUTTO (out e err) a DEVNULL. 
        # In MCP, stdout è sacro: serve solo al protocollo.
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        
        if os.path.exists(target_path):
            return f"Snapshot OK: {target_path}"
        return "Errore: FFmpeg non ha prodotto il file."
    except Exception as e:
        return f"Errore bypass: {str(e)}"

def main():
    # TRUCCO CRUCIALE: Rindirizziamo temporaneamente stderr su stdout 
    # solo se non siamo in modalità MCP, ma qui vogliamo l'opposto.
    # Assicuriamoci che nulla scriva su stdout accidentalmente.
    try:
        mcp.run()
    except Exception as e:
        # Se c'è un errore, lo scriviamo su stderr, così MCP lo logga senza crashare
        print(f"Server Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()