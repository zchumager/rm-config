import argparse
import broadlink
import ifcfg
import nmap
import netaddr
import random

from errno import ENETUNREACH
from functools import reduce


def setup_rm(ssid, password, sec_mode):
    """
    :param ssid: WiFi SSID
    :param password: WiFi Password
    :param sec_mode: WiFi Security Mode
    :return:
    """
    try:
        broadlink.setup(ssid, password, sec_mode)
    except IOError as e:
        if e.errno == ENETUNREACH:
            print("SENDING PACKAGES")


def get_rm_info(devices):
    """
    :param devices: A List of broadlink objects
    :return: a dict with the first broadlink object found
    """
    print("RM INFO")

    model = devices[0].model
    ip_address = devices[0].host[0]
    bin_mac = devices[0].mac
    mac_address = ':'.join(format(e, '02x').upper() for e in bin_mac)
    raw_mac = mac_address.replace(":", "").lower()

    return {
        "model": model,
        "ip_address": ip_address,
        "binary_mac": bin_mac,
        "mac_address": mac_address,
        "raw_mac": raw_mac
    }


def discover_devices():
    devices = broadlink.discover(timeout=5)
    if len(devices) > 0:
        rm_info = get_rm_info(devices)
        print(f"DEVICE INFORMATION: {rm_info}")
    else:
        print("NO DEVICE WAS FOUND IN THE NETWORK")


def calculate_netmask_bits(network_mask):
    """
    :param network_mask: the valid network mask where computer is connected like 255.255.255.0
    :return: number of bits in decimal format like /24
    """

    netmask_bits = 0

    for segment in network_mask.split("."):
        binary_value = bin(int(segment)).replace("0b", "")
        bits = int(reduce(lambda x, y: int(x) + int(y), binary_value))
        netmask_bits += bits

    return netmask_bits


def get_used_ips():
    default = ifcfg.default_interface()

    ip_address = default['inet']
    network_mask = default['netmask']

    netmask_bits = calculate_netmask_bits(network_mask)
    subnet_mask = f"{ip_address}/{netmask_bits}"

    print("GETTING IP TO USE AS STATIC...")

    all_ips = list(netaddr.IPNetwork(subnet_mask).iter_hosts())
    all_ips_list = [str(ip) for ip in all_ips]

    nm = nmap.PortScanner()
    host_dict = nm.scan(hosts=subnet_mask, arguments='-n -sP -PE').get('scan')
    host_list = host_dict.keys()

    print("USED IPS:")
    for host in host_list:
        print(host)

    free_ips = list(set(all_ips_list) - set(host_list))
    print("******************************************")
    print("SUGGESTED IP TO USE AS STATIC: ", random.choice(free_ips))


def main():
    parser = argparse.ArgumentParser(description='RM Mini Configurator Python CLI Tool')

    parser.add_argument('--ssid', help="WiFi SSID")
    parser.add_argument('--password', help="WiFi Password")
    parser.add_argument('--mode', help="WiFi Security Mode")
    parser.add_argument('--details', help="Get details for an already configured RM Mini", action="store_true")
    parser.add_argument('--getip', help='Get a free IP to use as static', action="store_true")

    args = parser.parse_args()

    if args.ssid and args.password and args.mode:
        setup_rm(args.ssid, args.password, int(args.mode))
        devices = broadlink.discover(timeout=5)
        if not devices:
            input("WAIT!!! PRESS ENTER JUST WHEN YOUR COMPUTER CONNECTS TO YOUR HOME NETWORK AGAIN...")
        discover_devices()
    elif args.details:
        discover_devices()
    elif args.getip:
        get_used_ips()
    else:
        print("IF THE RM MINI IS ALREADY CONFIGURED")
        print("PLEASE USE THE FLAG --details TO GET THE CONNECTION DATA")
        print("IN OTHER CASE USE THE FOLLOWING EXAMPLE TO CONFIGURE THE RM MINI")
        print("python3 rm_configurator/rm_config.py --sssid SSID_2.4 --password SSID_PASSWORD --mode  NETWORK_MODE")


if __name__ == "__main__":
    main()
