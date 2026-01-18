#!/usr/bin/env python
from .mcp_instance import mcp
from . import tools

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
