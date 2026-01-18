from voice_mode.mcp_instance import mcp

@mcp.resource("audio://files/{directory}")
async def list_audio_files(directory="all"):
    return "List of audio files"
