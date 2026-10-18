# OPNsense core 26.7.7: MVC API inventory vs. routerops.opnsense

Source: tag `26.7.7` of `opnsense/core` (`git ls-tree` / `git show` only). 126 files match `controllers/OPNsense/*/Api/*Controller.php`; 2 are abstract (`Firewall/FilterBase`, `Kea/Leases`) and not routable, so 124 routable API controllers in 20 areas. Stages from the spec section "Scope"; `tested` = entry in `meta/areas.yml` with `tested: ["26.7.7"]`.

## URL rule

From `Mvc/Router.php::parsePath` at 26.7.7: each URL segment is turned into a class name with `str_replace('_', '', ucwords($segment, '_'))`, the controller segment gets `Controller` appended, the action segment is `lcfirst(...)` + `Action`. So the API path is the CamelCase name split into snake_case at each inner capital: `DNatController` -> `d_nat`, `OneToOneController` -> `one_to_one`, `VlanSettingsController` -> `vlan_settings`, action `searchHostOverride` -> `search_host_override` (camelCase also works, since only the first letter is lowered). The module segment has a case-insensitive directory fallback (`resolveNamespace`), so `ipsec`, `dhcrelay`, `captiveportal` resolve to `IPsec`, `DHCRelay`, `CaptivePortal`. The controller segment has no such fallback (`is_file` on the expected path), so `dnat` would look for `DnatController.php` and fail on a case-sensitive filesystem (read from code, not tried live).

Kinds: `items` = ApiMutableModelControllerBase with search/get/add/set/del per item group (groups listed by action suffix); `settings` = get/set of a single model (the base `getAction`/`setAction`, or custom names); `service` = start/stop/restart/reconfigure/status; `ro/diag` = no persistent model writes (`:memory:` models count as no writes); `other` = said in the cell. Any ApiMutableModelControllerBase also inherits base `get`/`set`; a "+ general" note means the model has non-array top-level nodes reachable that way.

## Table 1: API controllers at 26.7.7

