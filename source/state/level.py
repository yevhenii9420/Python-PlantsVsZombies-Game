__author__ = 'marble_xu'

import os
import json
import pygame as pg
from .. import tool
from .. import constants as c
from ..component import map, plant, zombie, menubar

class Level(tool.State):
    def __init__(self):
        tool.State.__init__(self)
    
    def startup(self, current_time, persist):
        self.game_info = persist
        self.persist = self.game_info
        self.game_info[c.CURRENT_TIME] = current_time
        self.map_y_len = c.GRID_Y_LEN
        self.map = map.Map(c.GRID_X_LEN, self.map_y_len)
        
        self.loadMap()
        self.state = c.CHOOSE
        self.initChoose()
        self.setupBackground()

    def loadMap(self):
        map_file = 'level_' + str(self.game_info[c.LEVEL_NUM]) + '.json'
        file_path = os.path.join('source', 'data', 'map', map_file)
        f = open(file_path)
        self.map_data = json.load(f)
        f.close()
    
    def setupBackground(self):
        img_index = self.map_data[c.BACKGROUND_TYPE]
        self.background = tool.GFX[c.BACKGROUND_NAME][img_index]
        self.bg_rect = self.background.get_rect()

        self.level = pg.Surface((self.bg_rect.w, self.bg_rect.h)).convert()
        self.viewport = tool.SCREEN.get_rect(bottom=self.bg_rect.bottom)
        self.viewport.x += c.BACKGROUND_OFFSET_X
    
    def setupGroups(self):
        self.sun_group = pg.sprite.Group()
        self.head_group = pg.sprite.Group()

        self.plant_groups = []
        self.zombie_groups = []
        self.bullet_groups = []
        for i in range(self.map_y_len):
            self.plant_groups.append(pg.sprite.Group())
            self.zombie_groups.append(pg.sprite.Group())
            self.bullet_groups.append(pg.sprite.Group())
    
    def setupZombies(self):
        def takeTime(element):
            return element[0]

        self.zombie_list = []
        for data in self.map_data[c.ZOMBIE_LIST]:
            self.zombie_list.append((data['time'], data['name'], data['map_y']))
        self.zombie_start_time = 0
        self.zombie_list.sort(key=takeTime)

    def setupCars(self):
        self.cars = []
        for i in range(self.map_y_len):
            _, y = self.map.getMapGridPos(0, i)
            self.cars.append(plant.Car(-25, y+20, i))

    def update(self, surface, current_time, mouse_pos, mouse_click):
        self.current_time = self.game_info[c.CURRENT_TIME] = current_time
        if self.state == c.CHOOSE:
            self.choose(mouse_pos, mouse_click)
        elif self.state == c.PLAY:
            self.play(mouse_pos, mouse_click)

        self.draw(surface)

    def initChoose(self):
        self.panel = menubar.Panel(menubar.all_card_list, self.map_data[c.INIT_SUN_NAME])

    def choose(self, mouse_pos, mouse_click):
        if mouse_pos and mouse_click[0]:
            self.panel.checkCardClick(mouse_pos)
            if self.panel.checkStartButtonClick(mouse_pos):
                self.state = c.PLAY
                self.initPlay(self.panel.getSelectedCards())

    def initPlay(self, card_list):
        self.menubar = menubar.MenuBar(card_list, self.map_data[c.INIT_SUN_NAME])
        self.drag_plant = False
        self.hint_image = None
        self.hint_plant = False
        self.produce_sun = True
        self.sun_timer = self.current_time

        self.removeMouseImage()
        self.setupGroups()
        self.setupZombies()
        self.setupCars()

    def play(self, mouse_pos, mouse_click):
        if self.zombie_start_time == 0:
            self.zombie_start_time = self.current_time
        elif len(self.zombie_list) > 0:
            data = self.zombie_list[0]
            if  data[0] <= (self.current_time - self.zombie_start_time):
                self.createZombie(data[1], data[2])
                self.zombie_list.remove(data)

        for i in range(self.map_y_len):
            self.bullet_groups[i].update(self.game_info)
            self.plant_groups[i].update(self.game_info)
            self.zombie_groups[i].update(self.game_info)
        self.head_group.update(self.game_info)
        self.sun_group.update(self.game_info)
        
        if not self.drag_plant and mouse_pos and mouse_click[0]:
            result = self.menubar.checkCardClick(mouse_pos)
            if result:
                self.setupMouseImage(result[0], result[1])
        elif self.drag_plant:
            if mouse_click[1]:
                self.removeMouseImage()
            elif mouse_click[0]:
                if self.menubar.checkMenuBarClick(mouse_pos):
                    self.removeMouseImage()
                else:
                    self.addPlant()
            elif mouse_pos is None:
                self.setupHintImage()
        
        if self.produce_sun:
            if(self.current_time - self.sun_timer) > c.PRODUCE_SUN_INTERVAL:
                self.sun_timer = self.current_time
                map_x, map_y = self.map.getRandomMapIndex()
                x, y = self.map.getMapGridPos(map_x, map_y)
                self.sun_group.add(plant.Sun(x, 0, x, y))
            if not self.drag_plant and mouse_pos and mouse_click[0]:
                for sun in self.sun_group:
                    if sun.checkCollision(mouse_pos[0], mouse_pos[1]):
                        self.menubar.increaseSunValue(c.SUN_VALUE)

        for car in self.cars:
            car.update(self.game_info)

        self.menubar.update(self.current_time)

        self.checkBulletCollisions()
        self.checkZombieCollisions()
        self.checkPlants()
        self.checkCarCollisions()
        self.checkGameState()

    def createZombie(self, name, map_y):
        x, y = self.map.getMapGridPos(0, map_y)
        if name == c.NORMAL_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NormalZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.CONEHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.ConeHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.BUCKETHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.BucketHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.FLAG_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.FlagZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.NEWSPAPER_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NewspaperZombie(c.ZOMBIE_START_X, y, self.head_group))

    def canSeedPlant(self):
        x, y = pg.mouse.get_pos()
        return self.map.showPlant(x, y)
        
    def addPlant(self):
        pos = self.canSeedPlant()
        if pos is None:
            return

        if self.hint_image is None:
            self.setupHintImage()
        x, y = self.hint_rect.x, self.hint_rect.bottom
        map_x, map_y = self.map.getMapIndex(x, y)
        if self.plant_name == c.SUNFLOWER:
            self.plant_groups[map_y].add(plant.SunFlower(x, y, self.sun_group))
        elif self.plant_name == c.PEASHOOTER:
            self.plant_groups[map_y].add(plant.PeaShooter(x, y, self.bullet_groups[map_y]))
        elif self.plant_name == c.SNOWPEASHOOTER:
            self.plant_groups[map_y].add(plant.SnowPeaShooter(x, y, self.bullet_groups[map_y]))
        elif self.plant_name == c.WALLNUT:
            self.plant_groups[map_y].add(plant.WallNut(x, y))
        elif self.plant_name == c.CHERRYBOMB:
            self.plant_groups[map_y].add(plant.CherryBomb(x, y))
        elif self.plant_name == c.THREEPEASHOOTER:
            self.plant_groups[map_y].add(plant.ThreePeaShooter(x, y, self.bullet_groups, map_y))
        elif self.plant_name == c.REPEATERPEA:
            self.plant_groups[map_y].add(plant.RepeaterPea(x, y, self.bullet_groups[map_y]))
        elif self.plant_name == c.CHOMPER:
            self.plant_groups[map_y].add(plant.Chomper(x, y))
        elif self.plant_name == c.PUFFMUSHROOM:
            self.plant_groups[map_y].add(plant.PuffMushroom(x, y, self.bullet_groups[map_y]))
        elif self.plant_name == c.POTATOMINE:
            self.plant_groups[map_y].add(plant.PotatoMine(x, y))
        elif self.plant_name == c.SQUASH:
            self.plant_groups[map_y].add(plant.Squash(x, y))

        self.menubar.decreaseSunValue(self.plant_cost)
        self.menubar.setCardFrozenTime(self.plant_name)
        self.map.setMapGridType(map_x, map_y, c.MAP_EXIST)
        self.removeMouseImage()
        #print('addPlant map[%d,%d], grid pos[%d, %d] pos[%d, %d]' % (map_x, map_y, x, y, pos[0], pos[1]))

    def setupHintImage(self):
        pos = self.canSeedPlant()
        if pos and self.mouse_image:
            if (self.hint_image and pos[0] == self.hint_rect.x and
                pos[1] == self.hint_rect.y):
                return
            width, height = self.mouse_rect.w, self.mouse_rect.h
            image = pg.Surface([width, height])
            image.blit(self.mouse_image, (0, 0), (0, 0, width, height))
            image.set_colorkey(c.BLACK)
            image.set_alpha(128)
            self.hint_image = image
            self.hint_rect = image.get_rect()
            self.hint_rect.centerx = pos[0]
            self.hint_rect.bottom = pos[1]
            self.hint_plant = True
        else:
            self.hint_plant = False

    def setupMouseImage(self, plant_name, plant_cost):
        frame_list = tool.GFX[plant_name]
        if plant_name in tool.PLANT_RECT:
            data = tool.PLANT_RECT[plant_name]
            x, y, width, height = data['x'], data['y'], data['width'], data['height']
        else:
            x, y = 0, 0
            rect = frame_list[0].get_rect()
            width, height = rect.w, rect.h

        if plant_name == c.POTATOMINE or plant_name == c.SQUASH:
            color = c.WHITE
        else:
            color = c.BLACK
        self.mouse_image = tool.get_image(frame_list[0], x, y, width, height, color, 1)
        self.mouse_rect = self.mouse_image.get_rect()
        pg.mouse.set_visible(False)
        self.drag_plant = True
        self.plant_name = plant_name
        self.plant_cost = plant_cost

    def removeMouseImage(self):
        pg.mouse.set_visible(True)
        self.drag_plant = False
        self.mouse_image = None
        self.hint_image = None
        self.hint_plant = False

    def checkBulletCollisions(self):
        collided_func = pg.sprite.collide_circle_ratio(0.7)
        for i in range(self.map_y_len):
            for bullet in self.bullet_groups[i]:
                if bullet.state == c.FLY:
                    zombie = pg.sprite.spritecollideany(bullet, self.zombie_groups[i], collided_func)
                    if zombie and zombie.state != c.DIE:
                        zombie.setDamage(bullet.damage, bullet.ice)
                        bullet.setExplode()
    
    def checkZombieCollisions(self):
        collided_func = pg.sprite.collide_circle_ratio(0.7)
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                plant = pg.sprite.spritecollideany(zombie, self.plant_groups[i], collided_func)
                if plant and zombie.state == c.WALK:
                    zombie.setAttack(plant)
                    plant.setAttacked()

    def checkCarCollisions(self):
        collided_func = pg.sprite.collide_circle_ratio(0.8)
        for car in self.cars:
            zombies = pg.sprite.spritecollide(car, self.zombie_groups[car.map_y], False, collided_func)
            for zombie in zombies:
                if zombie and zombie.state != c.DIE:
                    car.setWalk()
                    zombie.setDie()
            if car.dead:
                self.cars.remove(car)

    def boomZombies(self, x, map_y, y_range, x_range):
        for i in range(self.map_y_len):
            if abs(i - map_y) > y_range:
                continue
            for zombie in self.zombie_groups[i]:
                if abs(zombie.rect.x - x) <= x_range:
                    zombie.setBoomDie()

    def killPlant(self, plant):
        x, y = plant.getPosition()
        map_x, map_y = self.map.getMapIndex(x, y)
        self.map.setMapGridType(map_x, map_y, c.MAP_EMPTY)
        if (plant.name == c.CHERRYBOMB or
            (plant.name == c.POTATOMINE and not plant.is_init)):
            self.boomZombies(plant.rect.centerx, map_y, plant.explode_y_range,
                            plant.explode_x_range)
        plant.kill()

    def checkPlant(self, plant, i):
        zombie_len = len(self.zombie_groups[i])
        if plant.name == c.THREEPEASHOOTER:
            if plant.state == c.IDLE:
                if zombie_len > 0:
                    plant.setAttack()
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    plant.setAttack()
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    plant.setAttack()
            elif plant.state == c.ATTACK:
                if zombie_len > 0:
                    pass
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    pass
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    pass
                else:
                    plant.setIdle()
        elif plant.name == c.CHOMPER:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        elif plant.name == c.POTATOMINE:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack()
                    break
        elif plant.name == c.SQUASH:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        else:
            if (plant.state == c.IDLE and zombie_len > 0):
                for zombie in self.zombie_groups[i]:
                    if plant.canAttack(zombie):
                        plant.setAttack()
                        break
            elif (plant.state == c.ATTACK and zombie_len == 0):
                plant.setIdle()

        if plant.health <= 0:
            self.killPlant(plant)

    def checkPlants(self):
        for i in range(self.map_y_len):
            for plant in self.plant_groups[i]:
                self.checkPlant(plant, i)

    def checkVictory(self):
        if len(self.zombie_list) > 0:
            return False
        for i in range(self.map_y_len):
            if len(self.zombie_groups[i]) > 0:
                return False
        return True
    
    def checkLose(self):
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                if zombie.rect.right < 0:
                    return True
        return False

    def checkGameState(self):
        if self.checkVictory():
            self.game_info[c.LEVEL_NUM] += 1
            self.next = c.GAME_VICTORY
            self.done = True
        elif self.checkLose():
            self.next = c.GAME_LOSE
            self.done = True

    def drawMouseShow(self, surface):
        if self.hint_plant:
            surface.blit(self.hint_image, self.hint_rect)
        x, y = pg.mouse.get_pos()
        self.mouse_rect.centerx = x
        self.mouse_rect.centery = y
        surface.blit(self.mouse_image, self.mouse_rect)
            
    def draw(self, surface):
        self.level.blit(self.background, self.viewport, self.viewport)
        surface.blit(self.level, (0,0), self.viewport)
        if self.state == c.CHOOSE:
            self.panel.draw(surface)
        elif self.state == c.PLAY:
            self.menubar.draw(surface)
            for i in range(self.map_y_len):
                self.plant_groups[i].draw(surface)
                self.zombie_groups[i].draw(surface)
                self.bullet_groups[i].draw(surface)
            for car in self.cars:
                car.draw(surface)
            self.head_group.draw(surface)
            self.sun_group.draw(surface)

            if self.drag_plant:
                self.drawMouseShow(surface)