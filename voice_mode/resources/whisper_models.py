from voice_mode.mcp_instance import mcp

@mcp.resource("whisper://models")
async def list_whisper_models():
    return "List of whisper models"
