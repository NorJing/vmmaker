#!/usr/bin/env python

import re
import sys

def update_dns_zone_serial(original_zone_file):
    path = "/var/named/master/"
    path_backup = "/root/named_master_backup/"
    new_zone_file = path + original_zone_file
    original_zone_file = path_backup + original_zone_file
    print "org_zone_file=%s" % original_zone_file
    print "new_zone_file=%s" % new_zone_file
    try:
        with open(original_zone_file, 'r') as file:
            with open(new_zone_file,'w') as new_file:
                for line in file:
                    if "serial" in line:
                        # \s+(\d+)(\s+)?;\sserial\s
                        the_line = re.match(r'(\s+)(\d+)(\s+)?(;\sserial\s.*)', line, re.M|re.I)
                        if the_line:
                            serial_number = "{0}".format(the_line.group(2))
                            print "original serial number=%s" % serial_number
                            print "original line=%s" % line.rstrip()
                            new_serial_number = int(serial_number) + 1
                            print "     new serial number=%s" % new_serial_number
                            if the_line.group(3) is None:
                                new_line = "{0}{1}{2}".format(the_line.group(1), new_serial_number, the_line.group(4))
                            else:
                                new_line = "{0}{1}{2}{3}".format(the_line.group(1), new_serial_number, the_line.group(3), the_line.group(4))
                                print "     new line=%s" % new_line
                            # write to new file
                            new_file.write(str(new_line))
                        else:
                            print "no serial line match!"
                    else:
                        new_file.write(str(line))
    except IOError:
        print "can not open file!"


if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Need 2 parameters!. Quit!"
        quit()

    original_zone_file = str(sys.argv[1])
    update_dns_zone_serial(original_zone_file)
