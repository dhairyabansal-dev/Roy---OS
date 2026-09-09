import ipaddress
import socket


def private_ipv4_addresses():
    """Return active private IPv4 addresses without hardcoding an interface."""
    addresses = set()
    probes = [("192.0.2.1", 9), ("10.255.255.1", 9)]
    for target, port in probes:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(0.2)
            sock.connect((target, port))
            address = sock.getsockname()[0]
            parsed = ipaddress.ip_address(address)
            if parsed.is_private and not parsed.is_loopback and not parsed.is_link_local:
                addresses.add(address)
        except OSError:
            pass
        finally:
            sock.close()
    return sorted(addresses, key=lambda value: tuple(int(part) for part in value.split(".")))


def mobile_access_url(port):
    addresses = private_ipv4_addresses()
    return f"http://{addresses[0]}:{port}" if addresses else None
