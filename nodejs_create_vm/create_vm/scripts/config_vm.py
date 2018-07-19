#!/usr/bin/env python

import ssl
from pysphere import VIServer
import time
import sys
from pysphere import ToolsStatus
from getpass import getpass
from __builtin__ import str
import base64
from sys import argv

def update_dns_zone(original_zone_file, original_reverse_zone_file, vm, vm_hostname, vm_ip, fqdn, vm_username, vm_password, dns_config_path, dns_backup_path):
    CP="/usr/bin/cp"
    # USR_LOCAL_BIN_UPDATE_DNS_ZONE_SERIAL, USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_ZONE and USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_REVERSE
    # have to stay in DNS server
    USR_LOCAL_BIN_UPDATE_DNS_ZONE_SERIAL="/usr/local/bin/update_dns_zone_serial.py"
    USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_ZONE="/usr/local/bin/append_new_vm_in_dns_zone.py"
    USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_REVERSE="/usr/local/bin/append_new_vm_in_dns_reverse_zone.py"
    BIN_SYSTEMCTL="/bin/systemctl"
    USR_LOCAL_BIN_DIR="/usr/local/bin/"
    TMP="/tmp/"
    print "update dns information"
    vm.login_in_guest(user=vm_username, password=str(vm_password))
    print "zone_file=%s%s" % (dns_config_path, original_zone_file)
    vm.start_process(program_path=CP, args=[str(dns_config_path) + str(original_zone_file), str(dns_backup_path) + str(original_zone_file)], env=None, cwd=str(dns_config_path))
    time.sleep(2)
    # update serial number
    vm.start_process(program_path=USR_LOCAL_BIN_UPDATE_DNS_ZONE_SERIAL, args=[str(original_zone_file)], env=None, cwd=USR_LOCAL_BIN_DIR)
    time.sleep(2)
    # append new vm record
    vm.start_process(program_path=USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_ZONE, args=[str(original_zone_file), vm_hostname, vm_ip], env=None, cwd=str(dns_config_path))
    time.sleep(2)
    # update dns reverse file serial number
    print "reverse_zone_file=%s%s" % (dns_config_path, original_reverse_zone_file)
    vm.start_process(program_path=CP, args=[str(dns_config_path) + str(original_reverse_zone_file), str(dns_backup_path) + str(original_reverse_zone_file)], env=None, cwd=str(dns_config_path))
    time.sleep(2)
    vm.start_process(program_path=USR_LOCAL_BIN_UPDATE_DNS_ZONE_SERIAL, args=[str(original_reverse_zone_file)], env=None, cwd=USR_LOCAL_BIN_DIR)
    time.sleep(2)
    vm.start_process(program_path=USR_LOCAL_BIN_APPEND_NEW_VM_IN_DNS_REVERSE, args=[str(original_reverse_zone_file), vm_hostname, vm_ip, fqdn], env=None, cwd=str(dns_config_path))
    time.sleep(2)
    # restart named
    vm.start_process(program_path=BIN_SYSTEMCTL, args=["restart", "named"], env=None, cwd=TMP)
    time.sleep(2)
    
def connect_to_dns_master_vm(vcenter_server, dns_server_datacenter, dns_server_datastore):
    vm=vcenter_server.get_vm_by_path(dns_server_datastore, dns_server_datacenter)
    return vm     
    
def connect_vcenter(vcenter_address, vcenter_username, vcenter_password):
    ssl._create_default_https_context=ssl._create_unverified_context
    vcenter_server=VIServer()
    vcenter_server.connect(host=vcenter_address, user=vcenter_username, password=vcenter_password)
    print "connect to vcenter."
    return vcenter_server

def config_new_vm(vcenter_server, datacenter, vm_datastore_path, vm_ip, vm_gateway, vm_fqdn, vm_username, vm_password):
    USR_BIN_PUPPET="/opt/puppetlabs/bin/puppet"
    TMP="/tmp/"
    USR_BIN_RM="/usr/bin/rm"
    VAR_LIB_PUPPET="/opt/puppetlabs/puppet/cache/"
    # SBIN_REBOOT="/sbin/reboot"
    vm = vcenter_server.get_vm_by_path(vm_datastore_path, datacenter)
    print "start to config new vm"
    vm.login_in_guest(user=vm_username, password=str(vm_password))
    time.sleep(2)
    # disable puppet agent
    vm.start_process(program_path=USR_BIN_PUPPET, args=["agent", "--disable"], env=None, cwd=TMP)
    time.sleep(2)
    print "remove puppet ssl on the new vm"
    vm.start_process(program_path=USR_BIN_RM, args=["-rf", "ssl*"], env=None, cwd=VAR_LIB_PUPPET)
    time.sleep(2)

