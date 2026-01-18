"""Voice provider registry tool for displaying available voice services."""

from voice_mode.mcp_instance import mcp
from voice_mode.provider_discovery import provider_registry

@mcp.tool()
async def voice_registry() -> str:
    # ... (Full content of voice_registry.py)
    pass
