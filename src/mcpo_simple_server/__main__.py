"""
Main entry point for running the MCPOSimpleServer as a module.

This allows running the server with `python -m mcpo_simple_server`
"""
import sys
import argparse
import uvicorn
from mcpo_simple_server.logger import logger
from mcpo_simple_server.services.starter import LibVerifierService, LibType


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCPOSimpleServer - MCP implementation")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    return parser.parse_args()


def main():
    """Run the server."""
    try:
        args = parse_args()
        logger.info(f"Starting MCPOSimpleServer on {args.host}:{args.port}")
        logger.info("Checking required libraries...")
        # Precheck
        libverifier_service = LibVerifierService()
        check_results = libverifier_service.check_all()
        if check_results[LibType.PYTHON3].status == "missing":
            logger.error("Python is not installed. Please install Python and try again.")
            sys.exit(1)
        else:
            logger.info(f"Python {check_results[LibType.PYTHON3].version} is installed at {check_results[LibType.PYTHON3].path}")
        if check_results[LibType.NPX].status == "missing":
            logger.error("NPX is not installed. Please install NPX and try again.")
            logger.error("NPX can be installed by running: apt-get -y install npm && npm install -g npx")
            sys.exit(1)
        else:
            logger.info(f"NPX {check_results[LibType.NPX].version} is installed at {check_results[LibType.NPX].path}")
        if check_results[LibType.UVX].status == "missing":
            logger.error("UVX is not installed. Please install UVX and try again.")
            sys.exit(1)
        else:
            logger.info(f"UVX {check_results[LibType.UVX].version} is installed at {check_results[LibType.UVX].path}")

        uvicorn.run(
            "mcpo_simple_server.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
