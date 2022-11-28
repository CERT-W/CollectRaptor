# -*- coding: UTF-8 -*-

import os
import pathlib
import shutil

from helpers.enum import OsArchitecture
from helpers.VelociraptorPacker import VelociraptorPacker


class WindowsFromKapeTargets:
    def __init__(self, target_os: OsArchitecture, artifacts_set: str, output_dir: str = None, tools_csv: str = None):
        self.target_os = target_os
        self.artifacts_set = artifacts_set

        base_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent

        output_dir = output_dir if output_dir else os.path.join(base_dir, 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        self.template = None
        self.output_config = None
        self.output_binary = None
        self.tools_csv = tools_csv if tools_csv else os.path.join(base_dir,
                                                                  'templates',
                                                                  'Windows_collector_tools.csv')

        if self.artifacts_set == 'kape_light':
            self.template = os.path.join(base_dir,
                                         'templates',
                                         'Windows_collector_KAPE_light.template')
            self.output_config = os.path.join(output_dir,
                                              'Windows_collector_KAPE_light.yaml')
            self.output_binary = os.path.join(output_dir,
                                              'Windows_collector_KAPE_light.exe')

        elif self.artifacts_set == 'kape_full':
            self.template = os.path.join(base_dir,
                                         'templates',
                                         'Windows_collector_KAPE_full.template')
            self.output_config = os.path.join(output_dir,
                                              'Windows_collector_KAPE_full.yaml')
            self.output_binary = os.path.join(output_dir,
                                              'Windows_collector_KAPE_full.exe')


    def create_config(self) -> str:
        shutil.copyfile(self.template, self.output_config)
        return self.output_config


    def create_collector(self):
        VelociraptorPacker.build_collector(self.target_os, self.output_config, self.output_binary, tools_csv=self.tools_csv)
