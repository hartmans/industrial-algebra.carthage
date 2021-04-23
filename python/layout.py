from carthage.dependency_injection import *
from carthage import *
from carthage.modeling import *
from carthage.systemd import *
from carthage.container import *
from carthage.image import *
from carthage.machine import *
from carthage.debian import *
from carthage.network import V4Config

class OurMachine(MachineModel, SystemdNetworkModelMixin, template = True): pass

class IaLayout(CarthageLayout):

    
        
    class suchdamage_enclave(Enclave):

        domain = "suchdamage.org"

        class industrial_algebra(OurMachine):

            name = "industrial-algebra"
            add_provider(machine_implementation_key, dependency_quote(LocalMachine))

            class net_config(NetworkConfigModel):
                ia_net = injector_access("ia_network")
                add( 'blaptop',
                     net = ia_net,
                     mac = persistent_random_mac,
                     local_type = "bridge",
                     v4_config = V4Config(
                         dhcp = False,
                         address = "10.37.0.1",
                         dns_servers = ['10.37.0.2'],
                         domains = "algebra",
                         masquerade = True,
                         ),
                     )
                

            class Cust(MachineCustomization):

                @setup_task("Enable resolved")
                def enable_resolved(self):
                    host = self.host
                    host.shell("systemctl", "enable", "--now", "systemd-resolved")
                        

    class ia_enclave(Enclave):

        
        @globally_unique_key("ia_network")
        class ia_net(NetworkModel):

            bridge_name = "blaptop"

            v4_config = V4Config(
                network = "10.37.0.0/24",
                dhcp_ranges=[
                    ("10.37.0.10", "10.37.0.250"),
        ],
                dhcp = True)

        domain = "algebra"
        add_provider(machine_implementation_key, dependency_quote(Container))
        add_provider(container_image, DebianContainerImage)

        class net_config(NetworkConfigModel):

            ia_net = injector_access("ia_net")
            add("eth0", net = ia_net, mac = persistent_random_mac,
                )
            
        class apt(OurMachine):

            nginx_config = mako_task("apt_site.mako", output = "etc/nginx/sites-enabled/apt")

            container_args = ['--bind=/debian']
            
            class cust(ContainerCustomization):

                install_packages = install_stage1_packages_task(['nginx'])

                install_mako = install_mako_task('model')

        class dns(OurMachine):


            dnsmasq_conf_task = mako_task("dnsmasq.mako", output = "etc/dnsmasq.conf",
                                          net = InjectionKey("ia_network"))

            class Cust(ContainerCustomization):

                description = "Customization for dns.algebra"

                install_packages = install_stage1_packages_task(['dnsmasq'])

                install_mako = install_mako_task('model')

            class network_config(NetworkConfigModel):
                ia_net = injector_access("ia_network")
                    

                add('eth0', mac = persistent_random_mac,
                    net = ia_net,
                    v4_config = V4Config(
                        address = "10.37.0.2",
                        gateway = "10.37.0.1",
                        dns_servers = ["127.0.0.1"],
                        dhcp = False),
                    )
                    
            
