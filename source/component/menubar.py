__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c

PANEL_Y_START = 87
PANEL_X_START = 22
PANEL_Y_INTERNAL = 74
PANEL_X_INTERNAL = 53
CARD_LIST_NUM = 8

card_name_list = [c.CARD_SUNFLOWER, c.CARD_PEASHOOTER, c.CARD_SNOWPEASHOOTER, c.CARD_WALLNUT,
                  c.CARD_CHERRYBOMB, c.CARD_THREEPEASHOOTER, c.CARD_REPEATERPEA, c.CARD_CHOMPER,
                  c.CARD_PUFFMUSHROOM, c.CARD_POTATOMINE, c.CARD_SQUASH]
plant_name_list = [c.SUNFLOWER, c.PEASHOOTER, c.SNOWPEASHOOTER, c.WALLNUT,
                   c.CHERRYBOMB, c.THREEPEASHOOTER, c.REPEATERPEA, c.CHOMPER,
                   c.PUFFMUSHROOM, c.POTATOMINE, c.SQUASH]
plant_sun_list = [50, 100, 175, 50, 150, 325, 200, 150, 0, 25, 50]
plant_frozen_time_list = [0, 5000, 5000, 10000, 5000, 5000, 5000, 5000, 8000, 8000, 8000]
all_card_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

def getSunValueImage(sun_value):
    font = pg.font.SysFont(None, 22)
    width = 32
    msg_image = font.render(str(sun_value), True, c.NAVYBLUE, c.LIGHTYELLOW)
    msg_rect = msg_image.get_rect()
    msg_w = msg_rect.width

    image = pg.Surface([width, 17])
    x = width - msg_w

    image.fill(c.LIGHTYELLOW)
    image.blit(msg_image, (x, 0), (0, 0, msg_rect.w, msg_rect.h))
    image.set_colorkey(c.BLACK)
    return image