| Area | API path | Kind | Fits item/settings | Stage |
|---|---|---|---|---|
| Auth | auth/group | items (actions without suffix: search/get/add/set/del) | yes, custom action names | 0.x |
| Auth | auth/priv | other: search/getItem/setItem, keyed by privilege id, no add/del | partly, set-only per id | v1 |
| Auth | auth/user | items (user; apikey: search/add/del only) + upload/download, newOtpSeed | yes for user; API keys partly (no set) | v0 (user) |
| CaptivePortal | captiveportal/access | ro/diag (logon/logoff/status) | no | not in spec |
| CaptivePortal | captiveportal/service | service (reconfigure) | apply target | v1 |
| CaptivePortal | captiveportal/session | other (list/connect/disconnect sessions) | no | not in spec |
| CaptivePortal | captiveportal/settings | items (zone, plus toggle) | yes | v1 |
| CaptivePortal | captiveportal/template | items-like (search/get/del + `saveTemplate` file upload) | partly, upload of a zip | v1 |
| CaptivePortal | captiveportal/voucher | other (generate/expire/drop vouchers, no model) | no | not in spec |
| Core | core/backup | other (list/diff/revert/delete/download config backups) | no | not in spec |
| Core | core/dashboard | other (widget layout per user) | no | not in spec |
| Core | core/defaults | other (factory reset, per-section reset) | no | not in spec |
| Core | core/firmware | other (updates, plugin install/remove) + settings via `getOptions`/`set` (mirror, flavour, type, subscription) | partly, `getOptions` returns repository options, not the model shape (unverified) | not in spec |
| Core | core/hasync | settings (base get/set) + reconfigure | yes | 0.x (HA sync) |
| Core | core/hasync_status | service (remote services start/stop/restart) | no | not in spec |
| Core | core/initial_setup | other (wizard, `:memory:` model) | no | not in spec |
| Core | core/menu | ro/diag (menu tree, favourites) | no | not in spec |
| Core | core/service | service (generic start/stop/restart of any service) | no | not in spec |
| Core | core/snapshots | other: search/get/add/set/del/activate on ZFS boot environments via configd, no model | partly, item-shaped but no `saved` result (unverified) | v1 |
| Core | core/system | other (reboot/halt/status) | no | not in spec |
| Core | core/tunables | items (item) + reset/reconfigure | yes; search also lists unset system defaults (TunableField, unverified) | v1 |
| Cron | cron/service | service (reconfigure) | apply target | v0 |
| Cron | cron/settings | items (job) | yes | v0 |
| DHCRelay | dhcrelay/service | service (reconfigure) | apply target | v1 |
| DHCRelay | dhcrelay/settings | items (relay, dest) | yes | v1 |
| Diagnostics | diagnostics/activity | ro/diag | no | not in spec |
| Diagnostics | diagnostics/cpu_usage | ro/diag | no | not in spec |
| Diagnostics | diagnostics/dns | ro/diag (reverse lookup) | no | not in spec |
| Diagnostics | diagnostics/dns_diagnostics | ro/diag (`:memory:` model) | no | not in spec |
| Diagnostics | diagnostics/firewall | ro/diag + state kill/flush | no | not in spec |
| Diagnostics | diagnostics/interface | ro/diag + flushArp/delRoute | no | not in spec |
| Diagnostics | diagnostics/log | ro/diag (`__call` log reader) | no | not in spec |
| Diagnostics | diagnostics/lvtemplate | items (item: saved log-view filter templates, persistent) | yes | not in spec |
| Diagnostics | diagnostics/netflow | settings via `getconfig`/`setconfig` (key `netflow`, returns `saved`) + reconfigure | yes, custom action names | not in spec |
| Diagnostics | diagnostics/networkinsight | ro/diag | no | not in spec |
| Diagnostics | diagnostics/packet_capture | ro/diag (`:memory:` jobs) | no | not in spec |
| Diagnostics | diagnostics/ping | ro/diag (`:memory:` jobs) | no | not in spec |
| Diagnostics | diagnostics/portprobe | ro/diag (`:memory:`) | no | not in spec |
| Diagnostics | diagnostics/system | ro/diag | no | not in spec |
| Diagnostics | diagnostics/systemhealth | settings (base get/set: `enabled`) + RRD reads | yes | not in spec |
| Diagnostics | diagnostics/traceroute | ro/diag (`:memory:`) | no | not in spec |
| Diagnostics | diagnostics/traffic | ro/diag | no | not in spec |
| Dnsmasq | dnsmasq/leases | ro/diag | no | not in spec |
| Dnsmasq | dnsmasq/service | service | apply target | tested |
| Dnsmasq | dnsmasq/settings | items (host, domain, range, option, tag, boot) + general (get/set) + host upload/download | yes | host tested; general/domain/range/option v0; tag/boot 0.x |
| Firewall | firewall/alias | items (item) + general geoip (get/set) + import/export | yes | tested (alias); geoip general not in spec |
| Firewall | firewall/alias_util | other (live pf table add/delete/flush) | no, runtime only | not in spec |
| Firewall | firewall/category | items (item) + upload/download | yes | 0.x |
| Firewall | firewall/d_nat | items (rule) + move/toggleLog/upload | yes | v0 |
| Firewall | firewall/filter | items (rule) + move/toggleLog/upload | yes; search returns non-MVC rows | v0 |
| Firewall | firewall/filter_util | ro/diag (rule stats) | no | not in spec |
| Firewall | firewall/group | items (item) + reconfigure | yes | v1 |
| Firewall | firewall/migration | other (export/flush legacy rules) | no | not in spec |
| Firewall | firewall/npt | items (rule) | yes | v1 |
| Firewall | firewall/one_to_one | items (rule) | yes | v0 |
| Firewall | firewall/source_nat | items (rule) + custom get/set of `general.snat_mode` (outbound NAT mode) | yes | v0 (rule); snat_mode not in spec |
| Hostdiscovery | hostdiscovery/service | service + search (discovered hosts) | apply target | not in spec |
| Hostdiscovery | hostdiscovery/settings | settings (base get/set, `general`) | yes | not in spec |
| IDS | ids/service | service + rule update, alert queries | apply target | v1 |
| IDS | ids/settings | items (userRule, policy, policyRule) + general + custom ruleset actions (setRuleset, setRulesetproperties, toggleRule) | partly: items and general yes, rulesets/rule overrides custom | v1 |
| IPsec | ipsec/connections | items (connection, local, remote, child) + global toggle | yes | v0 |
| IPsec | ipsec/key_pairs | items (item) + genKeyPair | yes | 0.x |
| IPsec | ipsec/leases | ro/diag | no | not in spec |
| IPsec | ipsec/legacy_subsystem | other (apply legacy tunnels) | no | not in spec |
| IPsec | ipsec/manual_spd | items (no suffix: search/get/add/set/del) | yes | 0.x (SPD) |
| IPsec | ipsec/pools | items (no suffix) | yes | 0.x |
| IPsec | ipsec/pre_shared_keys | items (item) | yes | v0 |
| IPsec | ipsec/sad | ro/diag + delete SA | no | not in spec |
| IPsec | ipsec/service | service | apply target | v0 |
| IPsec | ipsec/sessions | other (connect/disconnect) | no | not in spec |
| IPsec | ipsec/settings | settings (base get/set: `general`, `charon`) | yes | not in spec |
| IPsec | ipsec/spd | ro/diag + delete | no | not in spec |
| IPsec | ipsec/tunnel | other (toggle legacy phase1/2) | no | not in spec |
| IPsec | ipsec/vti | items (no suffix) | yes | v0 |
| Interfaces | interfaces/assignment | items (item) + pending | yes, min 26.7.6 for IP fields | v0 |
| Interfaces | interfaces/bridge_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/gif_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/gre_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/lagg_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/loopback_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/neighbor_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/overview | ro/diag + reloadInterface | no | not in spec |
| Interfaces | interfaces/settings | settings (get + base set: offloading, IPv6 DUID, DHCP defaults) | yes | not in spec |
| Interfaces | interfaces/vip_settings | items (item) | yes | v0 |
| Interfaces | interfaces/vlan_settings | items (item) | yes | v0 |
| Interfaces | interfaces/vxlan_settings | items (item) | yes | 0.x |
| Interfaces | interfaces/wireless_settings | items (item: wlan clone devices) | yes; needs a wireless NIC to test | not in spec |
| Kea | kea/ctrl_agent | settings (get + base set) | yes | 0.x |
| Kea | kea/ddns | settings (get + base set) | yes | v1 |
| Kea | kea/dhcpv4 | items (subnet, reservation, option, peer) + general (get/set) + reservation upload | yes | general/subnet/reservation v0; peer 0.x (HA peer); option not in spec |
| Kea | kea/dhcpv6 | items (subnet, reservation, option, pdPool, peer) + general | yes | 0.x (DHCPv6) |
| Kea | kea/leases4 | ro/diag (+ delLease) | no | not in spec |
| Kea | kea/leases6 | ro/diag (+ delLease) | no | not in spec |
| Kea | kea/service | service | apply target | v0 |
| Monit | monit/service | service | apply target | 0.x |
| Monit | monit/settings | items (alert, service, test) + general | yes | 0.x |
| Monit | monit/status | ro/diag | no | not in spec |
| Ntpd | ntpd/service | ro/diag (meta, gps, status); no settings controller | no | NTP config is legacy (spec) |
| OpenVPN | openvpn/client_overwrites | items (no suffix) | yes | v0 |
| OpenVPN | openvpn/export | other (client export; `storePresets` writes export presets) | partly, presets only, custom action | not in spec |
| OpenVPN | openvpn/instances | items (no suffix: instance; staticKey) + genKey | yes | v0 |
| OpenVPN | openvpn/service | service (custom names: startService/stopService/restartService/reconfigure) + sessions | apply target (reconfigure) | v0 |
| Radvd | radvd/service | service (reconfigure) | apply target | v1 |
| Radvd | radvd/settings | items (entry) | yes | v1 |
| Routes | routes/gateway | ro/diag (gateway status) | no | not in spec |
| Routes | routes/routes | items (lowercase `route`: searchroute/getroute...) + reconfigure | yes | v0 |
| Routing | routing/group_settings | items (no suffix) + reconfigure | yes | v1 (gateway group) |
| Routing | routing/settings | items (gateway) + reconfigure | yes; search returns non-MVC rows | v0 |
| Syslog | syslog/service | service + reset/stats | apply target | v0 |
| Syslog | syslog/settings | items (destination; search action is `searchDestinations`) + general | yes | destination v0; general not in spec |
| TrafficShaper | trafficshaper/service | service (reconfigure, flushreload) | apply target | 0.x |
| TrafficShaper | trafficshaper/settings | items (pipe, queue, rule; search actions plural) + upload/download | yes | 0.x |
| Trust | trust/ca | items (no suffix) + generateFile | yes; create inputs volatile | v0 (as far as OpenVPN needs) / 0.x |
| Trust | trust/cert | items (no suffix) + generateFile | yes; create inputs volatile | v0 (as far as OpenVPN needs) / 0.x |
| Trust | trust/crl | other: ApiControllerBase, search/get/set/del keyed by CA `refid` | partly, keyed by CA, no add | v1 |
| Trust | trust/settings | settings (base get/set) + reconfigure | yes | 0.x |
| Unbound | unbound/diagnostics | ro/diag | no | not in spec |
| Unbound | unbound/overview | ro/diag | no | not in spec |
| Unbound | unbound/service | service + dnsbl, reconfigureGeneral | apply target | v0 |
| Unbound | unbound/settings | items (forward, hostOverride, hostAlias, acl, dnsbl) + general/advanced (get/set) | yes | general/hostOverride/hostAlias/forward/acl v0; dnsbl 0.x; advanced not in spec (unverified whether spec "general" means both) |
| Wireguard | wireguard/client | items (client = peer) + builder helpers | yes | v0 (peer) |
| Wireguard | wireguard/general | settings (base get/set: `enabled`) | yes | 0.x |
| Wireguard | wireguard/server | items (server) + keyPair | yes | v0 |
| Wireguard | wireguard/service | service | apply target | v0 |

