from .layout import IaLayout
from carthage import *
import asyncio

import carthage

@inject(injector = Injector)
def  carthage_plugin(injector):
    injector.add_provider(layout.IaLayout)