def require_certificate(vcenter_server, datacenter, vm_datastore_path, puppet_master_fqdn, puppet_environment, vm_username, vm_password):
    USR_BIN_RM="/usr/bin/rm"
    # USR_BIN_PUPPET="/usr/bin/puppet"
    USR_BIN_PUPPET="/opt/puppetlabs/bin/puppet"
    TMP="/tmp/"
    # VAR_LIB_PUPPET="/var/lib/puppet/"
    VAR_LIB_PUPPET="/opt/puppetlabs/puppet/cache/"
    new_vm=vcenter_server.get_vm_by_path(vm_datastore_path, datacenter)
    new_vm.login_in_guest(user=vm_username, password=str(vm_password))
    # request a certificate and run puppet
    print "remove old puppet certificate in new vm"
    new_vm.start_process(program_path=USR_BIN_RM, args=["-rf", "ssl*"], env=None, cwd=VAR_LIB_PUPPET)
    for x in range(1,5):
        print("Sleep %s second. Waiting..." % x)
        time.sleep(1)
    print "connect to puppet master=%s, puppet environment=%s" % (puppet_master_fqdn, puppet_environment)
    print "request puppet certificate in new vm"
    new_vm.start_process(program_path=USR_BIN_PUPPET, args=["agent", "-t", "--server="+str(puppet_master_fqdn), "--environment="+str(puppet_environment)], env=None, cwd=TMP)
    print "require_certificate_done"
    for x in range(1,30):
        print("Sleep %s second. Waiting..." % x)
        time.sleep(1)

def sign_certificate(vcenter_server, new_vm_fqdn, vm_username, vm_password, dns_server_datacenter, dns_server_datastore):
    OPT_PUPPETLABS_BIN_PUPPET="/opt/puppetlabs/bin/puppet"
    # puppet master sign certificate
    dns_master_vm = connect_to_dns_master_vm(vcenter_server, dns_server_datacenter, dns_server_datastore)
    # print "dns_master_vm=%s" % dns_master_vm
    dns_master_vm.login_in_guest(user=vm_username, password=str(vm_password))
    print "new vm fqdn=%s. sign certificate for the new vm." % str(new_vm_fqdn)
    dns_master_vm.start_process(program_path="/opt/puppetlabs/bin/puppet", args=["cert", "sign", str(new_vm_fqdn)], env=None, cwd="/opt/puppetlabs/bin/")
    # certificate sign might take a little while
    for x in range(1,30):
        print("Sleep %s second. Waiting..." % x)
        time.sleep(1)
    print "sign_certificate_done"
   
def run_puppet_agent(vcenter_server, datacenter, vm_datastore_path, puppet_master_fqdn, puppet_environment, vm_username, vm_password):
    # USR_BIN_PUPPET="/usr/bin/puppet"
    USR_BIN_PUPPET="/opt/puppetlabs/bin/puppet"
    TMP="/tmp/"
    new_vm=vcenter_server.get_vm_by_path(vm_datastore_path, datacenter)
    new_vm.login_in_guest(user=vm_username, password=str(vm_password))  
    print "enable puppet agent and run on new vm for environment=%s and connected with puppet master=%s" % (str(puppet_environment), str(puppet_master_fqdn))
    new_vm.start_process(program_path=USR_BIN_PUPPET, args=["agent", "--enable"], env=None, cwd=TMP)
    for x in range(1,5):
        print("Waiting... Sleep %s second." % x)
        time.sleep(1)
    new_vm.start_process(program_path=USR_BIN_PUPPET, args=["agent", "-t", "--server="+str(puppet_master_fqdn), "--environment="+str(puppet_environment)], env=None, cwd=TMP)
    print "run_puppet_agent_done"

