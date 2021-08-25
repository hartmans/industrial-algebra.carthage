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

class OurMachine(MachineModel, SystemdNetworkModelMixin, template = True):

    @property
    def ip_address(self):
        return self.name #manage through the host name


class IaLayout(CarthageLayout, AnsibleModelMixin):

    layout_name = "industrial-algebra"

    apt_dependency = MachineDependency('apt.algebra')
    dns_dependency = MachineDependency('dns.algebra')
    
    @provides(container_image)
    class OurImage(DebianContainerImage):
        ssh_authorization = customization_task(SshAuthorizedKeyCustomizations)

    @no_instantiate()
    class BusterImage(OurImage.target):

        def __init__(self, **kwargs):
            super().__init__(name = "debian-buster",
                             distribution = "buster",
                             **kwargs)
            self.config_layout = self.injector.get_instance(ConfigLayout)
            self.config_layout.debian.distribution = "buster"

    add_provider(InjectionKey(BusterImage), BusterImage)
    # We don't need an origin
    add_provider(ssh_origin, None)



    class suchdamage_enclave(Enclave):

        domain = "suchdamage.org"

        class industrial_algebra(OurMachine):

            override_dependencies = True

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
            domain = "algebra"
            bridge_name = "blaptop"

            v4_config = V4Config(
                network = "10.37.0.0/24",
                dhcp_ranges=[
                    ("10.37.0.10", "10.37.0.250"),
        ],
                dhcp = True)

        domain = "algebra"
        add_provider(machine_implementation_key, dependency_quote(Container))


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

        class dns(OurMachine):

            override_dependencies = True

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


        class hadron(OurMachine):

            container_args=["--bind=/home/hartmans/hadron:/hadron"]

            network = injector_access('ia_network')
            @property
            def this_slot(self):
                import hadron.carthage
                slot =  hadron.carthage.fake_slot_for_model(self, netid = 1, role = "debian")
                slot.os = "Debian"
                slot.release = "bullseye"
                slot.track = "snapshot"
                return slot
            
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


        class buster(OurMachine):

            @provides(vm_image)
            @inject(ainjector = AsyncInjector, buster_container = BusterImage,
                    )
            async def vm_image(ainjector, buster_container):
                return await ainjector(
                    debian_container_to_vm,  buster_container, "debian-buster.raw",
                    "10G",
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
            
            class Cust(MachineCustomization):
                aces_distribution = ansible_playbook_task("ansible/playbooks/aces.yml")
                
