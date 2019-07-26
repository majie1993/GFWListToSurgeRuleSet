#!/usr/bin/env python
# encoding: utf-8

# Original code from https://github.com/cloverstd/GFWList2Surge

from __future__ import absolute_import, unicode_literals

import logging
from urllib.parse import urlparse
from urllib.request import urlopen
import base64

__all__ = ['main']

gfwlist_url = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'

def get_data_from_file(file_path):
    with open(file_path, 'rb') as f:
        builtin_rules = f.read()
        return builtin_rules


def get_hostname(something):
    try:
        # quite enough for GFW
        if not something.startswith('http:'):
            something = 'http://' + something
        r = urlparse(something)
        return r.hostname
    except Exception as e:
        logging.error(e)
        return None


def add_domain_to_set(s, something):
    hostname = get_hostname(something)
    if hostname is not None:
        s.add(hostname)


def combine_lists(content, user_rule=None):
    content = base64.decodebytes(content).decode("utf-8")
    gfwlist = content.splitlines(False)
    if user_rule:
        gfwlist.extend(user_rule.splitlines(False))
    return gfwlist


def parse_gfwlist(gfwlist):
    domains = set()
    for line in gfwlist:
        if line.find('.*') >= 0:
            continue
        elif line.find('*') >= 0:
            line = line.replace('*', '/')
        if line.startswith('||'):
            line = line.lstrip('||')
        elif line.startswith('|'):
            line = line.lstrip('|')
        elif line.startswith('.'):
            line = line.lstrip('.')
        if line.startswith('!'):
            continue
        elif line.startswith('['):
            continue
        elif line.startswith('@'):
            # ignore white list
            continue
        add_domain_to_set(domains, line)
    return domains


def reduce_domains(domains):
    # reduce 'www.google.com' to 'google.com'
    # remove invalid domains
    tld_content = get_data_from_file("resources/tld.txt").decode("utf-8")
    tlds = set(tld_content.splitlines(False))
    new_domains = set()
    for domain in domains:
        domain_parts = domain.split('.')
        last_root_domain = None
        for i in range(0, len(domain_parts)):
            root_domain = '.'.join(domain_parts[len(domain_parts) - i - 1:])
            if i == 0:
                if not tlds.__contains__(root_domain):
                    # root_domain is not a valid tld
                    break
            last_root_domain = root_domain
            if tlds.__contains__(root_domain):
                continue
            else:
                break
        if last_root_domain is not None:
            new_domains.add(last_root_domain)
    return new_domains


def main():
    print('Downloading gfwlist from %s' % gfwlist_url)
    content = urlopen(gfwlist_url, timeout=10).read()

    gfwlist = combine_lists(content)
    domains = parse_gfwlist(gfwlist)
    domains = reduce_domains(domains)
    domains = "DOMAIN-SUFFIX," + "\nDOMAIN-SUFFIX,".join(domains)
    print(domains)

    with open('resources/GFWList.list', 'wb') as f:
        f.write(domains.encode("UTF-8"))


if __name__ == '__main__':
    main()
