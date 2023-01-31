from .layout import IaLayout
from carthage import *
import asyncio
import carthage.ansible

import carthage

@inject(injector = Injector,
        config = ConfigLayout)
def  carthage_plugin(injector, config):
    injector.add_provider(layout.IaLayout)
    
    
