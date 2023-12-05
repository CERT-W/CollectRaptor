# -*- coding: UTF-8 -*-

import csv
import hashlib
import os
import platform
import requests
import shlex
import shutil
import stat
import subprocess
import sys
import zipfile

from loguru import logger

from helpers.enum import OsArchitecture


class VelociraptorPacker:

    """
    Download the builder binary used to execute the "config repack" command.
    Must be <= v0.6.7 as the "--append" option is required to embed 3rd-party tools.
    """
    @staticmethod
    def __download_binary_builder(os_version: OsArchitecture, output_folder: str) -> str:
        URL_WINDOWS_X86 = 'https://github.com/Velocidex/velociraptor/releases/download/v0.6.7-5/velociraptor-v0.6.7-windows-386.exe'
        URL_WINDOWS_X64 = 'https://github.com/Velocidex/velociraptor/releases/download/v0.6.7-5/velociraptor-v0.6.7-4-windows-amd64.exe'
        URL_LINUX = 'https://github.com/Velocidex/velociraptor/releases/download/v0.6.7-5/velociraptor-v0.6.7-4-linux-amd64-musl'

        velociraptor_url = ''
        if os_version == OsArchitecture.Windows_x64:
            velociraptor_url = URL_WINDOWS_X64
        elif os_version == OsArchitecture.Windows_x86:
            velociraptor_url = URL_WINDOWS_X86
        elif os_version == OsArchitecture.Linux_x64:
            velociraptor_url = URL_LINUX
        else:
            logger.error(f'Building on unsupported os: {os_version}')
            exit(1)

        binary_name = os.path.basename(velociraptor_url)
        output_path = os.path.join(output_folder, binary_name)

        if os.path.isfile(output_path):
            logger.success(f'Velociraptor builder binary for {os_version.value} already present in \'{output_path}\'...')
        else:
            logger.info(f'Downloading Velociraptor builder binary for {os_version.value} from \'{velociraptor_url}\'...')
            r = requests.get(velociraptor_url, allow_redirects=True)
            open(output_path, 'wb').write(r.content)
            logger.success(f'Downloaded Velociraptor builder binary to \'{output_path}\'!')

        return output_path

    """
    Download the "alternate" binary that will be used as the collector.
    Uses latest release version.
    """
    @staticmethod
    def __download_binary_alternate(os_version: OsArchitecture, output_folder: str) -> str:
        url = 'https://api.github.com/repos/Velocidex/velociraptor/releases/latest'

        velociraptor_version_alternate = ''
        if os_version == OsArchitecture.Windows_x64:
            velociraptor_version_alternate = 'windows-amd64.exe'
        elif os_version == OsArchitecture.Windows_x86:
            velociraptor_version_alternate = 'windows-386.exe'
        elif os_version == OsArchitecture.Linux_x64:
            velociraptor_version_alternate = 'linux-amd64-musl'
        else:
            logger.error(f'Unsupported Velociraptor version specified for collector: {os_version}')
            exit(1)

        # Lists the released assets.
        logger.info(f'Retrieving Velociraptor last release information to download base binary for {os_version.value}...')
        r = requests.get(url)
        if r.status_code != 200:
            logger.error(f'Couldn\'t retrieve Velociraptor last release information, status code = {r.status_code}')
            exit(1)

        assets = r.json()['assets']

        for asset in assets:
            if 'browser_download_url' in asset and asset['browser_download_url'].endswith(velociraptor_version_alternate):
                asset_url = asset['browser_download_url']
                asset_name = os.path.basename(asset_url)
                output_path = os.path.join(output_folder, asset_name)

                if os.path.isfile(output_path):
                    logger.success(f'Velociraptor base binary for {os_version.value} already present in \'{output_path}\'...')
                else:
                    logger.info(f'Downloading Velociraptor base binary for {os_version.value} from \'{asset_url}\'...')
                    r = requests.get(asset_url, allow_redirects=True)
                    open(output_path, 'wb').write(r.content)
                    logger.success(f'Downloaded Velociraptor base binary to \'{output_path}\'!')

                return output_path

    """_summary_
    Download the artifacts from the artifact exchange.
    Currently not used as all artifacts are bundled in the template config file.
    """
    @staticmethod
    def __download_artifact_exchange(output_folder: str) -> str:
        url = 'https://github.com/Velocidex/velociraptor-docs/raw/gh-pages/exchange/artifact_exchange.zip'
        output_artifact_exchange_zip = os.path.join(output_folder, 'artifact_exchange.zip')
        output_artifact_exchange_folder = os.path.join(output_folder, 'artifact_exchange')

        logger.info(f'Retrieving Velociraptor artifacts from the artifact exchange...')

        r = requests.get(url)
        if r.status_code != 200:
            logger.error(f'Couldn\'t retrieve artifacts from the artifact exchange, status code = {r.status_code}')
            exit(1)

        open(output_artifact_exchange_zip, 'wb').write(r.content)

        with zipfile.ZipFile(output_artifact_exchange_zip, 'r') as zip_ref:
            zip_ref.extractall(output_artifact_exchange_folder)

        return output_artifact_exchange_folder

    """
    Uses the tools CSV file to download the specified 3rd-party tools and bundle them into a zip file with inventory.csv (as required by Velociraptor).
    """
    @staticmethod
    def __download_tools(tools_csv_file: str, output_folder: str) -> str:
        output_tools_folder = os.path.join(output_folder, 'uploads')
        output_inventory_csv = os.path.join(output_tools_folder, 'inventory.csv')

        os.makedirs(output_tools_folder, exist_ok=True)

        logger.info(f'Retrieving required third-party tools from {tools_csv_file}...')

        f_in = open(tools_csv_file)
        f_out = open(output_inventory_csv, 'w+', newline='')
        csv_reader = csv.DictReader(f_in)
        csv_writter = csv.DictWriter(f_out, fieldnames=['ToolName', 'Filename', 'ExpectedHash', 'Size'])

        csv_writter.writeheader()

        while (tool_dict := next(csv_reader, None)) is not None:
            logger.info(f'Downloading {tool_dict["ToolName"]} from {tool_dict["Source"]}...')

            tool_output = os.path.join(output_tools_folder, tool_dict["EndpointFilename"])

            r = requests.get(tool_dict["Source"])
            if r.status_code != 200:
                logger.error(f'Couldn\'t retrieve artifacts from the artifact exchange, status code = {r.status_code}')
                exit(1)
            open(tool_output, 'wb').write(r.content)

            csv_writter.writerow({'ToolName': tool_dict["ToolName"], 'Filename': f'./uploads/{tool_dict["EndpointFilename"]}', 'ExpectedHash': hashlib.sha256(r.content).hexdigest(), 'Size': len(r.content)})

            logger.success(f'{tool_dict["ToolName"]} written to {tool_output}...')

        f_in.close()
        f_out.close()

        shutil.make_archive(output_tools_folder, 'zip', output_folder)

        return f'{output_tools_folder}.zip'

    """
    Build the collector binary.
    """
    @staticmethod
    def build_collector(target_os: OsArchitecture, config_path: str, output_path: str, tools_csv: str = None) -> None:
        tmp_folder = os.path.join(os.path.dirname(output_path), 'tmp')
        os.makedirs(tmp_folder, exist_ok=True)

        # Current OS architecture.
        current_os = OsArchitecture(f'{platform.system()}-{platform.machine()}')
        builder_os_binary = VelociraptorPacker.__download_binary_builder(current_os, tmp_folder)
        target_os_binary = VelociraptorPacker.__download_binary_alternate(target_os, tmp_folder)

        tools_zip = VelociraptorPacker.__download_tools(tools_csv, tmp_folder) if tools_csv else ''

        # Make the builder binary executable by the current user.
        if os.name == 'posix':
            st = os.stat(builder_os_binary)
            os.chmod(builder_os_binary, st.st_mode | stat.S_IEXEC)

        # Handle space(s) in builder binary path on Windows.
        # Dirty trick with cmd.exe and start to fail the build if an error message is raised by velociraptor.
        # Source: https://stackoverflow.com/questions/50315227/cannot-get-exit-code-when-running-subprocesses-in-python-using-popen-and-start
        if os.name == 'nt' and ' ' in builder_os_binary:
            if tools_zip:
                build_cmd = f'{os.environ.get("ComSpec", "cmd.exe")} /v:on /c "(start "" /wait "{builder_os_binary}" config repack --exe="{target_os_binary}" --append="{tools_zip}" "{config_path}" "{output_path}") & exit !errorlevel!"'
            else:
                build_cmd = f'{os.environ.get("ComSpec", "cmd.exe")} /v:on /c "(start "" /wait "{builder_os_binary}" config repack --exe="{target_os_binary}" "{config_path}" "{output_path}") & exit !errorlevel!"'
            logger.info(f'Building Velociraptor collector with command: \'{build_cmd}\'')
            process = subprocess.run(build_cmd, shell=True, capture_output=True)
        else:
            build_cmd = f'{builder_os_binary} config repack --exe={target_os_binary} {f"--append={tools_zip}" if tools_zip else ""} {config_path} {output_path}'
            logger.info(f'Building Velociraptor collector with command: \'{build_cmd}\'')
            process = subprocess.run(shlex.split(build_cmd, posix="win" not in sys.platform), shell=False, capture_output=True)

        if process.returncode == 0:
            logger.success(f'Velociraptor collector built to: \'{output_path}\'')
        else:
            logger.error(f'Velociraptor collector could not be built: \'{process.stderr.decode("utf-8").strip()}\'')
