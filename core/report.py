# core/report.py
# Copyright (C) 2015 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

"""Exception-reporting and bug reporting stuff. This should probably be
refactored and given a better module name.

"""

import platform

import psutil


def hardware_info():
    """Returns a dictionary with the following key-value pairs containing
    relating to the user's machine.

    Note: maximum partition size is retrieved as part of :func:`runtime_info`
    despite being a static characteristic.

    """
    info = dict()
    info['arch'] = platform.architecture()
    info['cpu'] = platform.processor()
    info['num_cpus'] = psutil.NUM_CPUS
    mem = psutil.virtual_memory()
    info['total_memory'] = mem[0]
    discs = [(device, fstype) for device, _, fstype, _ in psutil.disk_partitions()]
    info['discs'] = {device: fstype for device, fstype in discs}
    return info


def software_info():
    """Returns a dictionary containing software-related info."""
    info = dict()
    info['python'] = "Python %s (compiled with %s)" % (platform.python_version(), platform.python_compiler())
    if platform.system() == 'Windows':
        release, version, _, _ = platform.win32_ver()
        info['os'] = "Windows %s (%s)" % (release, version)
    elif platform.system() == 'Darwin':
        version, _, _ = platform.mac_ver()
        info['os'] = "OS X %s" % version
    elif platform.system() == 'Linux':
        # Slackware leaves the third item empty; Linux Mint has all three. So
        # since there exists some inconsistency we'll just grab all three values
        # to ensure we get everything we need.
        info['os'] = "%s %s %s" % platform.linux_distribution()
    else:
        raise NotImplementedError
    return info


def runtime_info():
    info = dict()
    info['uptime'] = psutil.get_boot_time()
    return info
