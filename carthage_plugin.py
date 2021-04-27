from .layout import IaLayout
from carthage import *
import asyncio
import hadron.carthage.ansible
import carthage.ansible

import carthage

@inject(injector = Injector,
        config = ConfigLayout)
def  carthage_plugin(injector, config):
    injector.add_provider(layout.IaLayout)
    injector.add_provider(InjectionKey(carthage.ansible.AnsibleHostPlugin, name = "hadron"),
                          hadron.carthage.ansible.HadronHostPlugin)
    injector.add_provider(hadron.inventory.config.generator.ConfigCache)
    injector.add_provider(hadron.inventory.config.generator.hadron_config_dir_key,
                          config.output_dir+"/hadron")
    
    