def provide_default_puppet_vm_yaml_file(vcenter_server, new_vm_fqdn, puppet_environment, vm_username, vm_password, dns_server_datacenter, dns_server_datastore):
    USR_BIN_ECHO="/usr/bin/echo"
    # puppet individual vm's config
    vm_puppet_path = "/etc/puppetlabs/code/environments/" + str(puppet_environment) + "/hieradata/nodes/"
    vm_puppet_file = vm_puppet_path + str(new_vm_fqdn) + ".yaml"
    print "vm class file in puppet master=%s" % vm_puppet_file
    dns_master_vm = connect_to_dns_master_vm(vcenter_server, dns_server_datacenter, dns_server_datastore)
    dns_master_vm.login_in_guest(user=vm_username, password=str(vm_password))
    time.sleep(1)
    dns_master_vm.start_process(program_path=USR_BIN_ECHO, args=["---", ">", str(vm_puppet_file)], env=None, cwd=str(vm_puppet_path))
    time.sleep(1)
    dns_master_vm.start_process(program_path=USR_BIN_ECHO, args=["classes:", ">>", str(vm_puppet_file)], env=None, cwd=str(vm_puppet_path))
    time.sleep(1)
    dns_master_vm.start_process(program_path=USR_BIN_ECHO, args=["  - passwd", ">>", str(vm_puppet_file)], env=None, cwd=str(vm_puppet_path))
    print "add vm class file in puppet master in environment=%s" % str(puppet_environment)

def disconnect_vcenter_server(vcenter_server):
    vcenter_server.disconnect()
    print "Disconnect with vcenter. End"

def vm_is_up(vcenter_server, vm_datastore_path, datacenter):
    vm = vcenter_server.get_vm_by_path(vm_datastore_path, datacenter)
    print "vm_is_up_1: vmware tools status=%s" % str(vm.get_tools_status())
    if (vm.get_tools_status() != ToolsStatus.RUNNING):
        while(vm.get_tools_status() != ToolsStatus.RUNNING):
            print "vm_is_up_2: vmware tools status=%s" % str(vm.get_tools_status())
            print("Sleep %s second. Waiting..." % 2)
            time.sleep(2)
        
        print "vm_is_up_3: vmware tools status=%s" % str(vm.get_tools_status())

# for dns config file
def get_environment_for_dns(env):
    # vm_environment: development, test, preproduction, admin, production
    # puppet_environment: development, test, preproduction, production
    # dns_environment: admin, development, preproduction, test, production
    environments = {'development':       'dev', 
                    'test':              'test',
                    'preproduction':     'preproduction',
                    'admin':             'admin', 
                    'production':        'production'
                    }
    # default env is dev
    return environments.get(env, 'development')

def read_new_vm_config():
    all_vm_config = {}
    # print "Start to read new vm config from configurations"
    filename = "create_vm/config/vm_config.yml"
    try:
        with open(filename, 'r') as file:
            for line in file:
                if (not str(line).startswith('---')) and (not str(line).startswith('domain:')):
                    (key, value) = line.rstrip().split()
                    all_vm_config[key.split(":")[0]] = str(value)
    except IOError:
        print "can't open %s" % filename
             
    return all_vm_config

def read_credentials():
    credentials = {}
    array =[]
    # print "Read VM OS credentials"
    filename = "create_vm/config/os_credentials.txt"
    try:
        with open(filename, 'r') as file:
            for line in file:
                if str(line).startswith('vm_encoded_password'):
                    array = line.rstrip().split("=")
                    key = array[0]
                    value = str(array[1]) + "="
                else:
                    (key, value) = line.rstrip().split("=")
                # print "add key=%s and value=%s to dict credentials" % (key, value)
                credentials[key]=value
    except IOError:
        print "can't open file" % filename
    
    return credentials

