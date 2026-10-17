# OPNsense plugins and the MVC API

Snapshot of `opnsense/plugins` `master` on 17.10.2026: 102 plugins, 70 with an MVC API controller (`src/opnsense/mvc/app/controllers/OPNsense/*/Api/`). Only plugins with an MVC API can be managed with `item` or `settings`. Plugins that moved into core (WireGuard since 24.1, Dnsmasq, Kea, Unbound) are not listed here.

Most plugins name their actions after the item type (`searchNeighbor`, `addRecord`) instead of `search_item`/`add_item`; pass the names with `actions`.

## Plugins with an MVC API

| Plugin | Status |
|---|---|
| `benchmarks/iperf` | untested |
| `databases/redis` | untested |
| `devel/grid_example` | example plugin, not managed |
| `devel/helloworld` | example plugin, not managed |
| `dns/bind` | planned after v0 |
| `dns/ddclient` | planned after v0 |
| `dns/dnscrypt-proxy` | untested |
| `emulators/qemu-guest-agent` | untested |
| `ftp/tftp` | untested |
| `mail/postfix` | untested |
| `mail/rspamd` | untested |
| `net-mgmt/collectd` | untested |
| `net-mgmt/lldpd` | untested |
| `net-mgmt/net-snmp` | untested |
| `net-mgmt/netdata` | untested |
| `net-mgmt/nrpe` | untested |
| `net-mgmt/telegraf` | untested |
| `net-mgmt/zabbix-agent` | untested |
| `net-mgmt/zabbix-proxy` | untested |
| `net/chrony` | untested |
| `net/cloudflared` | untested |
| `net/freeradius` | untested |
| `net/frr` | planned after v0 |
| `net/ftp-proxy` | untested |
| `net/haproxy` | planned after v0 |
| `net/isc-dhcp` | untested |
| `net/mdns-repeater` | tested (v0) |
| `net/ndp-proxy-go` | untested |
| `net/netflector` | untested |
| `net/ntopng` | untested |
| `net/radsecproxy` | untested |
| `net/relayd` | untested |
| `net/shadowsocks` | untested |
| `net/siproxd` | untested |
| `net/sslh` | untested |
| `net/tayga` | untested |
| `net/turnserver` | untested |
| `net/udpbroadcastrelay` | untested |
| `net/vnstat` | untested |
| `net/wol` | untested |
| `net/zerotier` | untested |
| `security/acme-client` | tested (v0) |
| `security/clamav` | untested |
| `security/crowdsec` | untested |
| `security/etpro-telemetry` | untested |
| `security/maltrail` | untested |
| `security/netbird` | untested |
| `security/openconnect` | untested |
| `security/q-feeds-connector` | untested |
| `security/stunnel` | untested |
| `security/tailscale` | untested |
| `security/tinc` | untested |
| `security/tor` | untested |
| `security/wazuh-agent` | untested |
| `sysutils/apcupsd` | untested |
| `sysutils/beats` | untested |
| `sysutils/dec-hw` | untested |
| `sysutils/dmidecode` | untested |
| `sysutils/hw-probe` | untested |
| `sysutils/munin-node` | untested |
| `sysutils/node_exporter` | tested (v0) |
| `sysutils/nut` | untested |
| `sysutils/puppet-agent` | untested |
| `sysutils/smart` | untested |
| `www/c-icap` | untested |
| `www/caddy` | untested |
| `www/nginx` | untested |
| `www/OPNProxy` | untested |
| `www/squid` | untested |
| `www/web-proxy-sso` | untested |

## Plugins without an MVC API

Classified by hand; the per-plugin notes are not verified against each plugin's source.

| Plugin | Why no API | Could gain one? |
|---|---|---|
| `dns/rfc2136`, `net/igmp-proxy`, `net/upnp`, `www/cache` | configured through legacy PHP pages | yes, watch list |
| `sysutils/gdrive-backup`, `sysutils/git-backup`, `sysutils/mail-backup`, `sysutils/nextcloud-backup`, `sysutils/sftp-backup` | hook into the legacy backup page | yes, watch list |
| `sysutils/lcdproc-sdeclcd`, `vendor/sunnyvalley` | legacy page, or a vendor's own API | unlikely |
| `net/firewall-legacy`, `security/openvpn-legacy`, `security/strongswan-legacy` | kept for the old core pages, the MVC successors live in core | no |
| `misc/theme-*` (6), `security/intrusion-detection-content-*` (5), `sysutils/cpu-microcode`, `net/realtek-re`, `sysutils/virtualbox`, `sysutils/vmware`, `sysutils/xen`, `net/google-cloud-sdk`, `devel/debug` | nothing to configure | no |

A search of `opnsense/plugins` issues and pull requests on 17.10.2026 found no open work to move a watch-list plugin to MVC.
