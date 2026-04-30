#!/usr/bin/env python3
# Copyright 2026 Dimensional Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configure host networking for a Livox Mid-360 LiDAR and verify reachability.

The Mid-360 has no DHCP client; it ships with a fixed IP on 192.168.1.0/24
(default scheme: 192.168.1.1XX where XX comes from the serial). The host
must therefore have a static IP on the same subnet for FAST-LIO2 to talk
to it.

What this script does:
    1. Picks an ethernet interface (link UP, not already on the lidar subnet).
       Pass --interface to override.
    2. Adds host_ip/24 as an alias on it via sudo. Idempotent.
    3. Pings the configured lidar IP. On failure, ARP-scans the subnet and
       prints any neighbors found so a different lidar IP can be spotted.

Usage::

    python -m dimos.hardware.sensors.lidar.fastlio2.setup_network
    python -m dimos.hardware.sensors.lidar.fastlio2.setup_network --interface en7
    python -m dimos.hardware.sensors.lidar.fastlio2.setup_network --lidar-ip 192.168.1.142

Defaults match FastLio2Config in module.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import ipaddress
import os
import platform
import re
import shutil
import subprocess
import sys
import time

# Keep in sync with FastLio2Config in dimos/hardware/sensors/lidar/fastlio2/module.py
DEFAULT_HOST_IP = "192.168.1.5"
DEFAULT_LIDAR_IP = "192.168.1.155"
SUBNET_MASK = "255.255.255.0"
PREFIX_LEN = 24

PING_TIMEOUT_MS = 2000
SCAN_PING_TIMEOUT_MS = 300
ARP_SETTLE_SEC = 4
POST_ASSIGN_SETTLE_SEC = 0.5
LAST_OCTET_RANGE = range(1, 255)

# Known Livox/DJI OUIs. Add new prefixes here when encountered.
LIVOX_OUIS = frozenset({"8c:58:23"})

TEST_SCRIPT_PATH = "dimos/hardware/sensors/lidar/fastlio2/fastlio_test.py"


@dataclass
class Interface:
    name: str
    mac: str
    is_up: bool
    has_carrier: bool
    is_wireless: bool = False
    addrs: list[str] = field(default_factory=list)


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _wireless_interfaces_darwin() -> set[str]:
    out = _run(["networksetup", "-listallhardwareports"]).stdout
    wireless: set[str] = set()
    port: str = ""
    for line in out.splitlines():
        if line.startswith("Hardware Port:"):
            port = line.split(":", 1)[1].strip()
        elif line.startswith("Device:") and ("Wi-Fi" in port or "AirPort" in port):
            wireless.add(line.split(":", 1)[1].strip())
    return wireless


def _list_interfaces_darwin() -> list[Interface]:
    out = _run(["ifconfig"], check=True).stdout
    wireless = _wireless_interfaces_darwin()
    interfaces: list[Interface] = []
    current: Interface | None = None
    for line in out.splitlines():
        if not line:
            continue
        if not line[0].isspace():
            if current is not None:
                interfaces.append(current)
            header = re.match(r"^(\S+):\s+flags=\S+<([^>]+)>", line)
            if not header:
                current = None
                continue
            flags = header.group(2).split(",")
            name = header.group(1)
            current = Interface(
                name=name,
                mac="",
                is_up="UP" in flags and "RUNNING" in flags,
                has_carrier=False,
                is_wireless=name in wireless,
            )
            continue
        if current is None:
            continue
        ether = re.search(r"\bether\s+([0-9a-fA-F:]+)", line)
        if ether:
            current.mac = ether.group(1)
        status = re.search(r"\bstatus:\s+(\S+)", line)
        if status:
            current.has_carrier = status.group(1) == "active"
        for addr in re.findall(r"\binet\s+(\d+\.\d+\.\d+\.\d+)", line):
            current.addrs.append(addr)
    if current is not None:
        interfaces.append(current)
    return [i for i in interfaces if i.name.startswith(("en", "eth"))]


def _is_wireless_linux(name: str) -> bool:
    return os.path.exists(f"/sys/class/net/{name}/wireless")


