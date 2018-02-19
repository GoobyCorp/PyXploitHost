#!/usr/bin/python3

import re
import sys
import socket
import traceback
from os.path import isfile
from threading import Thread
from binascii import unhexlify

HOSTS_FILE = "hosts.txt"

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 53

"""
This script can actually be used for anything DNS-related but it's nice to have for redirecting DNS queries on anything.
"""

domain_exp = re.compile(r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))', re.IGNORECASE)

def get_local_ip():
    #hacky AF but it will tell which interface is active
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_addr = s.getsockname()[0]
    s.close()
    return local_addr

class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = bytearray()
        tipo = (data[2] >> 3) & 15
        if tipo == 0:
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1] + bytes(".", "ascii")
                ini += lon + 1
                lon = data[ini]
        self.domain = str(self.domain, "utf8").rstrip(".")

    def response(self, ip):
        packet = bytearray()
        if self.domain:
            packet += self.data[:2] + b"\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + b"\x00\x00\x00\x00"
            packet += self.data[12:]
            packet += b"\xC0\x0C"
            packet += unhexlify("000100010000003C0004")
            packet += bytearray([int(x) for x in ip.split(".")])
        return packet

def resolve_hostname(hostname):
    return socket.gethostbyname(hostname)

def parse_host_file_as_regex(data):
    host_list = []
    for line in data.splitlines():
        if line != "" and line[0] != "#":
            split_line = line.split(" ", 1)
            if len(split_line) == 2:
                host_regex = split_line[0]
                ip_addr = split_line[1]
                host_list.append([re.compile(host_regex), ip_addr])
    return host_list

def handle_dns(addr, data):
    domain = None
    try:
        p = DNSQuery(data)
        domain = p.domain
        if ".in-addr.arpa" not in p.domain:  #no reverse DNS
            if domain_exp.match(p.domain):
                result = [ip_addr for (regex, ip_addr) in host_data if regex.search(p.domain)]
                if result:
                    ip = result[0]
                    if ip == "ME":
                        ip = local_ip
                    print("Local:   {} -> {} -> {}".format(addr[0], p.domain, ip))
                    sock.sendto(p.response(ip), addr)
                else:
                    ip = resolve_hostname(p.domain)
                    print("Remote:  {} -> {} -> {}".format(addr[0], p.domain, ip))
                    sock.sendto(p.response(ip), addr)
            else:
                ip = "0.0.0.0"
                print("Error:   {} -> {} -> {}".format(addr[0], p.domain, ip))
                sock.sendto(p.response(ip), addr)
        else:
            ip = "0.0.0.0"  #p.domain.replace(".in-addr.arpa", "")
            print("Reverse: {} -> {} -> {}".format(addr[0], p.domain, ip))
    except:
        if domain is not None:
            print(domain)
            sock.shutdown(socket.SHUT_RDWR)
        traceback.print_exc()

if __name__ == '__main__':
    if isfile(HOSTS_FILE):
        local_ip = get_local_ip()
        host_data = parse_host_file_as_regex(open(HOSTS_FILE, "r").read())
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((SERVER_HOST, SERVER_PORT))
        print("DNS Proxy server started on UDP port {}!".format(SERVER_PORT))
        print("Use %s as your primary DNS server on your PS4 console." % (local_ip))
        while True:
            try:
                (data, addr) = sock.recvfrom(1024)
                t = Thread(target=handle_dns, args=(addr, data))
                t.start()
            except KeyboardInterrupt:
                print("Exiting now...")
                sock.shutdown(socket.SHUT_RDWR)
                sys.exit(0)
            except:
                print("Error starting thread...")
    else:
        print("Host file not found!")