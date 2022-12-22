# -*- coding: UTF-8 -*-

import os
import pathlib

from loguru import logger

from helpers.enum import OsArchitecture
from helpers.ForensicArtifactsHelper import ForensicArtifactsHelper
from helpers.VelociraptorPacker import VelociraptorPacker


class LinuxFromForensicArtifacts:
    def __init__(self, target_os: OsArchitecture, zip_password: str, yaml_files: list = None, yaml_urls: str = None, template: str = None, output_dir: str = None):
        self.target_os = target_os
        self.zip_password = zip_password

        self.yaml_files = yaml_files
        self.yaml_urls = yaml_urls if yaml_urls else [
                'https://raw.githubusercontent.com/ForensicArtifacts/artifacts/main/data/linux.yaml',
                'https://raw.githubusercontent.com/ForensicArtifacts/artifacts/main/data/unix_common.yaml',
                'https://raw.githubusercontent.com/ForensicArtifacts/artifacts/main/data/shell.yaml',
                'https://raw.githubusercontent.com/ForensicArtifacts/artifacts/main/data/linux_proc.yaml',
                'https://raw.githubusercontent.com/ForensicArtifacts/artifacts/main/data/linux_services.yaml'
        ]

        base_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
        output_dir = output_dir if output_dir else os.path.join(base_dir, 'outputs')
        os.makedirs(output_dir, exist_ok=True)

        self.template = template if template else os.path.join(base_dir,
                                                               'templates',
                                                               'Linux_collector.template')

        self.output_config = os.path.join(output_dir, 'Linux_collector.yaml')
        self.output_binary = os.path.join(output_dir, 'Linux_collector')


    def __transform_artifacts(self, artifact_list) -> list:
        for index, elt in enumerate(artifact_list):
            if '%%users.homedir%%' in elt:
                artifact_list[index] = elt.replace('%%users.homedir%%', '/home/*')
                artifact_list.append(elt.replace('%%users.homedir%%', '/root'))

            if '%%users.localappdata%%' in elt:
                artifact_list[index] = elt.replace('%%users.localappdata%%', '/home/**')
                artifact_list.append(elt.replace('%%users.localappdata%%', '/root/**'))

        return artifact_list


    def create_config(self) -> str:
        yaml_list = list()
        artifact_set = set()

        if self.yaml_files is not None:
            yaml_list.extend(ForensicArtifactsHelper.load_yaml_from_files(self.yaml_files))

        if self.yaml_urls is not None:
            yaml_list.extend(ForensicArtifactsHelper.download_yamls(self.yaml_urls))

        for yaml in yaml_list:
            artifact_set.update(self.__transform_artifacts(ForensicArtifactsHelper.parse_yaml(yaml, target_os='Linux')))

        logger.success(f'Retrieved {len(artifact_set)} artifacts paths!')

        with open(self.template, 'r') as template_file:
            template_content = template_file.read()

        logger.info(f'Template file will be \'{self.template}\'')

        parametrized = template_content.replace('___files___', r'\n'.join(artifact_set)).replace('<PASSWORD>', self.zip_password)

        with open(self.output_config, 'w+') as output_file:
            output_file.write(parametrized)

        return self.output_config


    def create_collector(self):
        VelociraptorPacker.build_collector(self.target_os, self.output_config, self.output_binary)