def _list_interfaces_linux() -> list[Interface]:
    by_name: dict[str, Interface] = {}
    link_out = _run(["ip", "-o", "link", "show"], check=True).stdout
    for line in link_out.splitlines():
        header = re.match(r"^\d+:\s+([^:@]+)[:@].*<([^>]+)>", line)
        if not header:
            continue
        name = header.group(1)
        if not name.startswith(("en", "eth", "wl")):
            continue
        flags = header.group(2).split(",")
        mac_match = re.search(r"link/ether\s+([0-9a-fA-F:]+)", line)
        by_name[name] = Interface(
            name=name,
            mac=mac_match.group(1) if mac_match else "",
            is_up="UP" in flags,
            has_carrier="LOWER_UP" in flags,
            is_wireless=_is_wireless_linux(name),
        )
    addr_out = _run(["ip", "-o", "-4", "addr", "show"], check=True).stdout
    for line in addr_out.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        name, family, cidr = parts[1], parts[2], parts[3]
        if family != "inet" or name not in by_name:
            continue
        by_name[name].addrs.append(cidr.split("/")[0])
    return list(by_name.values())


def _list_interfaces() -> list[Interface]:
    if platform.system() == "Darwin":
        return _list_interfaces_darwin()
    return _list_interfaces_linux()


def _on_subnet(addrs: list[str], target_ip: str) -> bool:
    net = ipaddress.IPv4Network(f"{target_ip}/{PREFIX_LEN}", strict=False)
    return any(ipaddress.IPv4Address(a) in net for a in addrs)


def _has_link_local_only(addrs: list[str]) -> bool:
    if not addrs:
        return False
    return all(ipaddress.IPv4Address(a).is_link_local for a in addrs)


def _pick_interface(interfaces: list[Interface], lidar_ip: str) -> Interface | None:
    already_on_subnet = [i for i in interfaces if _on_subnet(i.addrs, lidar_ip)]
    if already_on_subnet:
        return already_on_subnet[0]
    wired = [i for i in interfaces if i.has_carrier and not i.is_wireless]
    apipa = [i for i in wired if _has_link_local_only(i.addrs)]
    if apipa:
        return apipa[0] if len(apipa) == 1 else None
    no_ip = [i for i in wired if not i.addrs]
    if no_ip:
        return no_ip[0] if len(no_ip) == 1 else None
    if len(wired) == 1:
        return wired[0]
    return None


def _assign_alias(iface: str, host_ip: str) -> bool:
    if platform.system() == "Darwin":
        cmd = ["sudo", "ifconfig", iface, "alias", host_ip, SUBNET_MASK]
    else:
        cmd = ["sudo", "ip", "addr", "add", f"{host_ip}/{PREFIX_LEN}", "dev", iface]
    print(f"  $ {' '.join(cmd)}")
    result = _run(cmd)
    if result.returncode == 0:
        return True
    stderr = (result.stderr or "").strip()
    if "exists" in stderr.lower() or "already" in stderr.lower():
        print("  (already configured -- ok)")
        return True
    if stderr:
        sys.stderr.write(stderr + "\n")
    return False