Counts by kind (124 routable, mixed rows counted by their first kind): items 51, settings 10, service 17, ro/diag 29, other 17 (3 of them item-shaped: auth/priv, core/snapshots, trust/crl).

## Table 2: spec-named areas without an MVC API at 26.7.7

| Area (spec) | Where it lives at 26.7.7 |
|---|---|
| System general (hostname, domain, DNS servers, time zone, language) | `system_general.php` |
| Advanced: admin access (web GUI, SSH, console, sudo) | `system_advanced_admin.php` |
| Advanced: firewall and NAT (pf optimisation, bogons, adaptive timeouts, log defaults) | `system_advanced_firewall.php` |
| Advanced: miscellaneous (powerd, crypto/thermal, RAM disks, swap) | `system_advanced_misc.php` |
| Authentication servers (LDAP, RADIUS) | `system_authservers.php` |
| NTP (time servers, GPS, PPS) | `services_ntpd.php`, `services_ntpd_gps.php`, `services_ntpd_pps.php`; `ntpd/service` is status only |
| PPPoE / PPP devices | `interfaces_ppps.php`, `interfaces_ppps_edit.php` |
| Firewall schedules | `firewall_schedule.php`, `firewall_schedule_edit.php` |
| Firewall scrub / normalisation | `firewall_scrub.php`, `firewall_scrub_edit.php` |
| ISC DHCP | removed from core (no page, no controller) |

