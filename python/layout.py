from pathlib import Path
from carthage.dependency_injection import *
from carthage import *
from carthage.ansible import ansible_log
from carthage.modeling import *
from carthage.systemd import *
from carthage.container import *
from carthage.image import *
from carthage.machine import *
from carthage.debian import *
from carthage.network import V4Config
from carthage.ansible import ansible_playbook_task
from carthage.vm import Vm, vm_image
from carthage_base import *

from carthage_base import *
from carthage_base.aces import AcesIntegration, AcesMachine
root_path = Path(__file__).parent.parent
assignments_path = root_path/"assignments.yml"

class OurMachine(MachineModel, SystemdNetworkModelMixin, template = True):

    @property
    def ip_address(self):
        return self.name #manage through the host name


class IaLayout(CarthageLayout,  AnsibleModelMixin):

    aces_integration = AcesIntegration
    layout_name = "industrial-algebra"

    add_provider(persistent_seed_path, assignments_path)
    apt_dependency = MachineDependency('apt.algebra')
    dns_dependency = MachineDependency('dns.algebra')
    

    @no_instantiate()
    class BusterImage(DebianImage):
        distribution = "buster"

    add_provider(container_image, DebianImage)
    add_provider(InjectionKey(BusterImage), BusterImage)
    # We don't need an origin
    add_provider(ssh_origin, None)



    class suchdamage_enclave(Enclave):

        domain = "suchdamage.org"

        class industrial_algebra(OurMachine):

            override_dependencies = True
            add_provider(machine_implementation_key,  BareOrLocal)
            host="industrial-algebra"
            name = "industrial-algebra"

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
        host = "industrial-algebra"

        @globally_unique_key("ia_network")
        class ia_net(NetworkModel):
            domain = "algebra"
            bridge_name = "blaptop"

            v4_config = V4Config(
                network = "10.37.0.0/24",
                dhcp_ranges=[
                    ("10.37.0.30", "10.37.0.250"),
        ],
                dhcp = True,
                pool = ('10.37.0.5', '10.37.0.25'),
                domains="algebra",
                )

        domain = "algebra"
        add_provider(machine_implementation_key, HostedContainer)


        class net_config(NetworkConfigModel):

            ia_net = injector_access("ia_net")
            add("eth0", net = ia_net, mac = persistent_random_mac,
                )

        class apt(OurMachine):

            disable_system_dependency(MachineDependency("apt.algebra"))
            
            
            nginx_config = mako_task("apt_site.mako", output = "etc/nginx/sites-enabled/apt")

            container_args = ['--bind=/debian']

            class cust(ContainerCustomization):

                install_packages = install_stage1_packages_task(['nginx'])

                install_mako = install_mako_task('model')

        class dns(OurMachine, DhcpRole):

            ip_address ="10.37.0.2"
            
            mirror_tracking  = DebianMirrorTracker
            override_dependencies = True



            class network_config(NetworkConfigModel):
                ia_net = injector_access("ia_network")


                add('eth0', mac = persistent_random_mac,
                    net = ia_net,
                    v4_config = V4Config(
                        address = "10.37.0.2",
                        gateway = "10.37.0.1",
                        dns_servers = ["192.168.101.1","8.8.8.8"],
                        dhcp = False),
                    )


        class hadron(OurMachine, AcesMachine):

            container_args=["--bind=/home/hartmans/hadron:/hadron"]

            network = injector_access('ia_network')
            
            class Cust(MachineCustomization):

                @setup_task("make user")
                async def make_user(self):
                    await self.ssh("useradd -u 8042 -m hartmans",
                                   _bg = True,
                                   _bg_exc = False)

                @setup_task("install packages")
                async def install_dev_packages(self):
                    await self.ssh("apt update",
                                   _bg = True, _bg_exc = False)
                    await self.ssh('apt -y install ansible git emacs-nox python3-sqlalchemy python3-tornado python3-pyvmomi rsync',
                                   _bg = True,
                                   _bg_exc = False)
                    async with self.filesystem_access() as path:
                        home_hartmans = Path(path)/"home/hartmans"
                        home_hartmans.joinpath("hadron").symlink_to("/hadron")

                aces_distribution = ansible_playbook_task("ansible/playbooks/aces.yml")
                
        class test(OurMachine):
            container_args=["--bind=/home/hartmans/hadron:/hadron", "--bind=/dev/kvm", "--bind=/dev/fuse"]

            class Cust(MachineCustomization):

                @setup_task("make user")
                async def make_user(self):
                    await self.ssh("useradd -u 8042 -m hartmans",
                                   _bg = True,
                                   _bg_exc = False)

                @setup_task("install packages")
                async def install_dev_packages(self):
                    await self.ssh("apt update",
                                   _bg = True, _bg_exc = False)
                    await self.ssh('apt -y install ansible git emacs-nox python3-sqlalchemy python3-tornado python3-pyvmomi rsync',
                                   _bg = True,
                                   _bg_exc = False)
                    async with self.filesystem_access() as path:
                        home_hartmans = Path(path)/"home/hartmans"
                        home_hartmans.joinpath("hadron").symlink_to("/hadron")


        class bookworm(OurMachine):

            @provides(vm_image)
            @inject(ainjector = AsyncInjector, container = DebianImage,
                    )
            async def vm_image(ainjector, container):
                return await ainjector(
                    debian_container_to_vm,  container, "debian-bullseye.raw",
                    "20G",
                    classes = "+SERIAL,CLOUD_INIT,OPENROOT")
            network  = injector_access("ia_network")
            
            @property
            def this_slot(self):
                import hadron.carthage
                slot =  hadron.carthage.fake_slot_for_model(self, netid = 1, role = "debian")
                return slot

            cloud_init = True
            add_provider(machine_implementation_key, dependency_quote(Vm))
            add_provider(ansible_log, "/srv/images/test/ansible.log")
            
#            class Cust(MachineCustomization):
#                aces_distribution = ansible_playbook_task("ansible/playbooks/aces.yml")
                
    class DenverEnclave(Enclave):

        domain = "watertown.aces-aoe.net"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.injector.add_provider(ConfigLayout)
            config = self.injector.get_instance(ConfigLayout)
            config.debian.mirror = "https://deb.debian.org/debian"
            

        class carthage(OurMachine, AcesMachine, CarthageServerRole):
            ip_address = "carthage.watertown.aces-aoe.net"
            add_provider(machine_implementation_key, dependency_quote(BareMetalMachine))
            network = injector_access("ia_network") # This is a lie but might work
