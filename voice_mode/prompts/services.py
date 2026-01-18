from voice_mode.mcp_instance import mcp

@mcp.prompt(name="whisper")
def whisper_prompt():
    return "Whisper service prompt"
