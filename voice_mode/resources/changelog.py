from voice_mode.mcp_instance import mcp

@mcp.resource("changelog://voice-mode")
def changelog_resource():
    return "Changelog content"
