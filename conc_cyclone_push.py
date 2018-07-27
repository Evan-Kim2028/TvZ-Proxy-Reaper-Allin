import sc2
import random
from time import sleep
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, SUPPLYDEPOT, BARRACKS, ORBITALCOMMAND, REFINERY, FACTORY, REAPER \
, CYCLONE, BARRACKSREACTOR, MARINE, BARRACKSTECHLAB
from sc2.ids.ability_id import UPGRADETOORBITAL_ORBITALCOMMAND, CALLDOWNMULE_CALLDOWNMULE, BUILD_REACTOR_BARRACKS, BUILD_TECHLAB_BARRACKS

#adding unnesecary comment
class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        """Controls async function executions)"""
        await self.distribute_workers()
        await self.build_peon()
        await self.build_supply()
        await self.build_gas()
        await self.build_rax()
        await self.manage_bases_oc()
        await self.manage_bases_cc()
        await self.research_upgrade_addon()

    async def build_peon(self):
        """Manages peon (SCV) prodcution from Command Centers and Orbital Command Centers in each expansion."""
        for cc in self.units(COMMANDCENTER).ready:
            if self.units(BARRACKS).exists:
                break
            else:
                if self.can_afford(SCV) and not self.already_pending(SCV):
                    await self.do(cc.train(SCV))

    async def build_supply(self):
        """Manages Supply Depot production to prevent supply blocks."""
        if self.supply_left < 4 and self.can_afford(SUPPLYDEPOT):
            if not self.already_pending(SUPPLYDEPOT):
                await self.build(SUPPLYDEPOT, near=self.units(COMMANDCENTER).first)
    
    async def build_gas(self):
        """Builds refineries for gas collection."""
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS) and self.units(REFINERY).amount < 1:
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY):
                        worker = self.select_build_worker(gas.position)
                        await self.do(worker.build(REFINERY, gas))
            #Need to add 2nd gas timing

    async def build_rax(self):
        """Build and control building location of all Barracks."""
        if self.units(SUPPLYDEPOT).exists:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS) and self.units(BARRACKS).amount < 1:
                await self.build(BARRACKS, near=self.units(SUPPLYDEPOT).first)

    async def manage_bases_oc(self):
        """Controls OC upgrading, OC mule deployment, OC scan."""
        if self.units(BARRACKS).exists and self.units(COMMANDCENTER).exists:
            if self.can_afford(ORBITALCOMMAND) and not self.already_pending(ORBITALCOMMAND):
                await self.do(self.units(COMMANDCENTER).ready[0](UPGRADETOORBITAL_ORBITALCOMMAND))
        #Calls down Mule
        for oc in self.units(ORBITALCOMMAND).ready:
            abilities = await self.get_available_abilities(oc)
            if CALLDOWNMULE_CALLDOWNMULE in abilities:
                mf = self.state.mineral_field.closest_to(oc)
                await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

    async def manage_bases_cc(self):
        """Controls expanding to future bases."""
        if self.units(ORBITALCOMMAND).exists:
            if self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
                if self.units(REFINERY).amount < 1:
                    await self.expand_now()
   
    async def research_upgrade_addon(self):
        """Manages buildng addons and researchs upgrades from tech lab."""
        for rax in self.units(BARRACKS):
            abilities = await self.get_available_abilities(rax)
            if self.can_afford(BARRACKSREACTOR) and self.units(BARRACKSREACTOR).amount < 1:
                    if BUILD_REACTOR_BARRACKS in abilities:
                        await self.do(rax(BUILD_REACTOR_BARRACKS))

            
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