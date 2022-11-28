# -*- coding: UTF-8 -*-

from enum import Enum


class OsArchitecture(Enum):
    Windows_x86 = 'Windows-i386'
    Windows_x64 = 'Windows-AMD64'
    Linux_x64 = 'Linux-x86_64'


class OsSimpleName(Enum):
    Windows = 'Windows'
    Linux = 'Linux'
