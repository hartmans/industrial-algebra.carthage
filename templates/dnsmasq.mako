bind-dynamic
interface=eth0
no-resolv
server=192.168.101.1
server=8.8.8.8
host-record=dns.algebra,10.37.0.2

%for l,h in net.v4_config.dhcp_ranges:
dhcp-range=${str(l)},${str(h)},1h
%endfor
%for l in net.network_links:
<%v4_config = l.merged_v4_config %>
%if v4_config.dhcp and l.mac:
%if v4_config.address:
dhcp-host=${l.mac},${v4_config.address},${l.machine.name},infinite
%else:
dhcp-host=${l.mac},${l.machine.name},1h
%endif
%endif
%endfor

dhcp-option=option:router,10.37.0.1
domain=algebra,10.37.0.0/24,local
