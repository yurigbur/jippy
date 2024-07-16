#!/usr/bin/env python3

import argparse
import ipaddress
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert IP notifications and collect idditional informations.')
    
    parser.add_argument('mode', 
                        choices=['atomize', 'minify', 'count'],
                        help='Mode of operation\n \
                            atomize: Returns a list of single IPs that are contained in the input\n \
                            minify: Calculates the smalles number of CIDR ranges containing all IPs from the input \n \
                            count: Returns the number of unique IPs contained in the input'
                        )
    
    parser.add_argument('ips', 
                        nargs='+', 
                        help='Input IPs as space separated list or an input file with newline separated entries.\n \
                            Supported formats are standard IP notation (123.123.123.123), CIDR ranges (123.123.123.0/24) and range notation (123.123.123.0-123)'
                        )
    
    args = parser.parse_args()
    return args    

def validate_ip_format(ip):
    return True


def get_input(ips):
    if len(ips) == 1:
        file_path = ips[0]
        if os.path.isfile(file_path):
            with open(file_path) as fd:
                ips = [line.strip() for line in fd.readlines()]

    for ip in ips:
        if validate_ip_format(ip):
            continue
        else:
            print('[!] Unknown IP format found in input file!')
            exit(-1)

    return ips


def atomize_targets(arguments):
    ips = []
    for arg in arguments:    
        if '-' in arg:
            # Handle IP Range format
            base_ip, end = arg.split('-')
            start_ip = ipaddress.IPv4Address(base_ip)
            end_ip = start_ip + int(end.split('.')[-1]) - int(str(start_ip).split('.')[-1])
            for ip_int in range(int(start_ip), int(end_ip) + 1):
                ips.append(str(ipaddress.IPv4Address(ip_int)))
        elif '/' in arg:
            # Handle CIDR Notation
            network = ipaddress.IPv4Network(arg, strict=False)
            for ip in network:
                ips.append(str(ip))
        else:
            # Handle Single IP Address
            ips.append(arg)
    
    sortable_ips = [ipaddress.ip_address(ip) for ip in list(set(ips))]
    sorted_ips = sorted(sortable_ips)
    
    return [str(ip) for ip in sorted_ips]


def main():
    args = parse_arguments()

    ips = get_input(args.ips)
    if args.mode == "atomize":
        print(atomize_targets(ips))
    
    if args.mode == "minify":
        print("[!] Not implemented yet")

    if args.mode == "count":
        print(len(atomize_targets(ips)))


if __name__ == '__main__':
    main()