def decode(key, string):
    decoded_chars = []
    string = base64.urlsafe_b64decode(string)
    for i in xrange(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(abs(ord(string[i]) - ord(key_c) % 256))
        decoded_chars.append(encoded_c)
    decoded_string = "".join(decoded_chars)
    return decoded_string

if __name__ == '__main__':
    credentials=read_credentials()
    vm_username=credentials['vm_username']
    key=credentials['key']
    vm_encoded_password=credentials['vm_encoded_password']
    vm_password=decode(key, vm_encoded_password)
    dns_config_path=credentials['dns_config_path']
    dns_server_datacenter=credentials['dns_server_datacenter']
    dns_server_datastore=credentials['dns_server_datastore']
    vcenter_address=credentials['vcenter_address']
    vcenter_username=credentials['vcenter_username']
    vcenter_encoded_password=credentials['vcenter_encoded_password']    
    vcenter_password=decode(key, vcenter_encoded_password)
    dns_backup_path=credentials['dns_backup_path']
    
    all_vm_config = {}
    all_vm_config = read_new_vm_config() 
    vm_hostname = all_vm_config['vm_hostname']
    puppet_master_fqdn = all_vm_config['puppet_master_fqdn']
    datacenter = all_vm_config['datacenter']
    datastore = all_vm_config['datastore']
    domain_prefix = all_vm_config['domain_prefix']
    puppet_environment = all_vm_config['puppet_environment']
    vm_ip = all_vm_config['vm_ip']
    vm_environment = all_vm_config['vm_environment']
    
    original_zone_file=domain_prefix + "." + get_environment_for_dns(vm_environment) + ".zone" 
    fqdn = vm_hostname + "." + domain_prefix + "." + get_environment_for_dns(vm_environment) 
    vm_gateway_list = vm_ip.split(".")
    vm_gateway=str(vm_gateway_list[0]) + "." + str(vm_gateway_list[1]) + "." + str(vm_gateway_list[2]) + "." + str(1);
    vm_datastore_path="[" + str(datastore) + "]" + " " + str(vm_hostname) + "/" + str(vm_hostname) + ".vmx"
    original_reverse_zone_file=domain_prefix + "." + get_environment_for_dns(vm_environment) + ".rr." + str(vm_gateway_list[2]) + ".zone"
    # print "zone file=%s" % original_zone_file
    # print "reverse zone file=%s" % original_reverse_zone_file
    # print "fqdn=%s" % fqdn
    # print "vm ip=%s" % vm_ip
    # print "vm gateway=%s" % vm_gateway
    # print "DATASTORE=%s" % vm_datastore_path 
    vcenter_server = connect_vcenter(vcenter_address, vcenter_username, vcenter_password)
    if argv[1] == 'update_dns':
        print "Wait 15 seconds for vm to come up."
        for x in range(1,15):
            print "%s second" % x
            time.sleep(1)
        # add VM dns record    
        vm_is_up(vcenter_server, vm_datastore_path, datacenter)
        dns_master_vm = connect_to_dns_master_vm(vcenter_server, dns_server_datacenter, dns_server_datastore)
        config_new_vm(vcenter_server, datacenter, vm_datastore_path, vm_ip, vm_gateway, fqdn, vm_username, vm_password)
        update_dns_zone(original_zone_file, original_reverse_zone_file, dns_master_vm, vm_hostname, vm_ip, fqdn, vm_username, vm_password, dns_config_path, dns_backup_path)
    elif argv[1] == 'connect_puppet_master':
        # connect to puppet master
        require_certificate(vcenter_server, datacenter, vm_datastore_path, puppet_master_fqdn, puppet_environment, vm_username, vm_password)
        sign_certificate(vcenter_server, fqdn, vm_username, vm_password, dns_server_datacenter, dns_server_datastore)
        run_puppet_agent(vcenter_server, datacenter, vm_datastore_path, puppet_master_fqdn, puppet_environment, vm_username, vm_password)
        disconnect_vcenter_server(vcenter_server)
    elif argv[1] == 'add_default_puppet_class':
        # add default puppet class (passwd). Or use common.yaml to provide default puppet class
        provide_default_puppet_vm_yaml_file(vcenter_server, fqdn, puppet_environment, vm_username, vm_password, dns_server_datacenter, dns_server_datastore)
        run_puppet_agent(vcenter_server, datacenter, vm_datastore_path, puppet_master_fqdn, puppet_environment, vm_username, vm_password)
        disconnect_vcenter_server(vcenter_server)
    elif argv[1] == 'test':
        print "this is a test from python scripts"
        sys.stdout.flush()