## Not coverable: no MVC API in 26.7.7

Method: every `src/www/*.php` at tag 26.7.7 (26 files) checked for `write_config(` or `$config[...] = `; 19 match. Feature grouping from the `$config[...]` keys each page writes. The 7 non-writing pages (`diag_authentication`, `firewall_rule_lookup`, `getserviceproviders`, `index`, `status_wireless`, `system_usermanager_settings_ldapacpicker`, `xmlrpc`) are tools or helpers. Gateway groups, DHCPv6, router advertisements, captive portal and SNMP have no legacy page left in core at 26.7.7 (SNMP is a plugin, `os-net-snmp`, not core).

| Feature | Legacy page(s) | MVC API at 26.7.7 | Named in spec |
|---|---|---|---|
| System general: hostname, domain, DNS servers, DNS override, search domain, time zone, language, theme | `system_general.php` | none | yes |
| Admin access: web GUI protocol/port/certificate, SSH, console, serial, sudo, auto-logout | `system_advanced_admin.php` | none | yes (advanced pages) |
| Firewall advanced: optimisation, bogons, static route bypass, adaptive timeouts, default log rules | `system_advanced_firewall.php` | none | yes (advanced pages) |
| Miscellaneous: powerd, crypto and thermal hardware, RAM disks for /tmp and /var, swap file, beep | `system_advanced_misc.php` | none | yes (advanced pages) |
| Authentication servers: LDAP, RADIUS | `system_authservers.php` | none | yes |
| NTP: time servers, GPS, PPS | `services_ntpd.php`, `services_ntpd_gps.php`, `services_ntpd_pps.php` | partial: `ntpd/service` reads status/GPS only | yes |
| PPP devices: PPPoE, PPTP, L2TP, modem | `interfaces_ppps.php`, `interfaces_ppps_edit.php` | partial: `interfaces/assignment` `type4` accepts `pppoe`/`ppp`/`pptp`/`l2tp`, `type6` accepts `pppoev6`; the PPP device itself (credentials, link) is legacy only | yes |
| Per-interface edit page (IPv4/IPv6 type, DHCP client, track6, PPP, wireless radio settings) | `interfaces.php` (2203 lines, still present) | partial: `interfaces/assignment` model has `type4`, `type6`, `ipaddr`, `ipaddrv6`, `dhcp*`, `dhcp6*`, `track6*`, gateways, `mtu`, `mss`, `spoofmac`, `blockpriv`, `blockbogons`, media; IPv6 tunnel types (6rd, 6to4) and wireless radio settings not seen in the model (unverified field by field) | no |
| Firewall schedules | `firewall_schedule.php`, `firewall_schedule_edit.php` | none | yes |
| Firewall scrub / normalisation rules and options | `firewall_scrub.php`, `firewall_scrub_edit.php` | none | yes |
| OpenDNS (DNS servers + dynamic IP update) | `services_opendns.php` | none | no |
| Config backup: backup count, restore from upload, RRD restore | `diag_backup.php` | partial: `core/backup` lists, diffs, reverts to a local backup, downloads; no upload/restore of a file | no |
| Crash reporter: contact e-mail, deployment type | `crash_reporter.php` | none | no |
| Own password and API token generation for the logged-in user (`user_allow_gen_token`) | `system_usermanager_passwordmg.php` | partial: `auth/user` sets any user's password and API keys; the `user_allow_gen_token` system flag is legacy only (unverified) | no |

