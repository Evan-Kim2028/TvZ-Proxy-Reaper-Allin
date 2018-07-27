import sc2
import random
from time import sleep
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, SUPPLYDEPOT, BARRACKS, ORBITALCOMMAND, REFINERY, FACTORY, REAPER, CYCLONE, BARRACKSREACTOR, MARINE \
, BARRACKSTECHLAB
from sc2.ids.ability_id import UPGRADETOORBITAL_ORBITALCOMMAND, CALLDOWNMULE_CALLDOWNMULE, BUILD_REACTOR_BARRACKS, BUILD_TECHLAB_BARRACKS

#Get rax, orbital command, and mule to drop
class TerranBot(sc2.BotAI):
    async def on_step(self, iteration):
        await self.distribute_workers()
        await self.build_workers()
        await self.build_refinery()
        await self.build_factory()
        await self.build_reactor()
        await self.build_marines()
        
        rax = self.units(BARRACKS).ready.idle
        cc = self.units(COMMANDCENTER).ready.idle
        if rax.exists:
            if cc.exists and self.can_afford(ORBITALCOMMAND):
                await self.do(self.units(COMMANDCENTER).ready.idle[0](UPGRADETOORBITAL_ORBITALCOMMAND))
        else:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                await self.build(BARRACKS, near=self.units(COMMANDCENTER).first)
            else:
                if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                    await self.build(BARRACKS, near=self.units(ORBITALCOMMAND).first)
                else:
                    if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT) and self.supply_left < 2 and cc.exists:
                        await self.build(SUPPLYDEPOT, near=self.units(COMMANDCENTER).first)
                    else:
                        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT) and self.supply_left < 6 and self.units(ORBITALCOMMAND).exists:
                            await self.build(SUPPLYDEPOT, near=self.units(ORBITALCOMMAND).first)
        if self.units(ORBITALCOMMAND).exists:
            """Calls down Mule"""
            for oc in self.units(ORBITALCOMMAND).ready:
                abilities = await self.get_available_abilities(oc)
                if CALLDOWNMULE_CALLDOWNMULE in abilities:
                    mf = self.state.mineral_field.closest_to(oc)
                    await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))
    async def build_workers(self):
        """Controls SCV production"""
        rax = self.units(BARRACKS).ready
        for cc in self.units(COMMANDCENTER).ready.noqueue:
            if self.can_afford(SCV) and self.workers.amount < 19 and not rax.exists:
                await self.do(cc.train(SCV))
        for oc in self.units(ORBITALCOMMAND).ready.noqueue:
            if self.can_afford(SCV) and self.workers.amount < 50 and self.units(ORBITALCOMMAND).ready.noqueue:
                await self.do(oc.train(SCV))

    async def build_refinery(self):
        for cc in self.units(COMMANDCENTER).ready:
            if self.already_pending(BARRACKS) and self.units(REFINERY).amount < 1:
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY):
                        worker = self.select_build_worker(gas.position)
                        await self.do(worker.build(REFINERY, gas))
        #"""builds 2nd gas"""
            if self.units(BARRACKSREACTOR).exists and self.units(REFINERY).amount < 2:
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY):
                        worker = self.select_build_worker(gas.position)
                        await self.do(worker.build(REFINERY, gas))
    
    async def build_factory(self):
        """builds factory for cyclone production."""
        if self.can_afford(FACTORY):
            if not self.already_pending(FACTORY) and self.units(FACTORY).amount < 1:
                await self.build(FACTORY, near=self.units(BARRACKS).first)
    async def build_reactor(self):
        """Builds reactor on first barracks"""
        if self.units(BARRACKS).ready.idle and self.units(BARRACKSREACTOR).amount < 1 and self.can_afford(BARRACKSREACTOR):
            for rax in self.units(BARRACKS).ready.idle:
                abilities = await self.get_available_abilities(rax)
                if BUILD_REACTOR_BARRACKS in abilities:
                    await self.do(rax(BUILD_REACTOR_BARRACKS))
                    if self.already_pending(BARRACKSREACTOR):
                        await self.build(BARRACKS, near=self.units(BARRACKSREACTOR).first)
                        
        if self.units(BARRACKSREACTOR).exists:
            if self.units(BARRACKS).ready.idle and self.units(BARRACKSTECHLAB).amount < 1 and self.can_afford(BARRACKSTECHLAB):
                for rax in self.units(BARRACKS).ready.idle:
                    abilities = await self.get_available_abilities(rax)
                    if BUILD_TECHLAB_BARRACKS in abilities:
                        await self.do(rax(BUILD_TECHLAB_BARRACKS))
                        if self.already_pending(BARRACKSTECHLAB):
                            await self.build(BARRACKS, near=self.units(BARRACKSTECHLAB).first)

        """Expands to natural after reactor starts building"""
        if self.already_pending(BARRACKSREACTOR) and self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
            await self.expand_now()
        if self.units(BARRACKSREACTOR).exists and self.can_afford(MARINE) and not self.already_pending(BARRACKSREACTOR):
            for rax in self.units(BARRACKS).idle:
                await self.do(rax.train(MARINE))
    async def build_marines(self):
        """Builds marines and adds a 2nd barracks"""
        if self.units(BARRACKSREACTOR).exists and self.can_afford(MARINE):
            for rax in self.units(BARRACKS).idle:
                    await self.do(rax.train(MARINE))
            if self.already_pending(COMMANDCENTER): #new line 
                if self.units(BARRACKS).amount < 1 and self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                    await self.build(BARRACKS, near=self.units(BARRACKSREACTOR.first))




run_game(maps.get("(2)DreamcatcherLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Terran, Difficulty.Easy)
    ], realtime=False)


#Code is too messy, more organized version can be found in conc_cyclone_push.py