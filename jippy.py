#!/usr/bin/env python3

import argparse
import ipaddress
import os
import netaddr

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert IP notations and collect additional informations.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('mode', 
                        choices=['atomize', 'minify', 'count'],
                        help=('Mode of operation\n'
                            '\tatomize: Returns a list of single IPs that are contained in the input\n'
                            '\tminify: Calculates the smalles number of CIDR ranges containing all IPs from the input \n'
                            '\tcount: Returns the number of unique IPs contained in the input\n'
                        ))
    
    parser.add_argument('ips', 
                        nargs='+', 
                        help=('Input IPs as space separated list or an input file with newline separated entries. Supported formats are:\n'
                            '\tStandard IP notation (123.123.123.123)\n'
                            '\tCIDR ranges (123.123.123.0/24)\n'
                            '\tRange notation (123.123.123.0-123)\n'
                        ))
    
    parser.add_argument('--output', '-o', default=None, help='Write the output to the specified file.')
    parser.add_argument('--exclude', '-e', nargs='+', default=None, help='Remove the IPs from the input')
    
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
    atom_list = atomize_targets(ips)
    if args.exclude:
            tmp_list = [ip for ip in atom_list if ip not in atomize_targets(get_input(args.exclude))]
            atom_list = tmp_list
        
    if args.mode == "atomize":
        output_list = atom_list
        print(*output_list, sep='\n')
    
    if args.mode == "minify":
        cidr_list = [str(cidr) for cidr in netaddr.IPSet(atom_list).iter_cidrs()]
        output_list = cidr_list
        print(*output_list, sep='\n')

    if args.mode == "count":
        cnt = len(atom_list)
        print(cnt)
        output_list = [cnt]

    #Write output if specified
    if args.output:
        try:
            with open(args.output, "w") as fd:
                for entry in output_list:
                    fd.write(entry + "\n")
        except Exception as e:
            print("[!] Something went wrong writing the output to the specified file")
            print(str(e))



if __name__ == '__main__':
    main()
