#! /usr/bin/python

import getopt
import sys

from ovirtsdk.api import API
from ovirtsdk.xml.params import Action
from ovirtsdk.xml.params import Ip
from ovirtsdk.xml.params import IpAddressAssignment
from ovirtsdk.xml.params import IpAddressAssignments
from ovirtsdk.xml.params import NetworkAttachment
from ovirtsdk.xml.params import NetworkAttachments


def usage():
    prog_name = sys.argv[0]
    print('\n%s -l <url> -u <username> -p <password> -c <cert_file>' % prog_name)
    print('OR')
    print('%s --url=<url> --username=<username> --password=<password> --certfile=<cert_file path>\n' % prog_name)
    sys.exit(-1)


def process_opts():
    opts, args = getopt.getopt(args=sys.argv[1:],
                               shortopts='hl:u:p:c',
                               longopts=['url=', 'username=', 'password=', 'certfile='])

    url = username = password = cert_file = None

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ('-l', '--url'):
            url = arg
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-c', '--certfile'):
            cert_file = arg
        else:
            print('Unknown parameter: %s' % opt)

    if url and username and password:
        return url, username, password, cert_file

    usage()


def print_nics(nics):
    for nic in nics:
        print('Nic: %s' % nic.name)


def main():
    api_url, username, password, cert_file = process_opts()

    api = API(url=api_url,
              username=username,
              password=password,
              cert_file=cert_file)
    print('Connected to %s' % api_url)

    host = api.hosts.get(name='nari05')
    network_name = 'test1'
    nic_name = 'enp2s16f3'

    network = api.networks.get(name=network_name)
    nic = host.nics.get(name=nic_name)

    host.setupnetworks(Action(
        async=False,
        force=False,
        check_connectivity=True,
        host_nics=None,
        modified_network_attachments=
        NetworkAttachments(network_attachment=[NetworkAttachment(
            network=network,
            host_nic=nic,
            ip_address_assignments=IpAddressAssignments(
                [IpAddressAssignment(assignment_method='DHCP', ip=Ip(version='v4'))]))]
        )
    ))

    api.disconnect()


if __name__ == '__main__':
    main()
