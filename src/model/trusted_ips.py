import ipaddress


class TrustedIpValidator:
    def __init__(self, trusted_ips) -> None:
        self._simple_ips = {ip for ip in trusted_ips if '/' not in ip}
        self._networks = [ipaddress.ip_network(ip) for ip in trusted_ips if '/' in ip]

    def is_trusted(self, ip):
        if ip in self._simple_ips:
            return True

        if self._networks:
            address = ipaddress.ip_address(ip)
            for network in self._networks:
                if address in network:
                    return True

        return False
