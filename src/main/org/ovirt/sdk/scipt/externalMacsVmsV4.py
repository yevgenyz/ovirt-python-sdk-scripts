#! /usr/bin/python
import getopt
import getpass
import os
import sys

from ovirtsdk4 import ConnectionBuilder
from ovirtsdk4.services import DataCentersService, VmsService, MacPoolsService, VmNicsService


def usage():
    prog_name = sys.argv[0]
    print('\n')
    print(prog_name)
    print('\t-l <url>, --url=<url>')
    print('\t-u <username>, --username=<username>')
    print('\t-c <cert_file>, --certfile=<cert_file path>')
    sys.exit(-1)


def process_opts():
    opts, args = getopt.getopt(args=sys.argv[1:],
                               shortopts='hl:u:c',
                               longopts=['url=', 'username=', 'certfile='])

    url = username = cert_file = None

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ('-l', '--url'):
            url = arg
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-c', '--certfile'):
            cert_file = arg
        else:
            print('Unknown parameter: %s' % opt)

    if url and username:
        return url, username, cert_file

    usage()


def mac2int(mac):
    return int(mac.replace(':', ''), 16)


def mac_pool2ranges(mac_pool):
    return [(mac2int(mac_range.from_), mac2int(mac_range.to))
            for mac_range in mac_pool.ranges]


def is_mac_in_pool(mac, mac_ranges):
    mac_int = mac2int(mac)
    for mac_range in mac_ranges:
        start, end = mac_range
        if start <= mac_int <= end:
            return True
    return False


def has_vm_external_mac(vm, mac_pool_ranges, vnics_loader):
    vnics = vnics_loader(vm)
    for vnic in vnics:
        mac_address = vnic.mac.address
        if mac_address:
            if not is_mac_in_pool(mac_address, mac_pool_ranges):
                print('WARN: MAC out of range - VM=%s\tvNIC=%s\tMAC=%s' % (vm.name, vnic.name, mac_address))
                return True
        else:
            print('WARN: VM=%s \tvnic=%s: vNIC has no MAC address' % (vm.name, vnic.name))
    return False


def iter_problematic_vms(connection):
    data_centers_service = DataCentersService(connection=connection, path='/datacenters')
    mac_pools_service = MacPoolsService(connection=connection, path='/macpools')
    vms_service = VmsService(connection=connection, path='/vms')

    def vnics_loader(_vm):
        return VmNicsService(connection, path='/vms/%s/nics' % _vm.id).list()

    data_centers = data_centers_service.list()
    for dc in data_centers:
        mac_pool = mac_pools_service.mac_pool_service(id=dc.mac_pool.id).get()
        mac_pool_ranges = mac_pool2ranges(mac_pool)

        vms = vms_service.list(search='datacenter=\"%s\"' % dc.name)
        for vm in vms:
            vm = vms_service.vm_service(vm.id).get()
            if has_vm_external_mac(vm, mac_pool_ranges, vnics_loader):
                yield vm


def build_search_criteria(vms, render_criteria):
    return 'VMs: ' + ' OR '.join([render_criteria(vm) for vm in vms])


def get_single_vm_criteria_by_name(vm):
    return 'name=\"%s\"' % vm.name


def get_single_vm_criteria_by_id(vm):
    return 'id=\"%s\"' % vm.id


def process(api_url, username, password, cert_file):
    connection = ConnectionBuilder(
        url=api_url,
        username=username,
        password=password,
        ca_file=cert_file,
        # debug=True
    ).build()

    problematic_vms = list(iter_problematic_vms(connection))

    connection.close()

    if problematic_vms:
        print(build_search_criteria(problematic_vms, get_single_vm_criteria_by_name))
        print(build_search_criteria(problematic_vms, get_single_vm_criteria_by_id))
    else:
        print('All MAC addresses are in range')


def get_password():
    password = os.getenv("OVIRT_PASSWORD")
    if not password:
        password = getpass.getpass("Please enter your password: ")
    return password


def main():
    api_url, username, cert_file = process_opts()

    password = get_password()

    process(api_url, username, password, cert_file)


if __name__ == '__main__':
    main()
