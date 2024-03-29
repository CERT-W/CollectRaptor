# -*- coding: UTF-8 -*-

import os
import pathlib
import shutil

from loguru import logger

from helpers.enum import OsArchitecture
from helpers.VelociraptorPacker import VelociraptorPacker


class WindowsFromKapeTargets:
    def __init__(self, target_os: OsArchitecture, artifacts_set: str, zip_password: str, output_dir: str = None, tools_csv: str = None):
        self.target_os = target_os
        self.artifacts_set = artifacts_set
        self.zip_password = zip_password

        base_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent

        output_dir = output_dir if output_dir else os.path.join(base_dir, 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        self.template = None
        self.output_config = None
        self.output_binary = None
        self.tools_csv = tools_csv

        if self.artifacts_set == 'kape_light':
            self.template = os.path.join(base_dir,
                                         'templates',
                                         'Windows_collector_KAPE_light.template')
            self.output_config = os.path.join(output_dir,
                                              'Windows_collector_KAPE_light.yaml')
            self.output_binary = os.path.join(output_dir,
                                              'Windows_collector_light.exe')
            if not self.tools_csv:
                self.tools_csv = os.path.join(base_dir,
                                              'templates',
                                              'Windows_collector_KAPE_light_tools.csv')


        elif self.artifacts_set == 'kape_full':
            self.template = os.path.join(base_dir,
                                         'templates',
                                         'Windows_collector_KAPE_full.template')
            self.output_config = os.path.join(output_dir,
                                              'Windows_collector_KAPE_full.yaml')
            self.output_binary = os.path.join(output_dir,
                                              'Windows_collector_full.exe')
            if not self.tools_csv:
                self.tools_csv = os.path.join(base_dir,
                                              'templates',
                                              'Windows_collector_KAPE_full_tools.csv')

        elif self.artifacts_set == 'kape_dc':
            self.tools_csv = None
            self.template = os.path.join(base_dir,
                                         'templates',
                                         'Windows_collector_KAPE_ADDS_DC.template')
            self.output_config = os.path.join(output_dir,
                                              'Windows_collector_KAPE_ADDS_DC.yaml')
            self.output_binary = os.path.join(output_dir,
                                              'Windows_collector_DC.exe')


    def create_config(self) -> str:
        with open(self.template, 'r') as template_file:
            template_content = template_file.read()

        logger.info(f'Template file will be \'{self.template}\'')

        parametrized = template_content.replace('<PASSWORD>', self.zip_password)

        with open(self.output_config, 'w+') as output_file:
            output_file.write(parametrized)

        return self.output_config


    def create_collector(self):
        VelociraptorPacker.build_collector(self.target_os, self.output_config, self.output_binary, tools_csv=self.tools_csv)
