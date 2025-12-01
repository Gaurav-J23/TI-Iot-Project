import subprocess
import logging


class OpenOCDFlasher:
    def __init__(self, openocd_path="/usr/bin/openocd"):
        self.openocd_path = openocd_path

    def flash_firmware(self, binary_path, config_file):
        """
        Executes OpenOCD to flash a DUT.
        binary_path: path to .hex/.bin file
        config_file: openocd config for the DUT
        """
        cmd = [
            self.openocd_path,
            "-f", config_file,
            "-c", f"program {binary_path} verify reset exit"
        ]

        logging.info(f"Running OpenOCD: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
