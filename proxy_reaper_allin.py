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
            #Change from something other then random?
            self.proxy_worker_depot = self.units(SCV).random
            self.proxy_worker_tag = self.proxy_worker.tag
            self.proxy_worker_tag_depot = self.proxy_worker_depot.tag
        await self.distribute_workers()
        await self.build_depot()
        await self.move_scv()
        await self.build_rax()
        await self.build_gas()
        await self.build_scv()
        await self.rax_production()
        await self.upgrade_to_oc()
        await self.reaper_attack()
        print(self.combinedActions)
        await self.do_actions(self.combinedActions)
        self.combinedActions = []

    async def move_scv(self):
        if not self.already_pending(BARRACKS) and not self.units(SUPPLYDEPOT).amount >= 1:
            proxy_location = self.game_info.map_center.towards(self.enemy_start_locations[0], 30)
            self.combinedActions.append(self.proxy_worker.move(proxy_location))
            pass
        #2nd scv goes to proxy location in preparation to build 2nd rax. 
        if self.units(SUPPLYDEPOT).ready.exists and self.units(REFINERY).amount < 1:
            ws = self.units(SCV).find_by_tag(self.proxy_worker_tag_depot)
            print("need to move scv to 2nd proxy location")
            proxy_location = self.game_info.map_center.towards(self.enemy_start_locations[0], 30)
            #Fixed action looping continuously by adding 'and self.units(REFINERY).amount < 1' to if statement. 
            #Loop behavior stops aftter refinery gets built.
            self.combinedActions.append(ws.move(proxy_location))
            pass

    async def build_depot(self):
        ws = self.units(SCV).find_by_tag(self.proxy_worker_tag_depot)
        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT) and self.supply_left < 5:
            loc = await self.find_placement(SUPPLYDEPOT, ws.position)
            self.combinedActions.append(ws.build(SUPPLYDEPOT, loc))
            #Issue - Sometimes SCV builds depot outside of ramp and the first rax builds too slowly. 

    async def build_rax(self):
        """Builds proxy rax in a location near the opponent."""
        if self.units(SUPPLYDEPOT).ready.exists:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS) and self.units(BARRACKS).amount < 1:
                proxy_worker = self.units(SCV).find_by_tag(self.proxy_worker_tag)
                #The second parameter in towards method dictates how close to the game center the building is placed.
                # A 1 builds the rax as close to the center as possible.
                # A 90 will build as close to the enemy base as possible.
                pos = await self.find_placement(BARRACKS, near=self.game_info.map_center.towards(self.enemy_start_locations[0], 25))
                self.combinedActions.append(proxy_worker.build(BARRACKS, pos))

            #2nd rax gets built by scv that finished building the supply depot. Currently does not build 2nd rax
            if self.can_afford(BARRACKS) and self.units(BARRACKS).amount < 2:
                proxy_worker2 = self.units(SCV).find_by_tag(self.proxy_worker_tag_depot)
                pos = await self.find_placement(BARRACKS, near=self.game_info.map_center.towards(self.enemy_start_locations[0], 25))
                self.combinedActions.append(proxy_worker2.build(BARRACKS, pos))
        
    async def build_gas(self):
        """Builds refineries for gas collection."""
        for cc in self.units(COMMANDCENTER):
            if self.already_pending(BARRACKS):
                gas = self.state.vespene_geyser.closer_than(15.0, cc)
                for gas in gas:
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 1:
                        ws = self.workers.gathering
                        if ws:
                            w = ws.furthest_to(ws.center)
                            #worker = self.select_build_worker(gas.position)
                            self.combinedActions.append(w.build(REFINERY, gas)) 
                    if self.can_afford(REFINERY) and not self.already_pending(REFINERY) and self.units(REFINERY).amount < 2:
                        ws = self.workers.gathering
                        if ws:
                            w = ws.furthest_to(ws.center)
                            self.combinedActions.append(w.build(REFINERY, gas))          

    async def build_scv(self):
        """Manage SCV Production from CCs and OCs."""
        for cc in self.units(COMMANDCENTER).ready.noqueue:
            #SCV Production from CC
            if self.units(SCV).amount < 15:
                if self.can_afford(SCV) and not self.already_pending(SCV):
                    #Squeeze 1 scv out before 2nd rax/2nd gas are put down.
                    if self.units(BARRACKS).amount >= 1:
                        if self.already_pending(REFINERY):
                            pass
                        else:
                            self.combinedActions.append(cc.train(SCV))                        
                    if self.units(BARRACKS).amount >= 2 and not self.already_pending(REAPER) and not self.already_pending(SUPPLYDEPOT): # and not self.already_pending(REFINERY)
                        self.combinedActions.append(cc.train(SCV))
            #SCV PRoduction from OC
        for oc in self.units(ORBITALCOMMAND).ready.noqueue:
            if 15 < self.units(SCV).amount < 22:
                if self.can_afford(SCV) and not self.already_pending(SCV):
                    self.combinedActions.append(oc.train(SCV))

    async def rax_production(self):
        for rax in self.units(BARRACKS).ready.noqueue:
            if self.can_afford(REAPER) and not self.already_pending(REAPER):
                self.combinedActions.append(rax.train(REAPER))

    async def upgrade_to_oc(self):
        """Controls upgrade to OC, mule deployment, and scan usage."""
        if self.units(BARRACKS).exists and self.units(COMMANDCENTER).ready.exists:
            if self.units(BARRACKS).amount >= 2 and not self.already_pending(ORBITALCOMMAND) and self.units(SCV).amount >= 15:
                if self.can_afford(ORBITALCOMMAND) and not self.already_pending(ORBITALCOMMAND):
                    self.combinedActions.append(self.units(COMMANDCENTER)[0](UPGRADETOORBITAL_ORBITALCOMMAND))
                    pass
                #Mule drop
        for oc in self.units(ORBITALCOMMAND).ready:
            abilities = await self.get_available_abilities(oc)
            if CALLDOWNMULE_CALLDOWNMULE in abilities:
                mf = self.state.mineral_field.closest_to(oc)
                self.combinedActions.append(oc(CALLDOWNMULE_CALLDOWNMULE, mf))


    async def reaper_attack(self):
        for r in self.units(REAPER):
            allEnemyGroundUnits = self.known_enemy_units.not_flying.not_structure
#            self.combinedActions.append(r.move(random.choice(self.enemy_start_locations)))
#            pass
            #added .not_structure to filter out structures
#            allEnemyGroundUnits = self.known_enemy_units.not_flying.not_structure
            if allEnemyGroundUnits.exists:
                closestEnemy = allEnemyGroundUnits.closest_to(r)
                self.combinedActions.append(r.attack(closestEnemy))
                if r.position.distance_to(closestEnemy) <= 5:
                    if r.health_percentage < 40/60:
                        self.combinedActions.append(r.move(self.units(BARRACKS)[0]))
                        pass
            else:
                self.combinedActions.append(r.move(random.choice(self.enemy_start_locations)))
                pass






    





































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
        Computer(Race.Zerg, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()