def _ping_args(target: str, timeout_ms: int) -> list[str]:
    if platform.system() == "Darwin":
        return ["ping", "-c", "2", "-W", str(timeout_ms), target]
    return ["ping", "-c", "2", "-W", str(max(1, timeout_ms // 1000)), target]


def _ping(target: str) -> bool:
    return _run(_ping_args(target, PING_TIMEOUT_MS)).returncode == 0


def _is_livox_mac(mac: str) -> bool:
    return mac.lower()[:8] in LIVOX_OUIS


def _print_banner(lines: list[str], char: str = "=") -> None:
    width = max(60, max(len(line) for line in lines) + 4)
    bar = char * width
    print()
    print(bar)
    for line in lines:
        print(f"  {line}")
    print(bar)


def _arp_scan(host_ip: str) -> list[tuple[str, str]]:
    base = ".".join(host_ip.split(".")[:3])
    procs: list[subprocess.Popen[bytes]] = []
    for last in LAST_OCTET_RANGE:
        addr = f"{base}.{last}"
        if addr == host_ip:
            continue
        if platform.system() == "Darwin":
            args = ["ping", "-c", "1", "-W", str(SCAN_PING_TIMEOUT_MS), addr]
        else:
            args = ["ping", "-c", "1", "-W", "1", addr]
        procs.append(subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    deadline = time.monotonic() + ARP_SETTLE_SEC
    for proc in procs:
        remaining = max(0.01, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()
    arp_out = _run(["arp", "-an"]).stdout
    found: list[tuple[str, str]] = []
    for line in arp_out.splitlines():
        match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+|\(incomplete\))", line)
        if not match:
            continue
        ip, mac = match.group(1), match.group(2).lower()
        if mac == "(incomplete)":
            continue
        if ip.startswith(base + ".") and ip != host_ip:
            found.append((ip, mac))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure host networking for the Livox Mid-360 LiDAR."
    )
    parser.add_argument("--interface", help="Ethernet interface to use (auto-detected if omitted).")
    parser.add_argument("--host-ip", default=DEFAULT_HOST_IP)
    parser.add_argument("--lidar-ip", default=DEFAULT_LIDAR_IP)
    args = parser.parse_args()

    if not shutil.which("sudo"):
        print(
            "sudo not found; this script needs root to assign an IP.",
            file=sys.stderr,
        )
        return 2

    interfaces = _list_interfaces()
    if not interfaces:
        print("No ethernet interfaces found.", file=sys.stderr)
        return 2

    if args.interface:
        chosen = next((i for i in interfaces if i.name == args.interface), None)
        if chosen is None:
            available = ", ".join(i.name for i in interfaces)
            print(
                f"Interface {args.interface!r} not found. Available: {available}",
                file=sys.stderr,
            )
            return 2
    else:
        chosen = _pick_interface(interfaces, args.lidar_ip)
        if chosen is None:
            print("Could not auto-pick an interface. Candidates:", file=sys.stderr)
            for iface in interfaces:
                addrs = ", ".join(iface.addrs) if iface.addrs else "[none]"
                kind = "wifi " if iface.is_wireless else "wired"
                print(
                    f"  {iface.name:6s}  {kind}  carrier={iface.has_carrier}  addrs={addrs}",
                    file=sys.stderr,
                )
            print("Re-run with --interface <name>.", file=sys.stderr)
            return 2

    addrs_str = ", ".join(chosen.addrs) if chosen.addrs else "[none]"
    carrier_str = "up" if chosen.has_carrier else "down"
    print(f"Interface: {chosen.name} (mac={chosen.mac}, carrier={carrier_str}, addrs={addrs_str})")
    if not chosen.has_carrier:
        print(
            f"  WARNING: {chosen.name} has no carrier. Check the cable to the Mid-360.",
            file=sys.stderr,
        )

    if _on_subnet(chosen.addrs, args.lidar_ip):
        print(f"  {chosen.name} already on lidar subnet -- skipping IP assignment")
    else:
        print(f"Assigning {args.host_ip}/{PREFIX_LEN} to {chosen.name}:")
        if not _assign_alias(chosen.name, args.host_ip):
            print(f"Failed to assign {args.host_ip}.", file=sys.stderr)
            return 1
        time.sleep(POST_ASSIGN_SETTLE_SEC)

    print(f"\nLooking for Mid-360 at {args.lidar_ip} ...")
    pinged = _ping(args.lidar_ip)
    if pinged:
        print(f"  ICMP reply from {args.lidar_ip}.")

    print(f"  ARP/L2 scan of subnet (~{ARP_SETTLE_SEC}s) ...")
    found = _arp_scan(args.host_ip)
    livox = [(ip, mac) for ip, mac in found if _is_livox_mac(mac)]
    other = [(ip, mac) for ip, mac in found if not _is_livox_mac(mac)]

    for ip, mac in livox:
        print(f"    {ip:16s}  {mac}  (Livox OUI)")
    for ip, mac in other:
        print(f"    {ip:16s}  {mac}")
    if not found:
        print("    no neighbors responded")

    actual_ip: str | None = None
    if pinged:
        actual_ip = args.lidar_ip
    elif len(livox) == 1:
        actual_ip = livox[0][0]
    elif len(found) == 1:
        actual_ip = found[0][0]

    if actual_ip is not None:
        ip_matches = actual_ip == args.lidar_ip
        lines = [
            "READY: Mid-360 host networking is configured.",
            f"  host {args.host_ip} on {chosen.name}  ->  lidar {actual_ip}",
            "",
            "Next:",
            f"  python {TEST_SCRIPT_PATH}",
        ]
        if not ip_matches:
            lines += [
                "",
                f"NOTE: lidar is at {actual_ip}, not the configured {args.lidar_ip}.",
                f'      Set lidar_ip="{actual_ip}" in fastlio_test.py\'s',
                "      FastLio2.blueprint(...) call.",
            ]
        _print_banner(lines)
        return 0

    if len(found) > 1:
        _print_banner(
            [
                "AMBIGUOUS: multiple neighbors on the lidar subnet.",
                "Pick the Livox one above and re-run with --lidar-ip <ip>",
                "(the script will then confirm and emit the READY banner).",
            ],
            char="!",
        )
        return 1

    _print_banner(
        [
            "NOT READY: no Mid-360 detected on the subnet.",
            "Things to check:",
            "  - Ethernet cable connected to the Mid-360",
            "  - Mid-360 powered (PoE+ or supplied 9-27V DC)",
            "  - Correct host port (re-run --interface <name> if wrong)",
            "  - Mid-360 not reconfigured to a different subnet",
        ],
        char="!",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
