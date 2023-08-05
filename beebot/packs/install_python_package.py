import subprocess

from pydantic import BaseModel, Field

from beebot.body.pack_utils import init_workspace_poetry
from beebot.packs.system_base_pack import SystemBasePack

"""This will use a poetry venv specifically for the beebot workspace. However, all normal caveats apply regarding
downloading and executing remote code."""

PACK_NAME = "install_python_package"

PACK_DESCRIPTION = "Installs Python packages from PyPi using Poetry."


class InstallPythonPackageArgs(BaseModel):
    package_name: str = Field(
        ..., description="The name of the Python package to be installed"
    )


class InstallPythonPackage(SystemBasePack):
    name = PACK_NAME
    description = PACK_DESCRIPTION
    args_schema = InstallPythonPackageArgs
    categories = ["Programming"]

    def _run(self, package_name: str) -> str:
        if self.body.config.restrict_code_execution:
            return "Error: Installing Python packages is not allowed"
        try:
            # Make sure poetry is init'd in the workspace. This errors if it's already init'd so yolo
            init_workspace_poetry(self.config.workspace_path)
            cmd = ["poetry", "add", package_name]

            process = subprocess.run(
                cmd,
                universal_newlines=True,
                cwd=self.body.config.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if process.returncode:
                return f"Error: {process.stdout}. {process.stderr}."

            return f"{package_name} is installed."
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:
            return f"Error: {e}"
