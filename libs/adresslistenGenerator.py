from _socket import inet_ntoa, inet_aton
from struct import pack, unpack

from netaddr import IPNetwork

DHCP_KEY = '[DHCP]'
INTERVAL_KEY = '[Interval]'
AUTO_KEY = '[AUTO]'

calc_needles = tuple(("MOD", "%", "DIV", "/", "MUL", "*", "ADD", "+", "SUB", "-", "ASCII(</b><i>x</i><b>)"))


class Adressliste:

    def __init__(self, server_count=0, client_count=0, dhcp_pools=None, ip='192.168.0.0', snm=27):
        if dhcp_pools is None:
            dhcp_pools = []
        self.bcAdr = None
        self.gwAdr = None
        self.serverLabels = None
        self.clientLabels = None
        self.labelsSet = False
        self.netzAdr = ip
        self.snmShort = "/" + str(snm)
        self.snmLong = self.get_snm(snm)
        self.serverArray = list()
        self.clientArray = list()
        self.hostArray = list()
        self.DHCPPools = list()
        data = self.ipv4_breakout(self.netzAdr, self.snmShort)
        for d in data:
            if type(d) is list:
                self.hostArray = d.copy()
                for j in range(1, min(server_count, len(self.hostArray)) + 1):
                    self.serverArray.append(self.hostArray[j])

                host_count = len(self.hostArray)
                itr = 0
                done = 0
                for i in dhcp_pools:
                    tmp = list()
                    minimum = min(server_count, len(self.hostArray)) + 1 + done
                    for j in range(minimum, minimum + i):
                        tmp.append(self.hostArray[j])
                        itr += 1
                    self.DHCPPools.append(tmp)
                    done += i

                for j in range(host_count - client_count, host_count):
                    self.clientArray.append(self.hostArray[j])

            else:
                if d[0] is "broadcast":
                    self.bcAdr = d[1]
                elif d[0] is "first_host":
                    self.gwAdr = d[1]

    def __str__(self):
        return self.to_html

    def set_labels(self, server_labels, client_labels):
        self.serverLabels = server_labels
        self.clientLabels = client_labels
        self.labelsSet = True

    def to_html(self):
        out = "<h4>Adr. Liste:</h4>\n"
        out += "Netz Adr.: "+str(self.netzAdr) + str(self.snmShort)+"<br />\n"
        out += "SNM: "+str(self.snmLong)+"<br />\n"
        out += "GW Adr.: "+str(self.gwAdr)+"<br />\n"
        if not (len(self.serverLabels)) < 1 or (
                len(self.serverLabels) == 1 and self.is_empty(self.serverLabels[0])):
            out += "Server:\n<ul>\n"
            i = 0
            for value in self.serverArray:
                if not self.is_empty(self.serverLabels[i]):
                    out += "<li>"
                    if self.labelsSet:
                        out += self.serverLabels[i] + ": "
                    out += value+"</li>\n"

                i += 1

            out += "</ul>\n"

        if len(self.DHCPPools) > 0:
            i = 0
            for pool in self.DHCPPools:
                out += "DHCPPool"+str(i)+":\n<ul>\n<li>" + pool[0] + " - " + pool[len(pool) - 1] + "</li>\n</ul>\n"
                i += 1

        if not (len(self.clientLabels) < 1 or (
                (len(self.clientLabels)) == 1 and self.is_empty(self.clientLabels[0]))):
            out += "Clients:\n<ul>\n"
            i = 0
            for value in self.clientArray:
                if not self.is_empty(self.clientLabels[i]):
                    out += "<li>"
                    if self.labelsSet:
                        out += self.clientLabels[i] + ": "
                    out += value+"</li>\n"

                i += 1

            out += "</ul>\n"

        out += "BC Adr.: "+str(self.bcAdr)
        return out

    @staticmethod
    def get_snm(snm):
        binary = ''
        for i in range(1, 33):
            if snm >= i:
                binary += '1'
            else:
                binary += '0'

        return long2ip(int(binary, 2))

    @staticmethod
    def ipv4_breakout(ip_address, ip_nmask):
        hosts = []
        net = IPNetwork(ip_address+ip_nmask)
        for ip in list(net[1:net.size-1]):
            hosts.append(str(ip))

        block_info = [
            ("network", str(net.network)),
            ("first_host", str(long2ip(net.first+1))),
            ("last_host", str(long2ip(net.last - 1))),
            ("broadcast", str(net.broadcast)),
            hosts
        ]
        return block_info

    @staticmethod
    def is_empty(s):
        out = ((s == '') or (s == ' ') or (s == '\n') or (s == '\r'))
        return out

    # Convert array of short unsigned integers to binary
    @staticmethod
    def _pack_bytes(array):
        chars = ''
        for byte in array:
            chars += pack('C', byte)

        return chars

    # Convert binary to array of short integers
    @staticmethod
    def _unpack_bytes(s):
        return unpack('C*', s)

    # Add array of short unsigned integers
    @staticmethod
    def _add_bytes(array1, array2):
        result = list()
        carry = 0
        for value1 in array1.reverse():
            value2 = array2.pop()
            if len(result) == 0:
                value2 += 1

            new_value = value1 + value2 + carry
            if new_value > 255:
                new_value = new_value - 256
                carry = 1
            else:
                carry = 0

            array_unshift(result, new_value)

        return result

    # Useful Functions
    @staticmethod
    def _cdr2bin(cdrin, length=4):
        if length > 4 or cdrin > 32:  # Are we ipv6?
            return "".ljust(cdrin, "1").ljust(128, "0")
        else:
            return "".ljust(cdrin, "1").ljust(32, "0")

    @staticmethod
    def _bin2cdr(binin):
        return len(binin.rstrip("0"))

    def _cdr2char(self, cdrin, length=4):
        hexadecimal = self._bin2hex(self._cdr2bin(cdrin, length))
        return self._hex2char(hexadecimal)

    def _char2cdr(self, char):
        binary = self._hex2bin(self._char2hex(char))
        return self._bin2cdr(binary)

    @staticmethod
    def _hex2char(hexadecimal):
        return pack('H*', hexadecimal)

    @staticmethod
    def _char2hex(char):
        hexadecimal = unpack('H*', char)
        return list(hexadecimal).pop()

    @staticmethod
    def _hex2bin(hexadecimal):
        return bin(int(hexadecimal, 16))

    @staticmethod
    def _bin2hex(binary):
        return hex(int(binary, 2))


