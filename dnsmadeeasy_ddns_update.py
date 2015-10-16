#!/usr/bin/env python
#
# Script to update dynamic DNS records at DNSMadeEasy.com with HTTPS support.
# Put your settings in settings.json in the same folder with the script 
# and set to run from cron.
#
# Requires following non-core modules;
#  * python-requests, https://pypi.python.org/pypi/requests/
#  * python-dns, https://pypi.python.org/pypi/dnspython/
#
# Original Author: Pekka Wallendahl <wyrmiyu@gmail.com>
#
# Author: Painful Cranium Consulting, LLC ( Chris Haubner<chaubner@painfulcranium.com> )
# Date Modified:
# 06/03/2015
#
# Notes:
# Forked from original author and updated to allow multi record JSON to be used
# so many records could be updated at once.
#
# If you find this useful, please drop me a line and let
# me know how this has helped you :)
#
# License: MIT, https://github.com/painfulcranium/dnsmadeeasy_api_updater/blob/master/LICENSE

from __future__ import print_function

import socket
import json
import logging
import os
import sys
import argparse
import requests
import dns.resolver

logging.basicConfig(format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def error(message):
    """
    Log an error and exit.
    """
    logger.error(message)
    sys.exit(1)


def check_ssl(url):
    try:
        requests.get(url, verify=True)
    except requests.exceptions.SSLError:
        error('The SSL certificate for %s is not valid.' % (url))


def get_current_ip(url):
    url = url
    try:
        return requests.get(url).text.strip()
    except requests.ConnectionError:
        logger.debug('Could not get the current IP from %s' % (url))


def get_dns_ip(name, target='A'):
    name = name
    bits = name.split('.')
    while bits:
        try:
            ns = str(dns.resolver.query('.'.join(bits), 'NS')[0])
        except:
            bits.pop(0)
        else:
            ns = socket.gethostbyname(ns)
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [ns]
            q = resolver.query(name, target)
            ip = str(q[0]).strip()
            return ip
    error('Could not get the authoritative name server for %s.' % (name))


def update_ip_to_dns(ip, url, username, record_id, record_password):
    url = url
    check_ssl(url)
    params = {
        'username': username,
        'password': record_password,
        'id': record_id,
        'ip': ip,
    }
    return requests.get(url, params=params)

# Constants
BASE_DIR = os.path.dirname(__file__)
GET_IP_URL = 'http://www.dnsmadeeasy.com/myip.jsp'
UPDATE_IP_URL = 'https://www.dnsmadeeasy.com/servlet/updateip'
LOG_LEVEL = 'DEBUG'

try:
    logger.setLevel(LOG_LEVEL)
except ValueError:
    logger.error('Invalid `LOG_LEVEL`. Valid levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL.')
    sys.exit(1)

if __name__ == '__main__':

        parser = argparse.ArgumentParser()
        parser.add_argument('--jsonConfig', type=str, help='Configuration file in current directory', required=True)
        parser.add_argument('--jsonKey', type=str, help='JSON Dict Key to use', required=True)
        args = parser.parse_args()

        # file and key arguments
        jsonConfigFile = os.path.join(BASE_DIR, args.jsonConfig)
        jsonConfigKey = args.jsonKey

        # Default exit code if everything works
        exitCode = 0

        # Iterate over this for EACH record in the JSON
        try:

            current_ip = get_current_ip(GET_IP_URL)
            if current_ip:
                # ToDo: Add ability to pass entry name and file to the script
                jsonSettingsFile = json.loads(open(jsonConfigFile).read())
                isValidJson = True

                # Iterate over this for EACH record in the JSON. One error and we stop
                for index, entry in enumerate(jsonSettingsFile[jsonConfigKey]):
                    # set defaults
                    username = ''
                    record_password = ''
                    record_name = ''
                    record_id = ''

                    # Validate JSON very non-elegantly :)
                    for opt in 'USERNAME', 'RECORD_PASSWORD', 'RECORD_ID', 'RECORD_NAME':
                        if opt not in entry:
                            isValidJson = False
                            # Set exit code here for easier finding
                            exitCode = 3

                            # Do not output entry as it contains username and/or password info and should
                            # not be logged anywhere!!! This will log errors
                            logger.error('Missing %s setting in entry number %s. '
                                         'Check json configuration file %s.'
                                         % (opt, index + 1, os.path.join(BASE_DIR, jsonConfigFile)))

                    if isValidJson:
                        # Set the variables we need, and then pass them to the function
                        username = entry['USERNAME']
                        record_password = entry['RECORD_PASSWORD']
                        record_name = entry['RECORD_NAME']
                        record_id = entry['RECORD_ID']
                        dns_ip = get_dns_ip(record_name)

                        if current_ip != dns_ip:

                            logger.debug('Current IP %s differs with DNS record %s, '
                                         'attempting to update DNS.' % (current_ip, dns_ip))
                            request = update_ip_to_dns(current_ip, UPDATE_IP_URL, username, record_id, record_password)

                            if request and request.text == 'success':
                                logger.info('Updating record for %s to %s was successful.' % (record_name, current_ip))
                            else:
                                logger.error('Updating record for %s to %s failed.' % (record_name, current_ip))

                        else:
                            logger.info('No changes for DNS record %s to report.' % record_name)

        except IOError:
            logger.error('No json config file found %s. Please try again or Create one from '
                         'the `settings.json.singlerecord.sample` or '
                         '`settings.json.multirecord.sample` file.' % jsonConfigFile)
            sys.exit(1)

        except ValueError:
            error('Invalid json Config File. Check the '
                  '`settings.json.singlerecord.sample` or `settings.json.multirecord.sample` '
                  'file for an example.')
            sys.exit(1)

        sys.exit(exitCode)
