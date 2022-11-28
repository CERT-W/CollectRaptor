# -*- coding: UTF-8 -*-

import csv
import hashlib
import os
import platform
import requests
import shlex
import shutil
import subprocess
import sys
import zipfile

from loguru import logger

from helpers.enum import OsArchitecture


class VelociraptorPacker:

    @staticmethod
    def __download_binary(os_version: OsArchitecture, output_folder: str) -> str:
        url = 'https://api.github.com/repos/Velocidex/velociraptor/releases/latest'

        velociraptor_version = ''
        if os_version == OsArchitecture.Windows_x64:
            velociraptor_version = 'windows-amd64.exe'
        elif os_version == OsArchitecture.Windows_x86:
            velociraptor_version = 'linux-amd64'
        elif os_version == OsArchitecture.Linux_x64:
            velociraptor_version = 'linux-amd64'
        else:
            logger.error(f'Unsupported of Velociraptor version specified: {os_version}')
            exit(1)

        # Lists the released assets.
        logger.info(f'Retrieving Velociraptor last release information to download base binary for {os_version.value}...')
        r = requests.get(url)
        if r.status_code != 200:
            logger.error(f'Couldn\'t retrieve Velociraptor last release information, status code = {r.status_code}')
            exit(1)

        assets = r.json()['assets']

        for asset in assets:
            if 'browser_download_url' in asset and asset['browser_download_url'].endswith(velociraptor_version):
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

    @staticmethod
    def build_collector(target_os: OsArchitecture, config_path: str, output_path: str, tools_csv: str = None) -> None:
        tmp_folder = os.path.join(os.path.dirname(output_path), 'tmp')
        os.makedirs(tmp_folder, exist_ok=True)

        # Current OS architecture.
        current_os = OsArchitecture(f'{platform.system()}-{platform.machine()}')
        current_os_binary = VelociraptorPacker.__download_binary(current_os, tmp_folder)

        target_os_binary = current_os_binary if current_os == target_os else VelociraptorPacker.__download_binary(target_os, tmp_folder)

        tools_zip = VelociraptorPacker.__download_tools(tools_csv, tmp_folder) if tools_csv else ''

        # artifact_exchange_folder = VelociraptorPacker.__download_artifact_exchange(tmp_folder)
        # build_cmd = f'{current_os_binary} --definitions={artifact_exchange_folder} config repack --exe={target_os_binary} {config_path} {output_path}'

        build_cmd = f'{current_os_binary} config repack --exe={target_os_binary} {f"--append={tools_zip}" if tools_zip else ""} {config_path} {output_path}'
        logger.info(f'Building Velociraptor collector with command: \'{build_cmd}\'')

        process = subprocess.run(shlex.split(build_cmd, posix="win" not in sys.platform), shell=False, capture_output=True)
        if process.stderr == b'':
            logger.success(f'Velociraptor collector built to: \'{output_path}\'')
        else:
            logger.error(f'Velociraptor collector could not be built: \'{process.stderr.decode("utf-8").strip()}\'')

