from typing import Dict
from pydantic import BaseModel
import sys
import subprocess

from enum import Enum

__all__ = ['LibType', 'LibCheckResult', 'LibVerifierService']


class LibType(Enum):
    PYTHON3 = "python3"
    NPX = "npx"
    UVX = "uvx"


class LibCheckResult(BaseModel):
    status: str = "missing"  # Either "missing" or "installed"
    version: str = ""  # Version of the library if installed
    path: str = ""  # Path to the library if installed
    message: str = ""  # Additional message


class LibVerifierService:
    def __init__(self):
        self.libs = {LibType.NPX: {"version": "", "path": ""},
                     LibType.UVX: {"version": "", "path": ""},
                     LibType.PYTHON3: {"version": "", "path": ""}}

    def check(self, lib: LibType) -> LibCheckResult:
        """
        Checks if a library is installed and returns its version and path.

        Args:
            lib: The library to check

        Returns:
            LibCheckResult: The result of the library check
        """
        # Default result for unknown library type
        result = LibCheckResult(
            status="missing",
            message=f"Unknown library type: {lib}"
        )

        if lib == LibType.PYTHON3:
            try:
                # Check Python version
                version = sys.version.split()[0]

                # Get Python executable path
                path = sys.executable

                # Update Python info in internal state
                self.libs[LibType.PYTHON3] = {"version": version, "path": path}

                if version:
                    result = LibCheckResult(
                        status="installed",
                        version=version,
                        path=path,
                        message="Python is installed"
                    )
                else:
                    result = LibCheckResult(
                        status="missing",
                        message="Python version could not be determined"
                    )
            except Exception as e:
                result = LibCheckResult(
                    status="missing",
                    message=f"Error checking Python: {str(e)}"
                )
        elif lib == LibType.NPX:
            try:
                # Check NPX version using subprocess
                cmd_result = subprocess.run(['npx', '--version'], capture_output=True, text=True, check=False)
                if cmd_result.returncode == 0:
                    version = cmd_result.stdout.strip()
                    path = subprocess.run(['which', 'npx'], capture_output=True, text=True, check=False).stdout.strip()

                    # Update internal state
                    self.libs[LibType.NPX] = {"version": version, "path": path}

                    result = LibCheckResult(
                        status="installed",
                        version=version,
                        path=path,
                        message="NPX is installed"
                    )
                else:
                    result = LibCheckResult(
                        status="missing",
                        message="NPX is not installed or not in PATH"
                    )
            except Exception as e:
                result = LibCheckResult(
                    status="missing",
                    message=f"Error checking NPX: {str(e)}"
                )
        elif lib == LibType.UVX:
            try:
                # Check UVX version using subprocess
                cmd_result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, check=False)
                if cmd_result.returncode == 0:
                    # Extract only the numeric version (remove 'uvx' prefix)
                    full_version = cmd_result.stdout.strip()
                    # Split by space and take the last part which should be the version number
                    version = full_version.split()[-1] if ' ' in full_version else full_version.replace('uvx', '')
                    path = subprocess.run(['which', 'uvx'], capture_output=True, text=True, check=False).stdout.strip()

                    # Update internal state
                    self.libs[LibType.UVX] = {"version": version, "path": path}

                    result = LibCheckResult(
                        status="installed",
                        version=version,
                        path=path,
                        message="UVX is installed"
                    )
                else:
                    result = LibCheckResult(
                        status="missing",
                        message="UVX is not installed or not in PATH"
                    )
            except Exception as e:
                result = LibCheckResult(
                    status="missing",
                    message=f"Error checking UVX: {str(e)}"
                )

        return result

    def check_all(self) -> Dict[LibType, LibCheckResult]:
        """
        Checks all libraries and returns their status.

        Returns:
            Dict[LibType, LibCheckResult]: A dictionary of library check results
        """
        results = {}
        for lib in LibType:
            results[lib] = self.check(lib)
        return results

    def get_status(self) -> Dict[LibType, Dict[str, str]]:
        """
        Returns the current status of all libraries.

        Returns:
            Dict[LibType, Dict[str, str]]: A dictionary containing version and path information for each library
        """
        return self.libs
