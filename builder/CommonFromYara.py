# -*- coding: UTF-8 -*-

import glob
import os
import pathlib
import requests
import shlex
import shutil
import subprocess
import sys

from loguru import logger

from helpers.enum import OsArchitecture
from helpers.VelociraptorPacker import VelociraptorPacker


class CommonFromYara:
    def __init__(self, target_os: OsArchitecture, zip_password: str, yara_input: str, template: str = None, output_dir: str = None, tools_csv: str = None):
        self.target_os = target_os
        self.yara_input =  yara_input
        self.zip_password = zip_password
        self.tools_csv = tools_csv

        base_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
        self.output_dir = output_dir if output_dir else os.path.join(base_dir, 'outputs')
        os.makedirs(self.output_dir, exist_ok=True)

        if target_os == OsArchitecture.Windows_x64 or target_os == OsArchitecture.Windows_x86:
            self.template = template if template else os.path.join(base_dir,
                                                                   'templates',
                                                                   'Windows_yara.template')
            self.output_config = os.path.join(self.output_dir, 'Windows_yara.yaml')
            self.output_binary = os.path.join(self.output_dir, 'Windows_yara.exe')

        elif target_os == OsArchitecture.Linux_x64:
            self.template = template if template else os.path.join(base_dir,
                                                                   'templates',
                                                                   'Linux_yara.template')
            self.output_config = os.path.join(self.output_dir, 'Linux_yara.yaml')
            self.output_binary = os.path.join(self.output_dir, 'Linux_yara')

        else:
            logger.error(f'Unsupported target OS: {target_os}')
            exit(-1)

    """
    Concat all yara rules if a folder is specified.
    """
    def __concat_yara(self) -> str:
        if os.path.isfile(self.yara_input):
            yara_path = self.yara_input

        # Processing a folder.
        else:
            yara_path = os.path.join(self.output_dir, 'yara_concatenated.yar')
            yara_file = open(yara_path, 'w')

            logger.info(f'Concatenating rules in: {yara_path}...')

            counter_rule_file = 0
            for dirpath,_,filenames in os.walk(self.yara_input):
                for f in filenames:
                    full_path = os.path.abspath(os.path.join(dirpath, f))
                    if full_path == yara_path:
                        continue
                    with open(full_path, 'r') as read_file:
                        shutil.copyfileobj(read_file, yara_file)
                    counter_rule_file = counter_rule_file + 1

            yara_file.close()

            logger.info(f'{counter_rule_file} rule files concatenated in a single rule file')

        return yara_path

    """
    Download Velocidex yara-tools from github for Windows or Linux depending on the current OS.
    """
    def __download_yaratool(self) -> str:
        URL_WINDOWS = 'https://github.com/Velocidex/yara-tools/releases/download/v0.2/yara_tool_0.2_windows.exe'
        URL_LINUX = 'https://github.com/Velocidex/yara-tools/releases/download/v0.2/yara_tool_0.2_linux'

        yaratool_url = ''
        if os.name == 'nt':
            yaratool_url = URL_WINDOWS
        elif os.name == 'posix':
            yaratool_url = URL_LINUX
        else:
            logger.error(f'Building on unsupported os: {os_version}')
            exit(1)

        binary_name = os.path.basename(yaratool_url)
        output_path = os.path.join(self.output_dir, binary_name)

        if os.path.isfile(output_path):
            logger.success(f'Velocidex yara-tools binary already present in \'{output_path}\'...')
        else:
            logger.info(f'Downloading Velocidex yara-tools from \'{yaratool_url}\'...')
            r = requests.get(yaratool_url, allow_redirects=True)
            open(output_path, 'wb').write(r.content)
            logger.success(f'Downloaded Velocidex yara-tools to \'{output_path}\'!')

        return output_path

    """
    Remove the yara rules metadata and validate them for Velociraptor using Velocidex yara-tools.
    """
    def __clean_yara(self, yaratools_binary, yara_path) -> str:
        if os.name == 'nt' and ' ' in yaratools_binary:
            cleaning_cmd = f'{os.environ.get("ComSpec", "cmd.exe")} /v:on /c "(start "" /wait "{yaratools_binary} clean --verify {yara_path}") & exit !errorlevel!"'
            logger.info(f'Cleaning yara rules with command: \'{cleaning_cmd}\'')
            process = subprocess.run(cleaning_cmd, shell=True, capture_output=True)
        else:
            cleaning_cmd = f'{yaratools_binary} clean --verify {yara_path}'
            logger.info(f'Cleaning yara rules with command: \'{cleaning_cmd}\'')
            process = subprocess.run(shlex.split(cleaning_cmd, posix="win" not in sys.platform), shell=False, capture_output=True)

        yara_clean_path = os.path.join(self.output_dir, 'yara_clean.yar')
        with open(yara_clean_path, 'wb+') as write_file:
            write_file.write(process.stdout)

        if process.returncode == 0:
            logger.success(f'Yara rules cleaned using Velocidex yara-tools: \'{yara_clean_path}\'')
        else:
            logger.error(f'Yara rules could not be cleaned using Velocidex yara-tools: \'{process.stderr.decode("utf-8").strip()}\'')

        return yara_clean_path

    def create_config(self) -> str:
        yaratools_binary = self.__download_yaratool()
        yara_clean = self.__clean_yara(yaratools_binary, self.__concat_yara())

        yara_rules = ''
        with open(yara_clean, 'r') as read_file:
            yara_rules = read_file.read()

        # Oneline the rules and escape double quotes.
        yara_rules = yara_rules.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\r\\n')

        with open(self.template, 'r') as template_file:
            template_content = template_file.read()

        logger.info(f'Template file will be \'{self.template}\'')

        parametrized = template_content.replace('__yara__', yara_rules).replace('<PASSWORD>', self.zip_password)

        with open(self.output_config, 'w+') as output_file:
            output_file.write(parametrized)

        return self.output_config

    def create_collector(self):
        VelociraptorPacker.build_collector(self.target_os, self.output_config, self.output_binary, tools_csv=self.tools_csv)
