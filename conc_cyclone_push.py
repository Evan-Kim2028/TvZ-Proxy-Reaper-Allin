import sc2
import random
from time import sleep
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SCV, SUPPLYDEPOT, BARRACKS, ORBITALCOMMAND, REFINERY, FACTORY, REAPER \
, CYCLONE, BARRACKSREACTOR, MARINE, BARRACKSTECHLAB
from sc2.ids.ability_id import UPGRADETOORBITAL_ORBITALCOMMAND, CALLDOWNMULE_CALLDOWNMULE, BUILD_REACTOR_BARRACKS, BUILD_TECHLAB_BARRACKS
from sc2.position import Point2, Point3
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

#adding unnesecary comment
class TerranBot(sc2.BotAI):
    def __init__(self):
        self.combinedActions = []

    async def on_step(self, iteration):
        """Controls async function executions)"""
        self.combinedActions = []

        #executs actions
        await self.distribute_workers()
        #Issue - distribute workers sucks. Look for Burny's custom distribute workers function in the mass reaper example.
        await self.build_peon()
        await self.build_supply()
        await self.build_gas()
        await self.build_rax()
        await self.manage_bases_oc()
        await self.manage_bases_cc()
        await self.research_upgrade_addon()
        await self.build_factory()
        await self.rax_production()
        await self.fac_production()
        await self.do_actions(self.combinedActions)

    async def build_peon(self):
        """Manages peon (SCV) prodcution from Command Centers and Orbital Command Centers in each expansion."""
        for cc in self.units(COMMANDCENTER).ready.noqueue:
            if self.can_afford(SCV) and not self.already_pending(SCV) and not self.units(BARRACKS).ready.exists:
                await self.do(cc.train(SCV))
        #Issue - SCVS don't build out of orbital command center

    async def build_supply(self):
        if self.supply_left < 5 and self.townhalls.exists and self.supply_used >= 14 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.units(UnitTypeId.SUPPLYDEPOT).not_ready.amount + self.already_pending(UnitTypeId.SUPPLYDEPOT) < 1:
            ws = self.workers.gathering
            if ws: # if workers found
                w = ws.furthest_to(ws.center)
                loc = await self.find_placement(UnitTypeId.SUPPLYDEPOT, w.position, placement_step=3)
                if loc: # if a placement location was found
                    # build exactly on that location
                    self.combinedActions.append(w.build(UnitTypeId.SUPPLYDEPOT, loc))

