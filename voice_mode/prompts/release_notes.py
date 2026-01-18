from voice_mode.mcp_instance import mcp

@mcp.prompt(name="release-notes")
def release_notes_prompt():
    return "Release notes prompt"
