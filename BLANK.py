    async def reaper_micro(self):
        for r in self.units(UnitTypeId.REAPER):

            # move to range 15 of closest unit if reaper is below 20 hp and not regenerating
            enemyThreatsClose = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(15, r) # threats that can attack the reaper
            if r.health_percentage < 2/5 and enemyThreatsClose.exists:
                retreatPoints = self.neighbors8(r.position, distance=2) | self.neighbors8(r.position, distance=4)
                # filter points that are pathable
                retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsClose.closest_to(r)
                    retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    self.combinedActions.append(r.move(retreatPoint))
                    continue # continue for loop, dont execute any of the following

            # reaper is ready to attack, shoot nearest ground unit
            enemyGroundUnits = self.known_enemy_units.not_flying.closer_than(5, r) # hardcoded attackrange of 5
            if r.weapon_cooldown == 0 and enemyGroundUnits.exists:
                enemyGroundUnits = enemyGroundUnits.sorted(lambda x: x.distance_to(r))
                closestEnemy = enemyGroundUnits[0]
                self.combinedActions.append(r.attack(closestEnemy))
                continue # continue for loop, dont execute any of the following
            
            # attack is on cooldown, check if grenade is on cooldown, if not then throw it to furthest enemy in range 5
            reaperGrenadeRange = self._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
            enemyGroundUnitsInGrenadeRange = self.known_enemy_units.not_structure.not_flying.exclude_type([UnitTypeId.LARVA, UnitTypeId.EGG]).closer_than(reaperGrenadeRange, r)
            if enemyGroundUnitsInGrenadeRange.exists and (r.is_attacking or r.is_moving):
                # if AbilityId.KD8CHARGE_KD8CHARGE in abilities, we check that to see if the reaper grenade is off cooldown
                abilities = (await self.get_available_abilities(r))
                enemyGroundUnitsInGrenadeRange = enemyGroundUnitsInGrenadeRange.sorted(lambda x: x.distance_to(r), reverse=True)
                furthestEnemy = None
                for enemy in enemyGroundUnitsInGrenadeRange:
                    if await self.can_cast(r, AbilityId.KD8CHARGE_KD8CHARGE, enemy, cached_abilities_of_unit=abilities):
                        furthestEnemy = enemy
                        break
                if furthestEnemy:
                    self.combinedActions.append(r(AbilityId.KD8CHARGE_KD8CHARGE, furthestEnemy))
                    continue # continue for loop, don't execute any of the following

            # move towards to max unit range if enemy is closer than 4
            enemyThreatsVeryClose = self.known_enemy_units.filter(lambda x: x.can_attack_ground).closer_than(4.5, r) # hardcoded attackrange minus 0.5
            # threats that can attack the reaper
            if r.weapon_cooldown != 0 and enemyThreatsVeryClose.exists:
                retreatPoints = self.neighbors8(r.position, distance=2) | self.neighbors8(r.position, distance=4)               
                # filter points that are pathable by a reaper
                retreatPoints = {x for x in retreatPoints if self.inPathingGrid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsVeryClose.closest_to(r)
                    retreatPoint = max(retreatPoints, key=lambda x: x.distance_to(closestEnemy) - x.distance_to(r))
                    # retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    self.combinedActions.append(r.move(retreatPoint))
                    continue # continue for loop, don't execute any of the following

            # move to nearest enemy ground unit/building because no enemy unit is closer than 5
            allEnemyGroundUnits = self.known_enemy_units.not_flying
            if allEnemyGroundUnits.exists:
                closestEnemy = allEnemyGroundUnits.closest_to(r)
                self.combinedActions.append(r.move(closestEnemy))
                continue # continue for loop, don't execute any of the following

            # move to random enemy start location if no enemy buildings have been seen
            self.combinedActions.append(r.move(random.choice(self.enemy_start_locations)))
