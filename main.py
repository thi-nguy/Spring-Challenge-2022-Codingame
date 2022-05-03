import sys
import math

''' idea: 
- if threat_for = 2 (meaning monster will attack component base) --> WIND to ENEMY_BASE
- if shield_life != 0 --> Do not cast SPELL
- 


'''
def log(*args):
    for arg in args+('\n', ):
        print(arg, file=sys.stderr, end=' ', flush=True)

BASE_X, BASE_Y = [int(i) for i in input().split()]
HEROES_PER_PLAYER = int(input())
BASE_SIGHT = 6000
HERO_SIGHT = 2000
HERO_ATTACK_RANGE = 800
HERO_ATTACK_DAMAGE = 2
WIND_RADIUS = 1280
CONTROL_RADIUS = 2200
WIDTH = 17630
HEIGHT = 9000

class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def flip(self):
        return Pos(WIDTH - self.x, HEIGHT - self.y)
    
    def add(self,other):
        return Pos(self.x + other.x, self.y + other.y)
    def sub(self,other):
        return Pos(self.x - other.x, self.y - other.y)

    def distance(self, other):
        return (math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2))


AGGRO_RANGE = 5000
ENEMY_BASE_X = WIDTH
ENEMY_BASE_Y = HEIGHT
GUARDS_POSTS = [Pos(2734, 4678), Pos(5000, 5000), Pos(4837,1609)]
ATTACK_POST = Pos(13359, 7417)
if BASE_X != 0:
    ENEMY_BASE_X = 0
    ENEMY_BASE_Y = 0
    GUARDS_POSTS = [p.flip() for p in GUARDS_POSTS]
    ATTACK_POST = ATTACK_POST.flip()

MY_BASE = Pos(BASE_X, BASE_Y)
ENEMY_BASE = Pos(ENEMY_BASE_X, ENEMY_BASE_Y)
MAX_DISTANCE_FROM_BASE = 7700

class Monster:
    def __init__(self, id, pos, shield_life, is_controlled, health, velocity, near_base, threat_for):
        self.id = id
        self.pos = pos
        self.shield_life = shield_life
        self.is_controlled = is_controlled
        self.health = health
        self.velocity = velocity
        self.near_base = near_base
        self.threat_for = threat_for
        self.is_being_hunted = False
        self.is_being_winded = False

class Hero:
    def __init__(self, id, pos, shield_life, is_controlled):
        self.id = id
        self.pos = pos
        self.shield_life = shield_life
        self.is_controlled = is_controlled
        self.guard_post = GUARDS_POSTS[self.id % 3]
        self.job = "GUARD" # guard, defend, attack