#old build_supply function that worked. Currently in the process of implementing combinedActions method
    #async def build_supply(self):
        #"""Manages Supply Depot production to prevent supply blocks."""
        #if self.supply_left < 4 and self.can_afford(SUPPLYDEPOT):
            #if not self.already_pending(SUPPLYDEPOT):
                #for cc in self.townhalls
                    #pos = await self.find_placement(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 7), min_distance=6)
                    #await self.build(SUPPLYDEPOT, pos)
    
    async def build_gas(self):
        """Builds refineries for gas collection."""
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS):
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 1:
                        worker = self.select_build_worker(gas.position)
                        await self.do(worker.build(REFINERY, gas))
                #Issue - Need to add in 2nd gas


    async def build_rax(self):
        """Build and control building location of all Barracks."""
        if self.units(SUPPLYDEPOT).exists:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS) and self.units(BARRACKS).amount < 1:
                pos = await self.find_placement(BARRACKS, near=self.units(SUPPLYDEPOT).first.position.towards(self.game_info.map_center, 4))
                await self.build(BARRACKS, pos)
                #for depot in self.units(SUPPLYDEPOT):
                    #pos = await self.find_placement(BARRACKS, near=depot.position.towards(self.game_info.map_center, 4))
                    #await self.build(BARRACKS, pos)

    async def manage_bases_oc(self):
        """Controls OC upgrading, OC mule deployment, OC scan."""
        if self.units(BARRACKS).exists and self.units(COMMANDCENTER).ready.exists:
            if self.can_afford(ORBITALCOMMAND) and not self.already_pending(ORBITALCOMMAND):
                await self.do(self.units(COMMANDCENTER)[0](UPGRADETOORBITAL_ORBITALCOMMAND))

        #Calls down Mule
        for oc in self.units(ORBITALCOMMAND).ready:
            abilities = await self.get_available_abilities(oc)
            if CALLDOWNMULE_CALLDOWNMULE in abilities:
                mf = self.state.mineral_field.closest_to(oc)
                await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

    async def manage_bases_cc(self):
        """Controls expanding to future bases."""
        if self.units(ORBITALCOMMAND).exists:
            print("OC exists")
            if self.can_afford(COMMANDCENTER) and not self.already_pending(COMMANDCENTER):
                await self.expand_now(building=COMMANDCENTER)
                #Issue - Expands too many times. There is currently no limit set.
   
    async def research_upgrade_addon(self):
        """Manages buildng addons and researchs upgrades from tech lab."""
        for rax in self.units(BARRACKS):
            abilities = await self.get_available_abilities(rax)
            if self.can_afford(BARRACKSREACTOR) and self.units(BARRACKSREACTOR).amount < 1:
                    if BUILD_REACTOR_BARRACKS in abilities:
                        await self.do(rax(BUILD_REACTOR_BARRACKS))
           
    async def build_factory(self):
        """Build and control building location of all Factories."""
        if self.units(BARRACKSREACTOR).exists:
            if self.can_afford(FACTORY) and not self.already_pending(FACTORY) and self.units(FACTORY).amount < 1:
                await self.build(FACTORY, near=self.units(BARRACKSREACTOR).first)

    async def rax_production(self):
        """Manages Reaper, Marine, and Maurauder production from Barracks."""
        if self.units(BARRACKSREACTOR).exists and self.can_afford(MARINE):
            for rax in self.units(BARRACKS).ready.noqueue:
                if self.can_afford(MARINE) and not self.already_pending(MARINE):
                    await self.do(rax.train(MARINE))
                    await self.do(rax.train(MARINE))
            

    async def fac_production(self):
        """Manages Cyclone production from Factories."""
        for fac in self.units(FACTORY).ready.noqueue:
            if self.can_afford(CYCLONE) and not self.already_pending(CYCLONE):
                await self.do(fac.train(CYCLONE))

    ###IMPORTANT DEFAULT FUNCTIONS###
    # distribute workers function rewritten, the default distribute_workers() function did not saturate gas quickly enough
    async def distribute_workers(self, performanceHeavy=True, onlySaturateGas=False):
        # expansion_locations = self.expansion_locations
        # owned_expansions = self.owned_expansions


        mineralTags = [x.tag for x in self.state.units.mineral_field]
        # gasTags = [x.tag for x in self.state.units.vespene_geyser]
        geyserTags = [x.tag for x in self.geysers]

        workerPool = self.units & []
        workerPoolTags = set()

        # find all geysers that have surplus or deficit
        deficitGeysers = {}
        surplusGeysers = {}
        for g in self.geysers.filter(lambda x:x.vespene_contents > 0):
            # only loop over geysers that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficitGeysers[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplusWorkers = self.workers.closer_than(10, g).filter(lambda w:w not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in geyserTags)
                # workerPool.extend(surplusWorkers)
                for i in range(-deficit):
                    if surplusWorkers.amount > 0:
                        w = surplusWorkers.pop()
                        workerPool.append(w)
                        workerPoolTags.add(w.tag)
                surplusGeysers[g.tag] = {"unit": g, "deficit": deficit}

        # find all townhalls that have surplus or deficit
        deficitTownhalls = {}
        surplusTownhalls = {}
        if not onlySaturateGas:
            for th in self.townhalls:
                deficit = th.ideal_harvesters - th.assigned_harvesters
                if deficit > 0:
                    deficitTownhalls[th.tag] = {"unit": th, "deficit": deficit}
                elif deficit < 0:
                    surplusWorkers = self.workers.closer_than(10, th).filter(lambda w:w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                    # workerPool.extend(surplusWorkers)
                    for i in range(-deficit):
                        if surplusWorkers.amount > 0:
                            w = surplusWorkers.pop()
                            workerPool.append(w)
                            workerPoolTags.add(w.tag)
                    surplusTownhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all([len(deficitGeysers) == 0, len(surplusGeysers) == 0, len(surplusTownhalls) == 0 or deficitTownhalls == 0]):
                # cancel early if there is nothing to balance
                return

        # check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficitGasCount = sum(gasInfo["deficit"] for gasTag, gasInfo in deficitGeysers.items() if gasInfo["deficit"] > 0)
        surplusCount = sum(-gasInfo["deficit"] for gasTag, gasInfo in surplusGeysers.items() if gasInfo["deficit"] < 0)
        surplusCount += sum(-thInfo["deficit"] for thTag, thInfo in surplusTownhalls.items() if thInfo["deficit"] < 0)

        if deficitGasCount - surplusCount > 0:
            # grab workers near the gas who are mining minerals
            for gTag, gInfo in deficitGeysers.items():
                if workerPool.amount >= deficitGasCount:
                    break
                workersNearGas = self.workers.closer_than(10, gInfo["unit"]).filter(lambda w:w.tag not in workerPoolTags and len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER] and w.orders[0].target in mineralTags)
                while workersNearGas.amount > 0 and workerPool.amount < deficitGasCount:
                    w = workersNearGas.pop()
                    workerPool.append(w)
                    workerPoolTags.add(w.tag)

        # now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for gTag, gInfo in deficitGeysers.items():
            if performanceHeavy:
                # sort furthest away to closest (as the pop() function will take the last element)
                workerPool.sort(key=lambda x:x.distance_to(gInfo["unit"]), reverse=True)
            for i in range(gInfo["deficit"]):
                if workerPool.amount > 0:
                    w = workerPool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        self.combinedActions.append(w.gather(gInfo["unit"], queue=True))
                    else:
                        self.combinedActions.append(w.gather(gInfo["unit"]))

        if not onlySaturateGas:
            # if we now have left over workers, make them mine at bases with deficit in mineral workers
            for thTag, thInfo in deficitTownhalls.items():
                if performanceHeavy:
                    # sort furthest away to closest (as the pop() function will take the last element)
                    workerPool.sort(key=lambda x:x.distance_to(thInfo["unit"]), reverse=True)
                for i in range(thInfo["deficit"]):
                    if workerPool.amount > 0:
                        w = workerPool.pop()
                        mf = self.state.mineral_field.closer_than(10, thInfo["unit"]).closest_to(w)
                        if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                            self.combinedActions.append(w.gather(mf, queue=True))
                        else:
                            self.combinedActions.append(w.gather(mf))



run_game(maps.get("(2)DreamcatcherLE"), [
    Bot(Race.Terran, TerranBot()),
    Computer(Race.Terran, Difficulty.Easy)
    ], realtime=False)