def get_names(names_in):
    names = list()
    dhcps = list()
    dhcp_str = '0'
    for i in range(len(names_in)):
        if INTERVAL_KEY in names_in[i]:
            tmp = names[i:]
            names_tmp = names[:i]
            interval_str = names_in[i]
            interval_str = interval_str.replace(INTERVAL_KEY, '')
            tmp = list(filter(lambda x: INTERVAL_KEY not in x, tmp))
            for j in range(int(interval_str)):
                names_tmp.append('')
            for t in tmp:
                names_tmp.append(t)
            names = names_tmp.copy()

        elif DHCP_KEY in names_in[i]:
            dhcp_str = names_in[i].strip()
            dhcp_str = dhcp_str.replace(DHCP_KEY, '')
            names = list(filter(lambda x: DHCP_KEY not in x, names))
            dhcps.append(int(dhcp_str))

        elif AUTO_KEY in names_in[i]:
            auto_str = names_in[i].strip()
            auto_str = auto_str.replace(AUTO_KEY, '')
            auto_name = auto_str[0:auto_str.find(',')].strip()
            auto_str = auto_str.replace(auto_name, '').replace(',', '').strip()
            names = list(filter(lambda x: AUTO_KEY not in x, names))
            for j in range(int(auto_str)):
                names.append(str(auto_name) + '' + str(j))
        else:
            names.append(names_in[i].strip())

    return names, dhcps


def create(server_names_in, client_names_in, ip, snm):
    dhcps = list()
    server_names, dhcps_0 = get_names(server_names_in)
    client_names, dhcps_1 = get_names(client_names_in)
    for dhcp in dhcps_0:
        dhcps.append(dhcp)
    for dhcp in dhcps_1:
        dhcps.append(dhcp)

    # for i in range(len(client_names_in)):
    #     client_names.append(client_names_in[i].strip())
    #     if len(client_names) <= i:
    #         break
    #     if INTERVAL_KEY in client_names[i]:
    #         tmp = client_names[i:]
    #         client_names_tmp = client_names[:i]
    #         interval_str = client_names[i]
    #         interval_str = interval_str.replace(INTERVAL_KEY, '')
    #         tmp = list(filter(lambda x: INTERVAL_KEY not in x, tmp))
    #         for j in range(int(interval_str)):
    #             client_names_tmp.append('')
    #         for t in tmp:
    #             client_names_tmp.append(t)
    #         client_names = client_names_tmp.copy()
    #
    #     elif DHCP_KEY in client_names[i]:
    #         dhcp_str = client_names[i]
    #         dhcp_str = dhcp_str.replace(DHCP_KEY, '')
    #         client_names = list(filter(lambda x: DHCP_KEY not in x, client_names))
    #
    #     elif AUTO_KEY in client_names[i]:
    #         auto_str = client_names[i]
    #         auto_str = auto_str.replace(AUTO_KEY, '')
    #         auto_name = auto_str[0:auto_str.find(',')].strip()
    #         auto_str = auto_str.replace(auto_name, '').replace(',', '').strip()
    #         client_names = list(filter(lambda x: AUTO_KEY not in x, client_names))
    #         for j in range(int(auto_str)):
    #             client_names.append(str(auto_name) + '' + str(j))

    tmp = Adressliste(len(server_names), len(client_names), dhcps, ip, snm)
    tmp.set_labels(server_names, client_names)
    return tmp


def ip2long(ip_addr):
    return unpack("!L", inet_aton(ip_addr))[0]


def long2ip(ip):
    return inet_ntoa(pack("!L", ip))


def array_unshift(array, *args):
    """Prepend one or more elements to the beginning of an array"""
    for i in reversed(args):
        array.insert(0, i)
    return array


def get_byte(s=""):
    if s.isnumeric() and 255 >= int(s) >= 0:
        return s
    else:
        return int(calc(s))


def calc(s):
    s = s.strip()
    if s.isnumeric():
        return int(s)
    else:
        for needle in calc_needles:
            if "ASCII" in needle and "ASCII" in s:
                return ord(s[s.find('(')+1:s.find(')')])
            elif needle in s:
                left = calc((s[0:s.find(needle)].replace(needle, "").strip()))
                right = calc(s[s.find(needle):].replace(needle, "").strip())
                return int({
                    "MOD": lambda l, r: l % r,
                    "%": lambda l, r: l % r,
                    "DIV": lambda l, r: l / r,
                    "/": lambda l, r: l / r,
                    "MUL": lambda l, r: l * r,
                    "*": lambda l, r: l * r,
                    "ADD": lambda l, r: l + r,
                    "+": lambda l, r: l + r,
                    "SUB": lambda l, r: l - r,
                    "-": lambda l, r: l - r,
                }.get(needle)(left, right))
    return False


if __name__ == '__main__':
    print(create(list(), list(), "192.168.0.0", 28).to_html)
