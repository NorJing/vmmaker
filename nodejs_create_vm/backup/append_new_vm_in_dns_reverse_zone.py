#!/usr/bin/env python

import re
import sys

def append_new_vm_in_dns_reverse_zone(zone_file, hostname, VM_IP, FQDN):
    # bind-9.9.4-51.el7.x86_64
    path = "/var/named/master/"
    print "Check hostname %s in zone file %s" % (hostname,zone_file)
    if(not is_vm_existed(hostname, zone_file)):
        # example: 253     IN      PTR     fqdn
        the_third_ip_digital = VM_IP.split(".")[3]
        new_record = str(the_third_ip_digital) + "\tIN\tPTR\t" + str(FQDN) + ".\n"
        try:
            with open(zone_file, 'a') as file:
                file.write(new_record)
                print "append host=" + hostname
        except IOError:
            print "append fails"

def is_vm_existed(hostname, zone_file):
    vm_existed = None
    try:
        with open(zone_file, 'r') as file:
            for line in file:
                 if str(hostname) in line:
                     print "vm is already in zone file"
                     vm_existed = True
                     break
    except IOError:
         print "can not open file!"

    if vm_existed is None:
        print "vm is not in zone file. append"
        vm_existed = False

    return vm_existed

if __name__ == '__main__':
    if (len(sys.argv) < 5):
        print "Need 4 parameters!. Quit!"
        quit()

    original_zone_file = str(sys.argv[1])
    vm_hostname = str(sys.argv[2])
    VM_IP = str(sys.argv[3])
    FQDN = str(sys.argv[4])
    append_new_vm_in_dns_reverse_zone(original_zone_file, vm_hostname, VM_IP, FQDN)
