# -*- coding: UTF-8 -*-

import requests
import yaml

from loguru import logger


class ForensicArtifactsHelper:

    # Retrieve the artifacts from the specified YAML files.
    @staticmethod
    def load_yaml_from_files(yaml_files: list) -> list:
        yamls_loaded = list()

        for yaml_file in yaml_files:
            logger.info(f'Adding artifacts YAML definition from file \'{yaml_file}\'')
            with open(yaml_file, 'r') as f:
                yamls_loaded.append(f.read())

        return yamls_loaded


    @staticmethod
    def download_yaml(yaml_url: str) -> str:
        req = requests.get(yaml_url)

        if req.status_code != 200:
            logger.error(f'Failed to retrieve the artifacts from \'{yaml_url}\', status code: {req.status_code}')
            return ''

        return req.content.decode('utf-8')


    @staticmethod
    def download_yamls(yaml_urls: list) -> list:
        yamls_downloaded = list()

        for yaml_url in yaml_urls:
            logger.info(f'Downloading artifacts ForensicArtifacts YAML definition from \'{yaml_url}\'')
            yamls_downloaded.append(ForensicArtifactsHelper.download_yaml(yaml_url))

        return yamls_downloaded


    @staticmethod
    def parse_yaml(artifact_yaml: str, target_os: str = None, target_type: str = 'FILE') -> list:
        try:
            artifact_yaml = yaml.safe_load_all(artifact_yaml)
        except Exception as e:
            logger.error(f'Failed to parse yaml, error: {e}')
            exit(-1)

        artifact_list = list()
        for artifact in artifact_yaml:
            if target_os is not None and 'supported_os' in artifact and target_os not in artifact['supported_os']:
                continue

            for source in artifact['sources']:
                if source['type'] == target_type and \
                   (target_os is None or 'supported_os' not in source or target_os in source['supported_os']):
                    artifact_list.extend(source['attributes']['paths'])

        return artifact_list
