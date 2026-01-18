from voice_mode.mcp_instance import mcp

@mcp.resource("voicemode://docs/quickstart")
def quickstart():
    return "Quickstart docs"
