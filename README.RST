Sam's Laptop Configuration
==========================

This is a `Carthage <https://github.com/hadron/carthage>`_ layout that
I use to set up my laptop for Carthage and Other development.  Chis is
provided as an example Carthage layout and to illustrate the sorts of
things that Carthage can do.

You probably cannot directly run this layout because it depends on  hadron-operations, a Proprietary plugin that Hadron uses.
The hadron-operations plugin is used only to install our internal software on the VMs that are intended for Hadron work.
If that were commented out, the other containers should work fine just with the free software parts of Carthage.

How to Run
**********

.. code-block:: shell

   carthage-runner --config config.yml --keep-machines --no-tmux

What This Layout Provides
*************************

This layout will set up several  containers in the local ``.algebra`` domain (the name of the hosting laptop is ``industrial-algebra``):

* dns.algebra: A local DNS and DHCP server

* apt.algebra: A server for the local Debian mirror

* hadron.algebra: A container with my employer's full development environment targeted on top of Debian bullseye

* buster.algebra: A VM with the development environment for my employer on top of a Debian 10 operating system

How it Works
************

Most of the work of the plugin is in ``python/layout.py``.
We'll talk about the overall taxonomy in a bit, but to  follow along, take a look there to start.

This layout depends on the following resources:

*OurMachine*
    A *MachineModel* that we use as the base of all the machines in the layout.  By inheriting from *SystemdNetworkModelMixin*, we indicate that Carthage should generate systemd-networkd condfiguration and arrange for that to be installed.

*OurImage*
    A *DebianContainerImage*   that is used as the default container image for any *MachineModel* realized as a container.  This image has my ssh key authorized as part of building the image

    
*BusterImage*
    A  container image based on buster rather than bullseye.

The layout also provides two *SystemDependencies*: by default every machine depends on ``dns.algebra`` and ``apt.algebra``.

The main layout is the class *IaLayout* (industrial algebra layout).

This layout is composed of two *Enclaves* (groupings of machines).

The *suchdamage_enclave* is an enclave for the real machines (the laptop).

The *industrial_algebra* machine model represents the laptop itself.  Setting *machine_implementation_key* to *LocalMachine* means that Carthage should manage the local machine.
In practice this means Carthage won't try to manage power and will use direct filesystem access to install files.
Since this machine directly includes a *NetworkConfig* (*NetworkConfigModel* is a subclass of *NetworkConfig*), it will directly use the supplied network config.

The *ia_enclave* is where most of the real work is done.  This enclave represents the containers and VMs on the system.

By default *machine_implementation_key* is set to *Container*, meaning that unless a machine overrides, Carthage will realize the machine with a systemd-nspawn container.
