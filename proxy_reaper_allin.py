import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.player import Bot, Computer
from sc2.player import Human
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId

class ProxyReaperBot(sc2.BotAI):
    def __init__(self):
        self.combinedActions = []
        self.proxy_worker = None
        self.proxy_worker_tag = None

    async def on_step(self, iteration):
        if iteration == 0:
            self.proxy_worker = self.units(SCV).random
            self.proxy_worker_tag = self.proxy_worker.tag
        await self.distribute_workers()
        await self.build_depot()
        await self.move_scv()
        await self.build_rax()
        await self.build_gas()
        #looping through too fast. look into do_actions and figure out whats going on. Maybe don't use combinedActions?
        print(self.combinedActions)
        await self.do_actions(self.combinedActions)
        self.combinedActions = []

    async def move_scv(self):
            if self.units(SUPPLYDEPOT).ready and self.can_afford(BARRACKS):
                pass
            else:
                proxy_location = self.game_info.map_center.towards(self.enemy_start_locations[0], 25)
                self.combinedActions.append(self.proxy_worker.move(self.proxy_location))

    async def build_depot(self):
        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT) and self.supply_left < 4:
            ws = self.workers.gathering
            if ws:
                w = ws.furthest_to(ws.center)
                loc = await self.find_placement(SUPPLYDEPOT, w.position, placement_step=10)
                if loc:
                    self.combinedActions.append(w.build(SUPPLYDEPOT, loc))

    async def build_rax(self):
        """Builds proxy rax in a location near the opponent."""
        if self.units(SUPPLYDEPOT).ready.exists:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS) and self.units(BARRACKS).amount < 1:
                proxy_worker = self.units(SCV).find_by_tag(self.proxy_worker_tag)
                #The second parameter in towards method dictates how close to the game center the building is placed.
                # A 1 builds the rax as close to the center as possible.
                # A 90 will build as close to the enemy base as possible.
                pos = await self.find_placement(BARRACKS, near=self.game_info.map_center.towards(self.enemy_start_locations[0], 22))
                self.combinedActions.append(proxy_worker.build(BARRACKS, pos))
                    
    async def build_gas(self):
        """Builds refineries for gas collection."""
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS):
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 1:
                        worker = self.select_build_worker(gas.position)
                        self.combinedActions.append(worker.build(REFINERY, gas))           


                #Issue - when scv finishes making depot, scv needs to be sent to first rax location to build a 2nd rax. 
                #Issue - Start gas as soon as the rax starts.
                #Issue - SCV Production is not constant, but required.
    




#[4:05 PM] BuRny: @EJK you need to store the worker tag, move the worker to proxy location, and once you have the money, restore the unit from the tag
#[4:07 PM] BuRny: e.g. 
#if iteration == 0:
    #proxy_worker = self.workers.random
    # move worker to proxy location
    #self.proxy_worker_tag = proxy_worker.tag
# once you can afford it:
#proxy_worker = self.units.find_by_tag(self.proxy_worker_tag)
# build your barracks





































# helper functions

    # this checks if a ground unit can walk on a Point2 position
    def inPathingGrid(self, pos):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        assert isinstance(pos, (Point2, Point3, Unit))
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[(pos)] != 0

    # stolen and modified from position.py
    def neighbors4(self, position, distance=1):
        p = position
        d = distance
        return {
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        }

    # stolen and modified from position.py
    def neighbors8(self, position, distance=1):
        p = position
        d = distance
        return self.neighbors4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }

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


def main():
    # Multiple difficulties for enemy bots available https://github.com/Blizzard/s2client-api/blob/ce2b3c5ac5d0c85ede96cef38ee7ee55714eeb2f/include/sc2api/sc2_gametypes.h#L30
    sc2.run_game(sc2.maps.get("(2)CatalystLE"), [
        Bot(Race.Terran, ProxyReaperBot()),
        Computer(Race.Zerg, Difficulty.VeryHard)
    ], realtime=False)

if __name__ == '__main__':
    main()
