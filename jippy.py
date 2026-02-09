#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ipaddress
import os
import netaddr
from typing import List, Union

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert IP notations and collect additional informations.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('mode', 
                        choices=['atomize', 'minify', 'count', 'adjacent'],
                        help=('Mode of operation\n'
                            '\tatomize: Returns a list of single IPs that are contained in the input\n'
                            '\tminify: Calculates the smalles number of CIDR ranges containing all IPs from the input \n'
                            '\tcount: Returns the number of unique IPs contained in the input\n'
                            '\tadjacent: Returns a list of IP addresses that are increasingly further away from the provided address until a CIDR range is covered'
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
    parser.add_argument('--prefix','-p', help='The prefix specifing the maximum CIDR range the IP List should include for calculating adjacent IPs',default=24)
    
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

def ips_by_increasing_distance(
    start_ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address],
    cidr: Union[str, ipaddress.IPv4Network, ipaddress.IPv6Network],
    *,
    include_network_and_broadcast: bool = True,
) -> List[str]:
    """
    Generate all IPs in `cidr`, ordered by increasing distance from `start_ip`
    (ties broken by preferring lower IP first: -d then +d).

    Example distances from start:
        start, start-1, start+1, start-2, start+2, ...

    Args:
        start_ip: Starting IP (string or ipaddress object)
        cidr: Network in CIDR notation (string or ipaddress network)
        include_network_and_broadcast: For IPv4, whether to include network and broadcast
            addresses. (If False, uses network.hosts().)

    Returns:
        List of IP strings covering the entire CIDR (or just hosts if configured).

    Raises:
        ValueError: if start_ip is not inside cidr or IP versions mismatch.
    """
    net = ipaddress.ip_network(cidr, strict=False) if isinstance(cidr, str) else cidr
    ip = ipaddress.ip_address(start_ip) if isinstance(start_ip, str) else start_ip

    if ip.version != net.version:
        raise ValueError("start_ip and cidr must be the same IP version")
    if ip not in net:
        raise ValueError(f"start_ip {ip} is not inside network {net}")

    # Define the population of addresses we must cover
    if isinstance(net, ipaddress.IPv4Network) and not include_network_and_broadcast:
        all_addrs = [a for a in net.hosts()]
    else:
        all_addrs = [a for a in net]

    addr_set = set(all_addrs)
    n = len(all_addrs)

    start_int = int(ip)

    out: List[str] = []
    seen = set()

    def try_add(x: int) -> None:
        a = ipaddress.ip_address(x)
        if a in addr_set and a not in seen:
            out.append(str(a))
            seen.add(a)

    # distance 0 first
    try_add(start_int)

    d = 1
    # Keep expanding distance until we've collected everything in the block
    while len(out) < n:
        # Prefer lower first for the same distance (matches your example)
        try_add(start_int - d)
        if len(out) >= n:
            break
        try_add(start_int + d)
        d += 1

        # Safety guard: should never be hit if logic is correct
        if d > n + 2:
            raise RuntimeError("Unexpected loop growth; check network bounds.")

    return out

def cidr_block_from_ip(ip: str, prefix_len: int) -> ipaddress.IPv4Network:
    return ipaddress.ip_network(f"{ip}/{prefix_len}", strict=False)


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

    if args.mode == "adjacent":
        if len(ips) !=1:
            print('[!] Adjacent mode requires singular IP address as input')
            exit(-1)
        output_list = ips_by_increasing_distance(ips[0],str(cidr_block_from_ip(ips[0],args.prefix)))
        print(*output_list, sep='\n')

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
