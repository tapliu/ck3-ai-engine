import random


def tick_economy(world):
    """每回合更新所有城池经济"""
    round_n = world.engine.round if world.engine else 0
    for cs in world.city_states.values():
        growth = 0.01 + cs.development / 5000
        cs.development = min(100, cs.development + growth)
        pop_growth = int(cs.population * (0.002 + cs.development / 20000))
        cs.population += pop_growth

        if round_n > 0 and round_n % 5 == 0:
            garrison_growth = int(cs.garrison * 0.05)
            cs.garrison += max(1, garrison_growth)

    # 势力征兵：每个控制城池的武将每5回合获得兵力
    if round_n > 0 and round_n % 5 == 0:
        for c in world.characters.values():
            if not c.alive:
                continue
            if not c.controlled_cities:
                c.troops += random.randint(10, 30)
                continue
            for city_name in c.controlled_cities:
                cs = world.city_states.get(city_name)
                if cs:
                    recruit = int(cs.population * 0.001 * (cs.development / 50))
                    c.troops += max(5, recruit)
            c.troops = min(c.troops, 50000)

    # 城池金收入
    if round_n > 0:
        for c in world.characters.values():
            if not c.alive:
                continue
            income = 0
            for city_name in c.controlled_cities:
                cs = world.city_states.get(city_name)
                if cs:
                    income += int(cs.development * 3 + cs.population / 1000)
            if income:
                c.gold += max(1, income)

    # 士气自然浮动
    if round_n > 0:
        for c in world.characters.values():
            if not c.alive:
                continue
            charm = c.i
            if c.morale < 30:
                gain = int(5 + charm * 5 / 100)
                c.morale = min(30, c.morale + gain)
            elif c.morale > 30:
                loss = int(10 - charm * 5 / 100)
                loss = max(3, loss)
                c.morale = max(30, c.morale - loss)


def try_expand(world, character):
    """AI势力尝试扩张：攻击相邻无主城池或敌对势力城池"""
    bases = character.controlled_cities[:] if character.controlled_cities else []
    if not bases and character.city:
        bases = [character.city]
    if not bases:
        return None

    targets = []
    for city_name in bases:
        for neighbor in world.city_connections.get(city_name, []):
            cs = world.city_states.get(neighbor)
            if not cs:
                continue
            if cs.controller is None or cs.controller != character.id:
                targets.append((neighbor, cs))

    if not targets:
        return None

    random.shuffle(targets)
    for target_name, cs in targets[:3]:
        if cs.controller is not None:
            defender = world.characters.get(cs.controller)
            if not defender or not defender.alive:
                continue
            if hasattr(world, 'alliances') and frozenset([character.id, cs.controller]) in world.alliances:
                continue
            if character.troops < defender.troops * 1.2:
                continue
        else:
            if character.troops < cs.garrison * 2:
                continue
        return target_name

    return None


def conquer_city(world, character, city_name, battle_result):
    """攻占城池"""
    cs = world.city_states.get(city_name)
    if not cs:
        return

    old_controller = cs.controller
    if old_controller and old_controller != character.id:
        old_char = world.characters.get(old_controller)
        if old_char:
            if city_name in old_char.controlled_cities:
                old_char.controlled_cities.remove(city_name)

    cs.controller = character.id
    if city_name not in character.controlled_cities:
        character.controlled_cities.append(city_name)

    cs.garrison = int(cs.garrison * 0.3)
    character.troops = int(character.troops * 0.8) + int(cs.garrison * 0.5)

    world._emit({
        "type": "conquest",
        "desc": f"{character.name}攻占{city_name}！{'击败了' + (world.characters[old_controller].name if old_controller and old_controller in world.characters else '原守军') if old_controller and old_controller != character.id else '占领了这座城池'}",
        "battle_result": battle_result,
    })
