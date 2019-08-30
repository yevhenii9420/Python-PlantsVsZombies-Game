__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c

class Zombie(pg.sprite.Sprite):
    def __init__(self, x, y, name, health, head_group=None, damage=1):
        pg.sprite.Sprite.__init__(self)
        
        self.name = name
        self.frames = []
        self.frame_index = 0
        self.loadImages()
        self.frame_num = len(self.frames)

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        
        self.health = health
        self.damage = damage
        self.dead = False
        self.losHead = False
        self.helmet = False
        self.head_group = head_group

        self.walk_timer = 0
        self.animate_timer = 0
        self.attack_timer = 0
        self.state = c.WALK
        self.animate_interval = 150
        self.ice_slow_ratio = 1
        self.ice_slow_timer = 0
    
    def loadFrames(self, frames, name, image_x):
        frame_list = tool.GFX[name]
        rect = frame_list[0].get_rect()
        width, height = rect.w, rect.h
        width -= image_x

        for frame in frame_list:
            frames.append(tool.get_image(frame, image_x, 0, width, height))

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        self.handleState()
        self.updateIceSlow()
        self.animation()

    def handleState(self):
        if self.state == c.WALK:
            self.walking()
        elif self.state == c.ATTACK:
            self.attacking()
        elif self.state == c.DIE:
            self.dying()

    def walking(self):
        if self.health <= 0:
            self.setDie()
        elif self.health <= c.LOSTHEAD_HEALTH and not self.losHead:
            self.changeFrames(self.losthead_walk_frames)
            self.setLostHead()
        elif self.health <= c.NORMAL_HEALTH and self.helmet:
            self.changeFrames(self.walk_frames)
            self.helmet = False
            
        if (self.current_time - self.walk_timer) > (c.ZOMBIE_WALK_INTERVAL * self.ice_slow_ratio):
            self.walk_timer = self.current_time
            self.rect.x -= 1
    
    def attacking(self):
        if self.health <= 0:
            self.setDie()
        elif self.health <= c.LOSTHEAD_HEALTH and not self.losHead:
            self.changeFrames(self.losthead_attack_frames)
            self.setLostHead()
        if (self.current_time - self.attack_timer) > (c.ATTACK_INTERVAL * self.ice_slow_ratio):
            self.plant.setDamage(self.damage)
            self.attack_timer = self.current_time

            if self.plant.health <= 0:
                self.plant = None
                self.setWalk()
    
    def dying(self):
        pass
    
    def setLostHead(self):
        self.losHead = True
        if self.head_group is not None:
            self.head_group.add(ZombieHead(self.rect.centerx, self.rect.bottom))

    def changeFrames(self, frames):
        '''change image frames and modify rect position'''
        self.frames = frames
        self.frame_num = len(self.frames)
        self.frame_index = 0
        
        bottom = self.rect.bottom
        centerx = self.rect.centerx
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.centerx = centerx

    def animation(self):
        if (self.current_time - self.animate_timer) > (self.animate_interval * self.ice_slow_ratio):
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                if self.state == c.DIE:
                    self.kill()
                    return
                self.frame_index = 0
            self.animate_timer = self.current_time
        
        self.image = self.frames[self.frame_index]
    
    def setIceSlow(self):
        '''when get a ice bullet damage, slow the attack or walk speed of the zombie'''
        self.ice_slow_timer = self.current_time
        self.ice_slow_ratio = 2

    def updateIceSlow(self):
        if self.ice_slow_ratio > 1:
            if (self.current_time - self.ice_slow_timer) > c.ICE_SLOW_TIME:
                self.ice_slow_ratio = 1

    def setDamage(self, damage, ice):
        self.health -= damage
        if ice:
            self.setIceSlow()
    
    def setWalk(self):
        self.state = c.WALK
        self.animate_interval = 150
        
        if self.helmet:
            self.changeFrames(self.helmet_walk_frames)
        elif self.losHead:
            self.changeFrames(self.losthead_walk_frames)
        else:
            self.changeFrames(self.walk_frames)

    def setAttack(self, plant):
        self.plant = plant
        self.state = c.ATTACK
        self.animate_interval = 100
        
        if self.helmet:
            self.changeFrames(self.helmet_attack_frames)
        elif self.losHead:
            self.changeFrames(self.losthead_attack_frames)
        else:
            self.changeFrames(self.attack_frames)
    
    def setDie(self):
        self.state = c.DIE
        self.animate_interval = 200
        self.changeFrames(self.die_frames)
    
    def setBoomDie(self):
        self.state = c.DIE
        self.animate_interval = 200
        self.changeFrames(self.boomdie_frames)

class ZombieHead(Zombie):
    def __init__(self, x, y):
        Zombie.__init__(self, x, y, c.ZOMBIE_HEAD, 0)
        self.state = c.DIE
    
    def loadImages(self):
        self.die_frames = []
        die_name =  self.name
        self.loadFrames(self.die_frames, die_name, 0)
        self.frames = self.die_frames

    def setWalk(self):
        self.animate_interval = 100

class NormalZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.NORMAL_ZOMBIE, c.NORMAL_HEALTH, head_group)

    def loadImages(self):
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name =  self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.walk_frames

class ConeHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.CONEHEAD_ZOMBIE, c.CONEHEAD_HEALTH, head_group)
        self.helmet = True

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []
        
        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.helmet_walk_frames

class BucketHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.BUCKETHEAD_ZOMBIE, c.BUCKETHEAD_HEALTH, head_group)
        self.helmet = True

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.helmet_walk_frames

class FlagZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.FLAG_ZOMBIE, c.FLAG_HEALTH, head_group)
    
    def loadImages(self):
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.walk_frames