class Card():
    def __init__(self, x, y, name_index, scale=0.78):
        self.loadFrame(card_name_list[name_index], scale)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.name_index = name_index
        self.sun_cost = plant_sun_list[name_index]
        self.frozen_time = plant_frozen_time_list[name_index]
        self.frozen_timer = -self.frozen_time
        self.select = True

    def loadFrame(self, name, scale):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        width, height = rect.w, rect.h

        self.image = tool.get_image(frame, 0, 0, width, height, c.BLACK, scale)
    
    def checkMouseClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def canClick(self, sun_value, current_time):
        if self.sun_cost <= sun_value and (current_time - self.frozen_timer) > self.frozen_time:
            return True
        return False

    def canSelect(self):
        return self.select

    def setSelect(self, can_select):
        self.select = can_select
        if can_select:
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(128)

    def setFrozenTime(self, current_time):
        self.frozen_timer = current_time

    def update(self, sun_value, current_time):
        if (self.sun_cost > sun_value or
            (current_time - self.frozen_timer) <= self.frozen_time):
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MenuBar():
    def __init__(self, card_list, sun_value):
        self.loadFrame(c.MENUBAR_BACKGROUND)
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 0
        
        self.sun_value = sun_value
        self.card_offset_x = 32
        self.setupCards(card_list)

    def loadFrame(self, name):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        frame_rect = (rect.x, rect.y, rect.w, rect.h)

        self.image = tool.get_image(tool.GFX[name], *frame_rect, c.WHITE, 1)

    def update(self, current_time):
        self.current_time = current_time
        for card in self.card_list:
            card.update(self.sun_value, self.current_time)

    def createImage(self, x, y, num):
        if num == 1:
            return
        img = self.image
        rect = self.image.get_rect()
        width = rect.w
        height = rect.h
        self.image = pg.Surface((width * num, height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        for i in range(num):
            x = i * width
            self.image.blit(img, (x,0))
        self.image.set_colorkey(c.BLACK)
    
    def setupCards(self, card_list):
        self.card_list = []
        x = self.card_offset_x
        y = 8
        for index in card_list:
            x += 55
            self.card_list.append(Card(x, y, index))

    def checkCardClick(self, mouse_pos):
        result = None
        for card in self.card_list:
            if card.checkMouseClick(mouse_pos):
                if card.canClick(self.sun_value, self.current_time):
                    result = (plant_name_list[card.name_index], card.sun_cost)
                break
        return result
    
    def checkMenuBarClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def decreaseSunValue(self, value):
        self.sun_value -= value

    def increaseSunValue(self, value):
        self.sun_value += value

    def setCardFrozenTime(self, plant_name):
        for card in self.card_list:
            if plant_name_list[card.name_index] == plant_name:
                card.setFrozenTime(self.current_time)
                break

    def drawSunValue(self):
        self.value_image = getSunValueImage(self.sun_value)
        self.value_rect = self.value_image.get_rect()
        self.value_rect.x = 21
        self.value_rect.y = self.rect.bottom - 21
        
        self.image.blit(self.value_image, self.value_rect)

    def draw(self, surface):
        self.drawSunValue()
        surface.blit(self.image, self.rect)
        for card in self.card_list:
            card.draw(surface)

class Panel():
    def __init__(self, card_list, sun_value):
        self.loadImages(sun_value)
        self.selected_cards = []
        self.selected_num = 0
        self.setupCards(card_list)

    def loadFrame(self, name):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        frame_rect = (rect.x, rect.y, rect.w, rect.h)

        return tool.get_image(tool.GFX[name], *frame_rect, c.WHITE, 1)

    def loadImages(self, sun_value):
        self.menu_image = self.loadFrame(c.MENUBAR_BACKGROUND)
        self.menu_rect = self.menu_image.get_rect()
        self.menu_rect.x = 0
        self.menu_rect.y = 0

        self.panel_image = self.loadFrame(c.PANEL_BACKGROUND)
        self.panel_rect = self.panel_image.get_rect()
        self.panel_rect.x = 0
        self.panel_rect.y = PANEL_Y_START

        
        self.value_image = getSunValueImage(sun_value)
        self.value_rect = self.value_image.get_rect()
        self.value_rect.x = 21
        self.value_rect.y = self.menu_rect.bottom - 21

        self.button_image =  self.loadFrame(c.START_BUTTON)
        self.button_rect = self.button_image.get_rect()
        self.button_rect.x = 155
        self.button_rect.y = 547

    def setupCards(self, card_list):
        self.card_list = []
        x = PANEL_X_START - PANEL_X_INTERNAL
        y = PANEL_Y_START + 43 - PANEL_Y_INTERNAL
        for i, index in enumerate(card_list):
            if i % 8 == 0:
                x = PANEL_X_START - PANEL_X_INTERNAL
                y += PANEL_Y_INTERNAL
            x += PANEL_X_INTERNAL
            self.card_list.append(Card(x, y, index, 0.75))

    def checkCardClick(self, mouse_pos):
        delete_card = None
        for card in self.selected_cards:
            if delete_card: # when delete a card, move right cards to left
                card.rect.x -= 55
            elif card.checkMouseClick(mouse_pos):
                self.deleteCard(card.name_index)
                delete_card = card

        if delete_card:
            self.selected_cards.remove(delete_card)
            self.selected_num -= 1

        if self.selected_num == CARD_LIST_NUM:
            return

        for card in self.card_list:
            if card.checkMouseClick(mouse_pos):
                if card.canSelect():
                    self.addCard(card)
                break

    def addCard(self, card):
        card.setSelect(False)
        y = 8
        x = 78 + self.selected_num * 55
        self.selected_cards.append(Card(x, y, card.name_index))
        self.selected_num += 1

    def deleteCard(self, index):
        self.card_list[index].setSelect(True)

    def checkStartButtonClick(self, mouse_pos):
        if self.selected_num < CARD_LIST_NUM:
            return False

        x, y = mouse_pos
        if (x >= self.button_rect.x and x <= self.button_rect.right and
            y >= self.button_rect.y and y <= self.button_rect.bottom):
           return True
        return False

    def getSelectedCards(self):
        card_index_list = []
        for card in self.selected_cards:
            card_index_list.append(card.name_index)
        return card_index_list

    def draw(self, surface):
        self.menu_image.blit(self.value_image, self.value_rect)
        surface.blit(self.menu_image, self.menu_rect)
        surface.blit(self.panel_image, self.panel_rect)
        for card in self.card_list:
            card.draw(surface)
        for card in self.selected_cards:
            card.draw(surface)

        if self.selected_num == CARD_LIST_NUM:
            surface.blit(self.button_image, self.button_rect)