## Not in spec but writable through item/settings

The real gaps: MVC model writes at 26.7.7 that fit `item` or `settings` and that no stage in the spec names.

Core
- `core/firmware` settings (mirror, flavour, type, subscription) via `getOptions`/`set`: partly, response shape unverified.

Diagnostics
- `diagnostics/lvtemplate` items: saved log-view templates.
- `diagnostics/netflow` settings via `getconfig`/`setconfig` (key `netflow`): NetFlow export, listening interfaces, capture.
- `diagnostics/systemhealth` settings: RRD collection on/off.

Firewall
- `firewall/alias` general: GeoIP database URL.
- `firewall/source_nat` general: outbound NAT mode (`snat_mode`, automatic/hybrid/manual); needed for any source NAT rule to take effect outside hybrid/manual mode.

Hostdiscovery
- `hostdiscovery/settings` general (hostwatch).

Interfaces
- `interfaces/settings`: global offloading, VLAN hardware filter, IPv6 DUID, DHCP defaults.
- `interfaces/wireless_settings` items: wlan clone devices (needs a wireless NIC to test).

IPsec
- `ipsec/settings`: `general` and `charon` (strongSwan tuning, enable/passthrough).

Kea
- `kea/dhcpv4` option items (DHCPv4 custom options); `kea/dhcpv6` options fall under the 0.x DHCPv6 entry.

OpenVPN
- `openvpn/export` presets via `storePresets`: partly, custom action, not a model item API.

Syslog
- `syslog/settings` general: local log retention, preserve days, max size.

Unbound
- `unbound/settings` advanced (and DNS-over-TLS forwarding `dots` if spec "forward" means only plain forwarding; check against plan 4c).

Auth
- `auth/user` API keys: search/add/del only (no set), partly.

Not verified: Firmware `getOptions` shape, Snapshots/CRL write results, Tunables search rows, the exact Unbound general vs. advanced split the spec intends.
