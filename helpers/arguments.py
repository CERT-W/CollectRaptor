# -*- coding: UTF-8 -*-

def add_ForensicArtifacts_args(parser):
    parser.add_argument('-u', '--url',
                        nargs='+',
                        dest='yaml_urls',
                        help='One or more URL(s) to retrieve YAML files from')

    parser.add_argument('-f', '--file',
                        nargs='+',
                        dest='yaml_files',
                        help='One or more artifacts YAML file(s)')
