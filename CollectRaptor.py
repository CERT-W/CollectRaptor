# -*- coding: UTF-8 -*-

import argparse
import os
import sys

from loguru import logger

from builder.LinuxFromForensicArtifacts import LinuxFromForensicArtifacts
from builder.WindowsFromKapeTargets import WindowsFromKapeTargets
from helpers.arguments import add_ForensicArtifacts_args
from helpers.enum import OsArchitecture, OsSimpleName

from helpers.VelociraptorPacker import VelociraptorPacker

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))

    logger.remove(0)
    logger.add(sys.stderr, format='{time:YYYY-MM-DDTHH:mm:ssZ} <level>[{level}] {message}</level>', colorize=True)

    args_parser = argparse.ArgumentParser(prog='CollectRaptor')

    # Common args.
    args_parser.add_argument('-t', '--template',
                             dest='template',
                             help='Template file to parametrize')
    args_parser.add_argument('--tools-csv',
                             dest='tools_csv',
                             help='CSV file containing the tools to download')
    args_parser.add_argument('-o', '--output',
                             dest='output',
                             help='Output directory for the config file and packed Velociraptor binary')
    args_parser.add_argument('--only-conf',
                             dest='only_conf',
                             help='Only generate a config file, not the packed Velociraptor binary')
    args_parser.add_argument('-p', '--password',
                             dest='zip_password',
                             default='<PASSWORD>',
                             help='Password for the encrypted zip produced by the collector. Defaults to \'<PASSWORD>\'')

    # Common args - Velociraptor packer.
    # args_parser.add_argument('--velo-path',
    #                          dest='velo_path',
    #                          help='Path to a folder containing the Velociraptor binaries to use for packing the collector')

    subparsers = args_parser.add_subparsers(dest='target_os',
                                            required=True,
                                            help='Target operating system')

    # Subparser for Windows.
    parser_windows = subparsers.add_parser(OsSimpleName.Windows.value)
    parser_windows_subparsers = parser_windows.add_subparsers(dest='artifacts_set')
    parser_windows_subparsers.add_parser('kape_light')
    parser_windows_subparsers.add_parser('kape_full')
    parser_windows_subparsers.add_parser('kape_dc')
    parser_windows.add_argument('-a', '--architecture',
                                choices=['x86', 'x64'],
                                default='x64',
                                help='Target operating system architecture',
                                dest='os_architecture')
    # Subparser for Linux.
    parser_linux = subparsers.add_parser(OsSimpleName.Linux.value)
    parser_linux_subparsers = parser_linux.add_subparsers(dest='artifacts_set')
    parser_linux.add_argument('-a', '--architecture',
                              choices=['x64'],
                              default='x64',
                              help='Target operating system architecture',
                              dest='os_architecture')

    parser_linux_forensic_artifacts = parser_linux_subparsers.add_parser('forensic_artifacts')
    add_ForensicArtifacts_args(parser_linux_forensic_artifacts)

    args = args_parser.parse_args()

    if args.artifacts_set is None:
        if args.target_os == OsSimpleName.Windows.value:
            parser_windows.print_help()
        elif args.target_os == OsSimpleName.Linux.value:
            parser_linux.print_help()
        exit(1)

    if args.tools_csv and not os.path.isfile(args.tools_csv):
        logger.error(f"'{args.tools_csv}' does not exist / is not a valid file.")
        exit(1)

    collector_builder = None

    # Process Windows target OS.
    if args.target_os == OsSimpleName.Windows.value:
        target_os = OsArchitecture.Windows_x64 if args.os_architecture == 'x64' else OsArchitecture.Windows_x86

        if args.artifacts_set.startswith('kape'):
            collector_builder = WindowsFromKapeTargets(target_os,
                                                       args.artifacts_set,
                                                       args.zip_password,
                                                       output_dir=args.output,
                                                       tools_csv=args.tools_csv)

    elif args.target_os == OsSimpleName.Linux.value:
        target_os = OsArchitecture.Linux_x64

        if args.artifacts_set == 'forensic_artifacts':
            collector_builder = LinuxFromForensicArtifacts(target_os,
                                                           args.zip_password,
                                                           yaml_urls=args.yaml_urls,
                                                           yaml_files=args.yaml_files,
                                                           template=args.template,
                                                           output_dir=args.output)

    config_file_path = collector_builder.create_config()

    logger.success(f'Collector configuration file written to \'{config_file_path}\'')

    if args.only_conf:
        logger.info(f'Command to build the Velociraptor collector: \'velociraptor config repack {os.path.basename(config_file_path)} <OUTPUT_BINARY> \'')
    else:
        collector_builder.create_collector()
