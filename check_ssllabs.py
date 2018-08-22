#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# check_ssllabs.py - A check plugin for SSLLabs score.
# Copyright (C) 2018  Nicolai Buchwitz <nb@tipi-net.de>
#
# Version: 0.1.0
#
# ------------------------------------------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# ------------------------------------------------------------------------------

from __future__ import print_function
import sys

try:
    from enum import Enum
    import argparse
    import json
    import requests
    import urllib3
    import signal
    import time

    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

except ImportError as e:
    print("Missing python module: {}".format(e.message))
    sys.exit(255)


class NagiosState(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class CheckSSLLabs:
    VERSION = '0.1.0'
    API_URL = "https://api.ssllabs.com/api/v2/{}"

    options = {}

    def output(self, returnCode, message):
        prefix = returnCode.name

        message = '{} - {}'.format(prefix, message)

        print(message)
        sys.exit(returnCode.value)

    def get_url(self, part):
        return self.API_URL.format(part)

    def request(self, url, **kwargs):
        response = None
        try:
            response = requests.get(
                url,
                params=kwargs.get('params', None)
            )

        except requests.exceptions.ConnectTimeout:
            self.output(NagiosState.UNKNOWN, "Could not connect to ssllabs: Connection timeout")
        except requests.exceptions.SSLError:
            self.output(NagiosState.UNKNOWN, "Could not connect to ssllabs: Certificate validation failed")
        except requests.exceptions.ConnectionError:
            self.output(NagiosState.UNKNOWN, "Could not connect to ssllabs: Failed to resolve hostname")

        if response.ok:
            return response.json()
        else:
            message = "Could not fetch data from API: "
            message += "HTTP error code was {}".format(response.status_code)

        self.output(NagiosState.UNKNOWN, message)

    def check(self):
        url = self.get_url('analyze')
        params = {'host': self.options.domainname, 'publish': self.options.publish}

        if self.options.cached:
            extra_params = {'fromCache': 'on', 'maxAge': self.options.max_age}
        else:
            extra_params = {'startNew': 'on'}
        params.update(extra_params)

        # Initial fetch of the test results
        data = self.request(url, params=params)

        # Pop extra params, because we only want the results and no new test
        all(map(params.pop, extra_params))

        # Set timeout handler
        signal.signal(signal.SIGALRM,
                      lambda signum, frame: self.output(NagiosState.CRITICAL, "Timeout while waiting for test results"))
        signal.alarm(self.options.timeout)

        while 1:
            if data['status'] in ['READY', 'ERROR']:
                break

            time.sleep(10)
            data = self.request(url, params=params)
            print(data['status'])

        # Remove timeout handler
        signal.alarm(0)

        if data['status'] == 'ERROR':
            self.output(NagiosState.CRITICAL, "Check failed: {}".format(data['statusMessage']))

        worst_grade = None
        found = not self.options.ip_address
        for endpoint in data['endpoints']:
            if self.is_worse(worst_grade, endpoint['grade']):
                worst_grade = endpoint['grade']

            if self.options.ip_address and endpoint['ipAddress'] == self.options.ip_address:
                found = True
                break

        if not found:
            self.output(NagiosState.CRITICAL, "IP address '{}' not found in test results of domain '{}'".format(self.options.ip_address, self.options.domainname))

        result = NagiosState.OK
        if self.is_worse(self.options.treshold_critical, worst_grade):
            result = NagiosState.CRITICAL
        elif self.is_worse(self.options.treshold_warning, worst_grade):
            result = NagiosState.WARNING

        self.output(result, "SSLLabs score for domain '{}' is {}".format(self.options.domainname, worst_grade))

        print(json.dumps(data, indent=4, sort_keys=True))

    @staticmethod
    def is_worse(a, b):
        if not a:
            return True
        elif not b:
            return False

        if a and b and a[0] == b[0]:
            return a > b
        else:
            return a < b

    def parse_options(self):
        p = argparse.ArgumentParser(description='Check command SSLLabs score monitoring')

        p.add_argument("-d", required=True, help="Domainname to test", dest='domainname')
        p.add_argument("-i", help="IP to test when the host has more than one endpoint", dest='ip_address')
        p.add_argument("-p", action='store_true', default=False, help="Publish the results", dest='publish')
        p.add_argument("--no-cache", action='store_false', default=True, help="Do not accept cached results",
                       dest='cached')
        p.add_argument("--cache-hours", type=int, default=2, help="Max age of cached results (hours)", dest='max_age')
        p.add_argument("--timeout", type=int, default=240, help="Timeout for test results in seconds", dest='timeout')

        p.add_argument('-w', dest='treshold_warning', default='B',
                       help='Warning treshold for check value')
        p.add_argument('-c', dest='treshold_critical', default='C',
                       help='Critical treshold for check value')

        options = p.parse_args()

        if self.is_worse(options.treshold_critical, options.treshold_warning):
            p.error("Treshold for warning has to be below critical")

        self.options = options

    def __init__(self):
        self.parse_options()


ssllabs = CheckSSLLabs()
ssllabs.check()
