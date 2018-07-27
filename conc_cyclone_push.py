import sc2
import random
from time import sleep
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, SUPPLYDEPOT, BARRACKS, ORBITALCOMMAND, REFINERY, FACTORY, REAPER \
, CYCLONE, BARRACKSREACTOR, MARINE, BARRACKSTECHLAB
from sc2.ids.ability_id import UPGRADETOORBITAL_ORBITALCOMMAND, CALLDOWNMULE_CALLDOWNMULE, BUILD_REACTOR_BARRACKS, BUILD_TECHLAB_BARRACKS

class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        """Controls async function executions)"""
        await self.distribute_workers()
        await self.build_peon()


    async def build_peon(self):
        """Manages peon (SCV) prodcution from Command Centers and Orbital Command Centers in each expansion."""
        for cc in self.units(COMMANDCENTER).is_idle:
                await self.do(cc.train(SCV))

    async def build_supply(self):
        """Manages Supply Depot production to prevent supply blocks."""
        for depot in self.units(SUPPLYDEPOT):
            if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
                if supply_left < 2:
                    await self.build(depot, near=self.units(COMMANDCENTER))

    async def build_rax(self):
        """Build and control building location of all Barracks."""


    async def manage_bases_cc(self):
        """Controls Base expansion, OC mule deployment, OC scan."""


    async def research_upgrade_addon(self):
        """Manages buildng addons and researchs upgrades from tech lab."""


    async def build_factory(self):
        """Build and control building location of all Factories."""


    async def rax_production(self):
        """Manages Reaper, Marine, and Maurauder production from Barracks."""


    async def fac_production(self):
        """Manages Cyclone production from Factories."""




run_game(maps.get("(2)DreamcatcherLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Terran, Difficulty.Easy)
    ], realtime=False)