#!/usr/bin/env python

import re
import sys

def append_new_vm_in_dns_zone(zone_file, hostname, VM_IP):
    path = "/var/named/master/"
    print "Check hostname %s in zone file %s" % (hostname,zone_file)
    if(not is_vm_existed(hostname, zone_file)):
        # example: hostname1          IN      A       ip1
        new_record = str(hostname) + "\tIN\tA\t" + str(VM_IP) + "\n"
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
    if (len(sys.argv) < 4):
        print "Need 3 parameters!. Quit!"
        quit()

    original_zone_file = str(sys.argv[1])
    vm_hostname = str(sys.argv[2])
    VM_IP = str(sys.argv[3])
    append_new_vm_in_dns_zone(original_zone_file, vm_hostname, VM_IP)