class Game:
    def __init__(self):
        self.my_health = None
        self.enemy_health = None
        self.my_mana = None
        self.enemy_mana = None
        self.monsters = []
        self.my_heroes = []
        self.enemy_heroes = []
        self.orders = {} # ! dictionary

    def wait(self, hero):
        self.orders[hero.id] = "WAIT {}".format(hero.job)

    def move(self, hero, pos):
        self.orders[hero.id] = "MOVE {} {} {}".format(pos.x, pos.y, hero.job)

    def wind(self, hero, pos):
        self.orders[hero.id] = "SPELL WIND {} {} {}".format(pos.x, pos.y, hero.job)

    def control(self, hero, entity, pos):
        self.orders[hero.id] = "SPELL CONTROL {} {} {} {}".format(entity.id, pos.x, pos.y, hero.job)

    def shield(self, hero, entity):
        self.orders[hero.id] = "SPELL SHIELD {} {}".format(entity.id, hero.job)

    def decide(self):
        for hero in self.my_heroes:
            self.wait(hero)

        # orders of heros from BASE, by increasing distance
        temp_heroes = self.my_heroes[:] # copy
        temp_heroes.sort(key = lambda h: h.pos.distance(MY_BASE)) # min -> max distance to my BASE
        
        # Decide how many heroes to fall back to base and defend
        urgents = [monster for monster in game.monsters if monster.near_base == 1]
        # enemy_attackers = len([h for h in self.enemy_heroes if h.pos.distance(MY_BASE) < AGGRO_RANGE + HERO_SIGHT])
        num_defenders = min(len(urgents), HEROES_PER_PLAYER)
        
        for h in temp_heroes[:num_defenders]: # !
            h.job = "DEFEND"
        # Always have one attacks
        num_attackers = 1 # if num_defenders <= 1 else 0

        for h in temp_heroes[len(temp_heroes)-num_attackers:]: # !
            h.job = "ATTACK"
        
        for hero in self.my_heroes:
            if hero.job == "GUARD":
                post = hero.guard_post
                cands = [monster for monster in self.monsters if monster.pos.distance(hero.pos) <= HERO_SIGHT and not monster.is_being_hunted]
                if cands: # See monster
                    mon = min(cands, key=lambda m: m.pos.distance(hero.pos))
                    mon.is_being_hunted = True
                    self.move(hero, mon.pos)
                else: # See no monster, return to guard post
                    self.move(hero, post)

            elif hero.job == "ATTACK":
                urgent_threats_for_enemy = [mon for mon in self.monsters if mon.pos.distance(hero.pos) <= HERO_SIGHT and mon.near_base == 1 and mon.threat_for == 2 and mon.shield_life == 0]
                threats_for_enemy = [mon for mon in self.monsters if mon.pos.distance(hero.pos) <= WIND_RADIUS and  mon.threat_for == 2 and mon.shield_life == 0] # and mon.near_base == 1 
                non_threats_for_enemy = [mon for mon in self.monsters if mon.pos.distance(hero.pos) <= WIND_RADIUS and mon.threat_for != 2 and mon.shield_life == 0]
                if self.my_mana >= 10: # Cast spell
                    if urgent_threats_for_enemy:
                        m = min(urgent_threats_for_enemy, key=lambda m: m.pos.distance(ENEMY_BASE))
                        self.shield(hero, m)
                        continue
                    if threats_for_enemy:
                        self.wind(hero, ENEMY_BASE)
                        continue
                    if non_threats_for_enemy:
                        # m = min(non_threats_for_enemy, key=lambda m: m.pos.distance(ENEMY_BASE))
                        # self.control(hero, m, ENEMY_BASE)
                        # ! Change to wind instead of control since it's more effective (faster)
                        self.wind(hero, ENEMY_BASE)
                        continue
                    # ! does not need shield here because we can take advantage of enemy when they push us away from their base
                    # if hero.shield_life == 0 and any (hero.pos.distance(enemy.pos) <= CONTROL_RADIUS for enemy in self.enemy_heroes):
                    #     self.shield(hero, hero)
                    #     continue
                
                cands = [monster for monster in self.monsters if monster.pos.distance(ATTACK_POST) <= HERO_SIGHT  and not monster.is_being_hunted and monster.threat_for != 2]
                if cands: # kill
                    mon = min(cands, key=lambda m: m.pos.distance(hero.pos))
                    mon.is_being_hunted = True
                    self.move(hero, mon.pos)
                else: # Go to Attack post
                    self.move(hero, ATTACK_POST)

            elif hero.job == "DEFEND":
                if hero.shield_life == 0 and self.my_mana >= 10 and any (h.pos.distance(MY_BASE) < AGGRO_RANGE + HERO_SIGHT for h in self.enemy_heroes):
                    self.shield(hero, hero)
                    continue
                mon = min(urgents, key=lambda m: m.pos.distance(MY_BASE))
                if hero.pos.distance(mon.pos) <= WIND_RADIUS and self.my_mana >= 10 and mon.shield_life == 0: # and mon.is_being_winded == False 
                    mon.is_being_winded = True
                    wind_direction = (mon.pos.sub(MY_BASE)).add(hero.pos)
                    self.wind(hero, wind_direction)
                else:
                    self.move(hero, mon.pos)
                
        for hero in self.my_heroes:
            print(self.orders[hero.id])
        

# game loop
while True:
    game = Game()
    game.my_health, game.my_mana = [int(i) for i in input().split()]
    game.enemy_health, game.enemy_mana = [int(i) for i in input().split()]

    entity_count = int(input())  # Amount of heros and monsters you can see
    
    for i in range(entity_count):
        id, type, x, y, shield_life, is_controlled, health, vx, vy, near_base, threat_for = [int(j) for j in input().split()]
        if type == 0:
            game.monsters.append(Monster(id, Pos(x, y), shield_life, is_controlled, health, Pos(vx, vy), near_base, threat_for))
        else:
            hero = Hero(id, Pos(x, y), shield_life, is_controlled)
            if type == 1:
                game.my_heroes.append(hero)
            else:
                game.enemy_heroes.append(hero)

    game.decide()
