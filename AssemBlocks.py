import pygame
import os.path
from os import listdir, makedirs
from json import load as loadjson, dump as savejson
from math import ceil, floor
from copy import copy
from textwrap import wrap
import traceback
from tkinter import Tk as TkinterWindow
from tkinter import messagebox
from sys import exc_info as get_exception_info

screen_width = 640
screen_height = 480

storage_folder = os.path.expanduser(os.path.join("~", "AssemBlocks"))
makedirs(storage_folder, exist_ok=True)
# custom_levels_folder = os.path.join(storage_folder, "levels")
# makedirs(custom_levels_folder, exist_ok=True)
save_folder = os.path.join(storage_folder, "save")
makedirs(save_folder, exist_ok=True)

BG_COLOR = (40, 40, 40)
WHITE_COLOR = (240, 240, 240)
BORDER_SIZE = 19

images = {}
arrow_up_light = None
arrow_up_dark = None
arrow_down_light = None
arrow_down_dark = None
def load_images():
    global images
    global arrow_up_light
    global arrow_up_dark
    global arrow_down_light
    global arrow_down_dark

    images["arrow_up"] = pygame.image.load(os.path.join("images", "arrow_up.png")).convert_alpha()
    images["arrow_down"] = pygame.image.load(os.path.join("images", "arrow_down.png")).convert_alpha()

    images["robot"] = pygame.image.load(os.path.join("images", "robot.png")).convert_alpha()
    squares = [
        "square_empty",
        "square_marked",
        "square_painted",
        "square_square",
        "square_square_hole",
        "square_square_hole_filled",
        "square_triangle",
        "square_triangle_hole",
        "square_triangle_hole_filled",
        "square_circle",
        "square_circle_hole",
        "square_circle_hole_filled",
    ]
    for square_type in squares:
        images[square_type] = pygame.image.load(os.path.join("images", square_type + ".png"))

    light_square = pygame.Surface((20, 20))
    light_square.fill(WHITE_COLOR)

    dark_square = pygame.Surface((20, 20))
    dark_square.fill(BG_COLOR)

    arrow_up_light = pygame.Surface((20, 20), pygame.SRCALPHA)
    arrow_up_light.blit(images["arrow_up"], (4, 4))
    arrow_up_light.blit(light_square, (0, 0), None, pygame.BLEND_RGBA_MULT)

    arrow_up_dark = pygame.Surface((20, 20), pygame.SRCALPHA)
    arrow_up_dark.blit(images["arrow_up"], (4, 4))
    arrow_up_dark.blit(dark_square, (0, 0), None, pygame.BLEND_RGBA_MULT)

    arrow_down_light = pygame.Surface((20, 20), pygame.SRCALPHA)
    arrow_down_light.blit(images["arrow_down"], (4, 4))
    arrow_down_light.blit(light_square, (0, 0), None, pygame.BLEND_RGBA_MULT)

    arrow_down_dark = pygame.Surface((20, 20), pygame.SRCALPHA)
    arrow_down_dark.blit(images["arrow_down"], (4, 4))
    arrow_down_dark.blit(dark_square, (0, 0), None, pygame.BLEND_RGBA_MULT)

allowed_keys = "AZERTYUIOPQSDFGHJKLMWXCVBN0123456789!-<>= "
allowed_keycodes = [
    pygame.K_a,
    pygame.K_b,
    pygame.K_c,
    pygame.K_d,
    pygame.K_e,
    pygame.K_f,
    pygame.K_g,
    pygame.K_h,
    pygame.K_i,
    pygame.K_j,
    pygame.K_k,
    pygame.K_l,
    pygame.K_m,
    pygame.K_n,
    pygame.K_o,
    pygame.K_p,
    pygame.K_q,
    pygame.K_r,
    pygame.K_s,
    pygame.K_t,
    pygame.K_u,
    pygame.K_v,
    pygame.K_w,
    pygame.K_x,
    pygame.K_y,
    pygame.K_z,

    pygame.K_0,
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
    pygame.K_5,
    pygame.K_6,
    pygame.K_7,
    pygame.K_8,
    pygame.K_9,

    pygame.K_ASTERISK,
    pygame.K_PLUS,
    pygame.K_MINUS,
    pygame.K_SLASH,
    pygame.K_EQUALS,

    pygame.K_KP0,
    pygame.K_KP1,
    pygame.K_KP2,
    pygame.K_KP3,
    pygame.K_KP4,
    pygame.K_KP5,
    pygame.K_KP6,
    pygame.K_KP7,
    pygame.K_KP8,
    pygame.K_KP9,

    pygame.K_KP_MULTIPLY,
    pygame.K_KP_PLUS,
    pygame.K_KP_MINUS,
    pygame.K_KP_DIVIDE,
    pygame.K_KP_EQUALS,

    pygame.K_SPACE,
    pygame.K_LESS,
    pygame.K_GREATER,

    pygame.K_SEMICOLON,
]

def rendertext(font, text, dark):
    return font.render(text.upper(), False, BG_COLOR if dark else WHITE_COLOR)

def wrap_mission_info(text):
    lines = text.split("\n")
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(wrap(line, 24))
    return [rendertext(smallfont, "".join(line), False) for line in wrapped_lines]

class Button:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.hovering_timer = 0
        self.surface = pygame.Surface((width-4, height-4))
        self.border_surface = pygame.Surface((width, height))
        self.surface.fill(BG_COLOR)
        self.border_surface.fill(WHITE_COLOR)
        self.border_surface.blit(self.surface, (2, 2))
        self.surface.fill(WHITE_COLOR)

    def draw(self, surface, x, y):
        surface.blit(self.border_surface, (x, y))
        self.surface.set_alpha(self.hovering_timer)
        surface.blit(self.surface, (x+2, y+2))

    def draw_not_hovering(self, surface, x, y):
        if self.hovering_timer != 0:
            self.hovering_timer -= 15
        self.draw(surface, x, y)

    def draw_hovering(self, surface, x, y):
        if self.hovering_timer != 255:
            self.hovering_timer += 15
        self.draw(surface, x, y)

    def draw_selected(self, surface, x, y):
        self.hovering_timer = 255
        self.draw(surface, x, y)

class Tab:
    def __init__(self, number):
        self.hovering_timer = 0
        self.surface = pygame.Surface((BORDER_SIZE-4, BORDER_SIZE-2))
        self.surface.fill(BG_COLOR)
        self.border_surface = pygame.Surface((BORDER_SIZE, BORDER_SIZE))
        self.border_surface.fill(WHITE_COLOR)
        number = hex(number)[2:].zfill(2)
        self.number_light = rendertext(smallfont, number, False)
        self.number_dark = rendertext(smallfont, number, True)

    def draw(self, surface, x, y):
        surface.blit(self.border_surface, (x, y))
        self.surface.set_alpha(self.hovering_timer)
        surface.blit(self.surface, (x+2, y+2))
        surface.blit(self.number_dark if self.hovering_timer == 0 else self.number_light, (x + (BORDER_SIZE - 7*2)//2 + 1, y + 2))

    def draw_not_hovering(self, surface, x, y):
        if self.hovering_timer != 0:
            self.hovering_timer -= 15
        self.draw(surface, x, y)

    def draw_hovering(self, surface, x, y):
        if self.hovering_timer != 255:
            self.hovering_timer += 15
        self.draw(surface, x, y)

    def draw_selected(self, surface, x, y):
        self.hovering_timer = 255
        self.draw(surface, x, y)
  
class MainMenuTitle:
    def __init__(self):
        self.title_light = rendertext(bigfont, self.info["title"], False)
        self.title_dark = rendertext(bigfont, self.info["title"], True)
        self.description_light = rendertext(smallfont, self.info["description"], False)
        self.description_dark = rendertext(smallfont, self.info["description"], True)

class Level(MainMenuTitle):
    def __init__(self, path):
        with open(path, "rt") as f:
            self.level = loadjson(f)
            self.info = self.level["info"]
            MainMenuTitle.__init__(self)

class AddCustomLevel(MainMenuTitle):
    def __init__(self):
        self.info = {
            "title": "Add a custom level",
            "description": "Make sure the level is in your clipboard!"
        }
        MainMenuTitle.__init__(self)

class AssemBlocksConstants:
    STATE_LEVEL_SELECTOR = 0
    STATE_EDITING_CODE = 1
    STATE_PLAYING_LEVEL = 2

    BORDER_ACTUAL_SIZE = BORDER_SIZE*2

    DIFFICULTY_BUTTON_WIDTH = 120
    DIFFICULTY_BUTTON_HEIGHT = 64

    LEVEL_SELECTOR_WIDTH = screen_width - BORDER_ACTUAL_SIZE
    LEVEL_SELECTOR_SCROLL_SIZE = 20
    LEVEL_SELECTOR_LEVELS_Y = BORDER_SIZE + DIFFICULTY_BUTTON_HEIGHT + 10
    LEVEL_SELECTOR_HEIGHT = screen_height - LEVEL_SELECTOR_LEVELS_Y - BORDER_SIZE
    LEVEL_SELECTOR_SCROLLBAR_MAX_HEIGHT = LEVEL_SELECTOR_HEIGHT - 2*2 - LEVEL_SELECTOR_SCROLL_SIZE*2
    LEVEL_SELECTOR_SCROLLBAR_WIDTH = LEVEL_SELECTOR_SCROLL_SIZE - 2*2 - 2*2
    LEVEL_SELECTOR_SCROLL_X = BORDER_SIZE + LEVEL_SELECTOR_WIDTH - LEVEL_SELECTOR_SCROLL_SIZE
    LEVEL_SELECTOR_LEVELS_PER_SCREEN = 6

    LEVEL_SELECTOR_LEVEL_HEIGHT = (screen_height - BORDER_SIZE - LEVEL_SELECTOR_LEVELS_Y - 4 - LEVEL_SELECTOR_LEVELS_PER_SCREEN*2) // LEVEL_SELECTOR_LEVELS_PER_SCREEN
    LEVEL_SELECTOR_LEVEL_WIDTH = LEVEL_SELECTOR_SCROLL_X - 2 - BORDER_SIZE - 4

    GRID_MAX_SIZE = 18
    GRID_PIXEL_SIZE = 16

    GRID_BORDER_WIDTH = GRID_MAX_SIZE*GRID_PIXEL_SIZE + 2*2
    GRID_BORDER_HEIGHT = GRID_MAX_SIZE*GRID_PIXEL_SIZE + BORDER_SIZE + 2

    PLAYER_FUNCTION_HEADER_SIZE = BORDER_SIZE
    PLAYER_CODE_ZONE_WIDTH = (screen_width - GRID_MAX_SIZE*GRID_PIXEL_SIZE - BORDER_ACTUAL_SIZE - 8)//2
    PLAYER_CODE_ZONE_LINE_WIDTH = PLAYER_CODE_ZONE_WIDTH - 2*2 - 2 - BORDER_SIZE
    PLAYER_CODE_ZONE_HEIGHT = screen_height - BORDER_ACTUAL_SIZE

    PLAYER_MISSION_ZONE_WIDTH = PLAYER_CODE_ZONE_WIDTH
    PLAYER_MISSION_ZONE_HEIGHT = PLAYER_CODE_ZONE_HEIGHT

    PLAYER_OUTPUT_ZONE_WIDTH = GRID_BORDER_WIDTH
    PLAYER_OUTPUT_ZONE_HEIGHT = BORDER_SIZE + 2 + 16*4

class Difficulty(AssemBlocksConstants):
    def __init__(self, name):
        self.name = name

        self.name_light = rendertext(bigfont, name, False)
        self.name_dark = rendertext(bigfont, name, True)
        self.button = Button(self.DIFFICULTY_BUTTON_WIDTH, self.DIFFICULTY_BUTTON_HEIGHT)

        self.scroll = 0
        self.scroll_step = 0
        self.scroll_bar = None

        self.load_levels()

        levels_amount = len(self.levels)
        self.level_buttons = [Button(self.LEVEL_SELECTOR_LEVEL_WIDTH, self.LEVEL_SELECTOR_LEVEL_HEIGHT) for i in range(levels_amount)]
        if len(self.levels) > self.LEVEL_SELECTOR_LEVELS_PER_SCREEN:
            scroll_bar_height = max(int(self.LEVEL_SELECTOR_SCROLLBAR_MAX_HEIGHT * (self.LEVEL_SELECTOR_LEVELS_PER_SCREEN / levels_amount)), 20)
            self.scroll_bar = pygame.Surface((self.LEVEL_SELECTOR_SCROLLBAR_WIDTH, scroll_bar_height))
            self.scroll_bar.fill(WHITE_COLOR)
            self.scroll_step = self.LEVEL_SELECTOR_SCROLLBAR_MAX_HEIGHT / levels_amount

    def load_levels(self):
        levels_path = os.path.join("levels", self.name)
        self.levels = [Level(os.path.join(levels_path, level)) for level in listdir(levels_path)]

class CustomDifficulty(Difficulty):
    def __init__(self):
        Difficulty.__init__(self, "Custom")

    def load_levels(self):
        self.levels = []
        # self.levels = [Level(os.path.join(custom_levels_folder, level)) for level in listdir(custom_levels_folder)]
        self.levels.append(AddCustomLevel())

class Grid(AssemBlocksConstants):
    def __init__(self, width, height, coords):
        self.width = width
        self.height = height
        self.coords = coords
        if coords:
            width += 1
            height += 1
        assert(width <= self.GRID_MAX_SIZE and height <= self.GRID_MAX_SIZE)
        self.surface = pygame.Surface((width*self.GRID_PIXEL_SIZE, height*self.GRID_PIXEL_SIZE))
        self.surface.fill(BG_COLOR)
        self.x = BORDER_SIZE + self.PLAYER_CODE_ZONE_WIDTH + 2 + 2 + ((self.GRID_MAX_SIZE*self.GRID_PIXEL_SIZE) - width*self.GRID_PIXEL_SIZE)//2
        self.y = screen_height - BORDER_SIZE - 2 - (self.GRID_MAX_SIZE*self.GRID_PIXEL_SIZE) + ((self.GRID_MAX_SIZE*self.GRID_PIXEL_SIZE) - (height*self.GRID_PIXEL_SIZE))//2
        if coords:
            for i in range(max(self.width, self.height)):
                surf = rendertext(coordsfont, str(i+1), False)
                w, h = surf.get_size()
                if i < self.width:
                    self.surface.blit(surf, (self.GRID_PIXEL_SIZE*(i+1) + (self.GRID_PIXEL_SIZE - w)//2, (self.GRID_PIXEL_SIZE - h + 2)//2)) 
                if i < self.height:
                    self.surface.blit(surf, ((self.GRID_PIXEL_SIZE - w)//2, self.GRID_PIXEL_SIZE*(i+1) + (self.GRID_PIXEL_SIZE - h)//2)) 

    def draw(self, surface):
        x = self.x
        y = self.y
        surface.blit(self.surface, (x, y))
        if self.coords:
            x += self.GRID_PIXEL_SIZE
            y += self.GRID_PIXEL_SIZE
        return x, y

class Test(AssemBlocksConstants):
    def __init__(self, test, coords):
        self.grid = Grid(test["width"], test["height"], coords)
        self.robot_original_column = test["robot_column"]
        self.robot_original_row = test["robot_row"]
        self.start = test["grid_start"]
        self.wanted = test["grid_wanted"]
        self.reset()

    def reset(self):
        self.current = [copy(line) for line in self.start]
        self.robot_row = self.robot_original_row
        self.robot_column = self.robot_original_column
        self.held = None

    def draw(self, surface):
        startx, starty = self.grid.draw(surface)
        y = starty
        for line in self.current:
            x = startx
            for square in line:
                if type(square) is int:
                    surface.blit(images["square_empty"], (x, y))
                    number = rendertext(smallfont, str(square), True)
                    w, h = number.get_size()
                    surface.blit(number, (x +(self.GRID_PIXEL_SIZE - w)//2, y + 2 + (self.GRID_PIXEL_SIZE - h)//2))
                else:
                    surface.blit(images[square], (x, y))
                x += self.GRID_PIXEL_SIZE
            y += self.GRID_PIXEL_SIZE
        surface.blit(images["robot"], (startx + self.robot_column*self.GRID_PIXEL_SIZE, starty + self.robot_row*self.GRID_PIXEL_SIZE))

    def check_done(self):
        return self.current == self.wanted

    def check_paint(self):
        return self.current[self.robot_row][self.robot_column] == "square_painted"

    def paint(self):
        if self.current[self.robot_row][self.robot_column] == "square_marked":
            self.current[self.robot_row][self.robot_column] = "square_painted"
        else:
            raise Exception("Attempt to paint an unmarked square")

    def grab(self):
        if self.held is not None:
            raise Exception("Attempt to grab a shape while already holding one")

        current_square = self.current[self.robot_row][self.robot_column]
        if current_square == "square_circle":
            self.held = "circle"
        elif current_square == "square_square":
            self.held = "square"
        elif current_square == "square_triangle":
            self.held = "triangle"
        else:
            raise Exception("Attempt to grab on a square without a shape")

    def drop(self):
        if self.held is None:
            raise Exception("Attempt to drop a shape while holding nothing")
        current_square = self.current[self.robot_row][self.robot_column]
        if current_square == "square_circle_hole" and self.held == "circle":
            self.current[self.robot_row][self.robot_column] = "square_circle_hole_filled"
        elif current_square == "square_square_hole" and self.held == "square":
            self.current[self.robot_row][self.robot_column] = "square_square_hole_filled"
        elif current_square == "square_triangle_hole" and self.held == "triangle":
            self.current[self.robot_row][self.robot_column] = "square_triangle_hole_filled"
        elif current_square == "square_empty":
            self.current[self.robot_row][self.robot_column] = "square_" + self.held
        else:
            raise Exception("Attempt to drop on a square that is not empty or a matching hole")
        self.held = None

    def read(self):
        current_square = self.current[self.robot_row][self.robot_column]
        if type(current_square) is int:
            return current_square
        else:
            raise Exception("Attempt to read a number from a normal square")

    def write(self, num):
        current_square = self.current[self.robot_row][self.robot_column]
        if type(current_square) is int:
            self.current[self.robot_row][self.robot_column] = num
        else:
            raise Exception("Attempt to write a number to a normal square")

    def move_up(self):
        if self.robot_row == 0:
            raise Exception("Going out of bounds")
        else:
            self.robot_row -= 1

    def move_right(self):
        if self.robot_column == self.grid.width - 1:
            raise Exception("Going out of bounds")
        else:
            self.robot_column += 1

    def move_down(self):
        if self.robot_row == self.grid.height - 1:
            raise Exception("Going out of bounds")
        else:
            self.robot_row += 1

    def move_left(self):
        if self.robot_column == 0:
            raise Exception("Going out of bounds")
        else:
            self.robot_column -= 1

    def get_column(self):
        return self.robot_column + 1

    def get_row(self):
        return self.robot_row + 1

class AssemBlocks(AssemBlocksConstants):
    def set_screen_from_config(self):
        global config
        display_flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        if config.get("fullscreen", False):
            display_flags |= pygame.FULLSCREEN
        elif config.get("borderless", False):
            display_flags |= pygame.NOFRAME
        self.screen_size = (config.get("screen_width", screen_width), config.get("screen_height", screen_height))
        self.screen_surface = pygame.display.set_mode(self.screen_size, display_flags)
        self.mouse_x_ratio = self.screen_size[0]/screen_width
        self.mouse_y_ratio = self.screen_size[1]/screen_height

    def __init__(self):
        self.set_screen_from_config()
        load_images()
        self.scaled_icon = pygame.transform.scale(images["robot"], (32, 32))
        pygame.display.set_caption("AssemBlocks")
        pygame.display.set_icon(self.scaled_icon)

        self.state = self.STATE_LEVEL_SELECTOR
        self.difficulties = (
            Difficulty("Easy"),
            Difficulty("Medium"),
            Difficulty("Hard"),
            CustomDifficulty()
        )

        self.selected_difficulty_index = 0
        self.selected_difficulty = self.difficulties[self.selected_difficulty_index]

        self.hovering_above = None
        self.difficulty_buttons_start_x = (screen_width - (len(self.difficulties) * (self.DIFFICULTY_BUTTON_WIDTH + BORDER_SIZE)) + BORDER_SIZE)//2

        self.level_selector_scroll_up = Button(20, 20)
        self.level_selector_scroll_down = Button(20, 20)
        self.level_selector_border = pygame.Surface((self.LEVEL_SELECTOR_WIDTH, self.LEVEL_SELECTOR_HEIGHT))
        self.level_selector_border.fill(WHITE_COLOR)
        self.level_selector_border.fill(BG_COLOR, (2, 2, self.LEVEL_SELECTOR_WIDTH - 2 - self.LEVEL_SELECTOR_SCROLL_SIZE, self.LEVEL_SELECTOR_HEIGHT - 2*2))
        self.level_selector_border.fill(BG_COLOR, (self.LEVEL_SELECTOR_WIDTH - self.LEVEL_SELECTOR_SCROLL_SIZE + 2, 2, self.LEVEL_SELECTOR_SCROLL_SIZE - 4,  self.LEVEL_SELECTOR_HEIGHT - 2*2))

        self.player_grid_border = pygame.Surface((self.GRID_BORDER_WIDTH, self.GRID_BORDER_HEIGHT))
        self.player_grid_border.fill(WHITE_COLOR)
        self.player_grid_border.fill(BG_COLOR, (2, BORDER_SIZE, self.GRID_BORDER_WIDTH - 4, self.GRID_BORDER_HEIGHT - BORDER_SIZE - 2))
        self.player_grid_border.fill(BG_COLOR, (2 + BORDER_SIZE*2, 2, self.GRID_BORDER_WIDTH - 2 - BORDER_SIZE*2 - 2, BORDER_SIZE - 4))
        self.player_grid_border.blit(rendertext(smallfont, "GRID", True), (2, 2))

        self.player_code_zone = pygame.Surface((self.PLAYER_CODE_ZONE_WIDTH, self.PLAYER_CODE_ZONE_HEIGHT))
        self.player_code_zone.fill(WHITE_COLOR)
        self.player_code_zone.fill(BG_COLOR, (2, BORDER_SIZE, BORDER_SIZE, self.PLAYER_CODE_ZONE_HEIGHT - BORDER_SIZE - 2))
        self.player_code_zone.fill(BG_COLOR, (2 + BORDER_SIZE + 2, 2, self.PLAYER_CODE_ZONE_LINE_WIDTH, self.PLAYER_CODE_ZONE_HEIGHT - 2*2))
        self.player_code_zone.fill(WHITE_COLOR, (2 + BORDER_SIZE + 2, BORDER_SIZE - 2, self.PLAYER_CODE_ZONE_LINE_WIDTH, 2))
        self.player_code_zone.blit(rendertext(smallfont, "PC", True), ((BORDER_SIZE - 7*2)//2, 2))
        self.program_line = [rendertext(smallfont, hex(i)[2:].zfill(2), False) for i in range(256)]

        self.player_mission_zone = pygame.Surface((self.PLAYER_MISSION_ZONE_WIDTH, self.PLAYER_MISSION_ZONE_HEIGHT))
        self.player_mission_zone.fill(WHITE_COLOR)
        self.player_mission_zone.fill(BG_COLOR, (2, BORDER_SIZE, self.PLAYER_MISSION_ZONE_WIDTH - 2*2, self.PLAYER_CODE_ZONE_HEIGHT - BORDER_SIZE - 2))
        self.player_mission_zone.blit(rendertext(smallfont, "MISSION", True), (2, 2))

        self.player_output_zone = pygame.Surface((self.PLAYER_OUTPUT_ZONE_WIDTH, self.PLAYER_OUTPUT_ZONE_HEIGHT))
        self.player_output_zone.fill(WHITE_COLOR)
        self.player_output_zone.fill(BG_COLOR, (2, BORDER_SIZE, self.PLAYER_OUTPUT_ZONE_WIDTH - 2*2, self.PLAYER_OUTPUT_ZONE_HEIGHT - 2 - BORDER_SIZE))
        self.player_output_zone.blit(rendertext(smallfont, "OUTPUT", True), (2, 2))

        self.characters_light = {}
        self.characters_dark = {}
        for character in allowed_keys:
            self.characters_light[character] = rendertext(smallfont, character, False)
            self.characters_dark[character] = rendertext(smallfont, character, True)

        self.verifying = False
        self.running_line = None
        self.error_line = -1
        self.command_function = {
            "CHECKPAINT": self.check_paint,
            "PAINT": self.paint,

            "READ": self.read,
            "WRITE": self.write,

            "GRAB": self.grab,
            "DROP": self.drop,

            "UP": self.move_up,
            "RIGHT": self.move_right,
            "DOWN": self.move_down,
            "LEFT": self.move_left,

            "SET": self.set_reg,
            "ADD": self.do_add,
            "SUB": self.do_sub,
            "MUL": self.do_mul,
            "DIV": self.do_div,
            "MOD": self.do_mod,
            "DIVMOD": self.do_divmod,

            "CALL": self.do_function_call,
            "RETURN": self.do_return,

            "ROW": self.get_row,
            "COLUMN": self.get_column,

            "PUSH": self.do_push,
            "POP": self.do_pop,

            "STORE": self.do_store,
            "LOAD": self.do_load,

            "TEST": self.do_test,
            "JMP": self.do_jump,
            "JMPF": self.do_jump_false,
            "JMPT": self.do_jump_true,
            "JRO": self.do_relative_jump,
        }

        self.set_error_message(None)

        self.clock = pygame.time.Clock()

    def mainloop(self):
        while True:
            if self.events() is not None:
                break

            self.advance()

            display_surface.fill(BG_COLOR)
            self.draw()
            pygame.transform.scale(display_surface, self.screen_size, self.screen_surface)
            pygame.display.flip()

            self.clock.tick(60)

    def events(self):
        pos = pygame.mouse.get_pos()
        pos = (int(pos[0]/self.mouse_x_ratio), int(pos[1]/self.mouse_y_ratio))
        self.check_hover(pos)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return True
            elif not self.verifying:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.state == self.STATE_LEVEL_SELECTOR:
                            return True
                        elif self.state == self.STATE_EDITING_CODE:
                            self.state = self.STATE_LEVEL_SELECTOR
                        elif self.state == self.STATE_PLAYING_LEVEL:
                            self.stop_playing()
                    elif self.state == self.STATE_EDITING_CODE:
                        if len(self.subprograms[self.selected_subprogram][self.cursor_y]) < 17 and e.key in allowed_keycodes and e.unicode.upper() in allowed_keys:
                            if self.error_line != -1:
                                self.error_line = -1
                            line = list(self.subprograms[self.selected_subprogram][self.cursor_y])
                            # line.insert(self.cursor_x, allowed_keys_for_code[e.key])
                            line.insert(self.cursor_x, e.unicode.upper())
                            self.subprograms[self.selected_subprogram][self.cursor_y] = "".join(line)
                            self.cursor_x += 1
                        elif e.key == pygame.K_F5:
                            self.start_playing()
                        elif e.key == pygame.K_BACKSPACE:
                            if self.cursor_x != 0:
                                self.subprograms[self.selected_subprogram][self.cursor_y] = self.subprograms[self.selected_subprogram][self.cursor_y][:self.cursor_x-1] + self.subprograms[self.selected_subprogram][self.cursor_y][self.cursor_x:]
                                self.cursor_x -= 1
                        elif e.key == pygame.K_DELETE:
                            if self.cursor_x != len(self.subprograms[self.selected_subprogram][self.cursor_y]):
                                self.subprograms[self.selected_subprogram][self.cursor_y] = self.subprograms[self.selected_subprogram][self.cursor_y][:self.cursor_x] + self.subprograms[self.selected_subprogram][self.cursor_y][self.cursor_x+1:]
                        elif e.key == pygame.K_RETURN or e.key == pygame.K_KP_ENTER:
                            if self.cursor_y != 255:
                                self.cursor_y += 1
                            self.cursor_x = 0
                        elif e.key == pygame.K_UP:
                            if self.cursor_y != 0:
                                self.cursor_y -= 1
                            new_row_length = len(self.subprograms[self.selected_subprogram][self.cursor_y])
                            if self.cursor_x > new_row_length:
                                self.cursor_x = new_row_length
                            if self.cursor_y < self.program_scroll:
                                self.program_scroll -= 1
                        elif e.key == pygame.K_DOWN:
                            if self.cursor_y != 255:
                                self.cursor_y += 1
                            new_row_length = len(self.subprograms[self.selected_subprogram][self.cursor_y])
                            if self.cursor_x > new_row_length:
                                self.cursor_x = new_row_length
                            if self.program_scroll < 256 - 0x1A and self.cursor_y > (self.program_scroll + 0x1A):
                                self.program_scroll += 1
                        elif e.key == pygame.K_LEFT:
                            if self.cursor_x != 0:
                                self.cursor_x -= 1
                        elif e.key == pygame.K_RIGHT:
                            if self.cursor_x < 17 - 1 and self.cursor_x != len(self.subprograms[self.selected_subprogram][self.cursor_y]):
                                self.cursor_x += 1
                    elif self.state == self.STATE_PLAYING_LEVEL:
                        if e.key == pygame.K_F6:
                            self.stop_playing()
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        self.handle_click(pos)

    def check_hover(self, pos):
        mouse_x, mouse_y = pos
        self.hovering_above = None
        if self.state == self.STATE_LEVEL_SELECTOR:
            if BORDER_SIZE <= mouse_y <= (BORDER_SIZE + self.DIFFICULTY_BUTTON_HEIGHT):
                x = self.difficulty_buttons_start_x
                for difficulty in self.difficulties:
                    if (x <= mouse_x <= (x + self.DIFFICULTY_BUTTON_WIDTH)):
                        self.hovering_above = difficulty.name
                        return
                    x += self.DIFFICULTY_BUTTON_WIDTH + BORDER_SIZE
            elif self.LEVEL_SELECTOR_SCROLL_X <= mouse_x <= (self.LEVEL_SELECTOR_SCROLL_X + self.LEVEL_SELECTOR_SCROLL_SIZE):
                y = self.LEVEL_SELECTOR_LEVELS_Y
                if y <= mouse_y <= (y + self.LEVEL_SELECTOR_SCROLL_SIZE):
                    self.hovering_above = "scroll_up"

                y = screen_height - BORDER_SIZE - self.LEVEL_SELECTOR_SCROLL_SIZE
                if y <= mouse_y <= (y + self.LEVEL_SELECTOR_SCROLL_SIZE):
                    self.hovering_above = "scroll_down"
            else:
                x = BORDER_SIZE + 4
                y = self.LEVEL_SELECTOR_LEVELS_Y + 4
                if x <= mouse_x <= (x + self.LEVEL_SELECTOR_LEVEL_WIDTH) and y <= mouse_y <= (y + self.LEVEL_SELECTOR_LEVEL_HEIGHT * self.LEVEL_SELECTOR_LEVELS_PER_SCREEN + 2 * (self.LEVEL_SELECTOR_LEVELS_PER_SCREEN - 1)):
                    for i in range(self.LEVEL_SELECTOR_LEVELS_PER_SCREEN):
                        if i >= len(self.selected_difficulty.levels):
                            break
                        if y <= mouse_y <= (y + self.LEVEL_SELECTOR_LEVEL_HEIGHT):
                            self.hovering_above = f"{self.selected_difficulty.name}_level_{self.selected_difficulty.scroll + i}"
                            return
                        y += self.LEVEL_SELECTOR_LEVEL_HEIGHT + 2
        elif self.state == self.STATE_EDITING_CODE or self.state == self.STATE_PLAYING_LEVEL:
            if self.state == self.STATE_EDITING_CODE:
                grid_y = screen_height - BORDER_SIZE - self.GRID_BORDER_HEIGHT
                test_tabs_x = BORDER_SIZE + self.PLAYER_CODE_ZONE_WIDTH + 2 + BORDER_SIZE*2
                subprogram_tabs_x = BORDER_SIZE*2 + 2
                if BORDER_SIZE <= mouse_y <= (BORDER_SIZE*2) and subprogram_tabs_x <= mouse_x <= (subprogram_tabs_x + self.PLAYER_CODE_ZONE_WIDTH - BORDER_SIZE):
                    x = subprogram_tabs_x
                    for i in range(len(self.subprogram_tabs)):
                        if (x + 2) <= mouse_x <= (x + BORDER_SIZE - 2):
                            self.hovering_above = f"subprogram_tab_{i}"
                            return
                        x += BORDER_SIZE - 2
                elif grid_y <= mouse_y <= (grid_y + BORDER_SIZE) and test_tabs_x <= mouse_x <= (test_tabs_x + self.GRID_MAX_SIZE*self.GRID_PIXEL_SIZE - BORDER_SIZE*2):
                    x = test_tabs_x
                    for i in range(len(self.test_tabs)):
                        if (x + 2) <= mouse_x <= (x + BORDER_SIZE - 2):
                            self.hovering_above = f"test_tab_{i}"
                            return
                        x += BORDER_SIZE - 2

    def handle_click(self, pos):
        mouse_x, mouse_y = pos
        if self.state == self.STATE_LEVEL_SELECTOR:
            if BORDER_SIZE <= mouse_y <= (BORDER_SIZE + self.DIFFICULTY_BUTTON_HEIGHT):
                x = BORDER_SIZE
                for i, difficulty in enumerate(self.difficulties):
                    if (x <= mouse_x <= (x + self.DIFFICULTY_BUTTON_WIDTH)):
                        self.selected_difficulty_index = i
                        self.selected_difficulty = self.difficulties[self.selected_difficulty_index]
                        return
                    x += self.DIFFICULTY_BUTTON_WIDTH + BORDER_SIZE
            elif self.LEVEL_SELECTOR_SCROLL_X <= mouse_x <= (self.LEVEL_SELECTOR_SCROLL_X + self.LEVEL_SELECTOR_SCROLL_SIZE):
                y = BORDER_SIZE + self.DIFFICULTY_BUTTON_HEIGHT + BORDER_SIZE
                if y <= mouse_y <= (y + self.LEVEL_SELECTOR_SCROLL_SIZE):
                    if self.selected_difficulty.scroll_bar is not None and self.selected_difficulty.scroll != 0:
                        self.selected_difficulty.scroll -= 1
                    return

                y = screen_height - BORDER_SIZE - self.LEVEL_SELECTOR_SCROLL_SIZE
                if y <= mouse_y <= (y + self.LEVEL_SELECTOR_SCROLL_SIZE):
                    if self.selected_difficulty.scroll_bar is not None and self.selected_difficulty.scroll != (len(self.selected_difficulty.levels) - self.LEVEL_SELECTOR_LEVELS_PER_SCREEN):
                        self.selected_difficulty.scroll += 1
                    return
            else:
                x = BORDER_SIZE + 4
                y = self.LEVEL_SELECTOR_LEVELS_Y + 4
                if x <= mouse_x <= (x + self.LEVEL_SELECTOR_LEVEL_WIDTH) and y <= mouse_y <= (y + self.LEVEL_SELECTOR_LEVEL_HEIGHT * self.LEVEL_SELECTOR_LEVELS_PER_SCREEN + 2 * (self.LEVEL_SELECTOR_LEVELS_PER_SCREEN - 1)):
                    for i in range(self.LEVEL_SELECTOR_LEVELS_PER_SCREEN):
                        if i >= len(self.selected_difficulty.levels):
                            break
                        if y <= mouse_y <= (y + self.LEVEL_SELECTOR_LEVEL_HEIGHT):
                            level_index = self.selected_difficulty.scroll + i
                            if self.selected_difficulty_index == 3:
                                if level_index == len(self.selected_difficulty.levels) - 1:
                                    self.state = self.STATE_ADDING_CUSTOM
                                    return
                            self.start_level(self.selected_difficulty.levels[level_index])
                            return
                        y += self.LEVEL_SELECTOR_LEVEL_HEIGHT + 2
        elif self.state == self.STATE_EDITING_CODE or self.state == self.STATE_PLAYING_LEVEL:
            if self.state == self.STATE_EDITING_CODE:
                grid_y = screen_height - BORDER_SIZE - self.GRID_BORDER_HEIGHT
                test_tabs_x = BORDER_SIZE + self.PLAYER_CODE_ZONE_WIDTH + 2 + BORDER_SIZE*2
                subprogram_tabs_x = BORDER_SIZE*2 + 2
                if BORDER_SIZE <= mouse_y <= (BORDER_SIZE*2) and subprogram_tabs_x <= mouse_x <= (subprogram_tabs_x + self.PLAYER_CODE_ZONE_WIDTH - BORDER_SIZE):
                    x = subprogram_tabs_x
                    for i in range(len(self.subprogram_tabs)):
                        if (x + 2) <= mouse_x <= (x + BORDER_SIZE - 2):
                            self.open_subprogram_page(i)
                            return
                        x += BORDER_SIZE - 2
                elif grid_y <= mouse_y <= (grid_y + BORDER_SIZE) and test_tabs_x <= mouse_x <= (test_tabs_x + self.GRID_MAX_SIZE*self.GRID_PIXEL_SIZE - BORDER_SIZE*2):
                    x = test_tabs_x
                    for i in range(len(self.test_tabs)):
                        if (x + 2) <= mouse_x <= (x + BORDER_SIZE - 2):
                            self.selected_test = i
                            return
                        x += BORDER_SIZE - 2

    def start_playing(self):
        self.state = self.STATE_PLAYING_LEVEL
        self.pc = 0
        self.page = 0
        self.program_scroll = 0
        self.registers = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,

            "T": 0,
        }
        self.call_stack = []
        self.memory = [0]*self.memory_size
        self.stack = []
        self.tests[self.selected_test].reset()

    def stop_playing(self):
        self.state = self.STATE_EDITING_CODE
        self.stack = None
        self.memory = None
        self.call_stack = None
        self.registers = None

    def start_level(self, level):
        self.set_error_message(None)

        self.level = level
        self.mission_info = wrap_mission_info(level.level["mission"].upper())
        self.state = self.STATE_EDITING_CODE
        self.open_subprogram_page(0)
        self.selected_test = 0

        grid_coords = level.level["grid_coords"]
        self.tests = [Test(test, grid_coords) for test in level.level["tests"]]
        self.subprograms = [[""]*256]
        for i in range(level.level["limitations"]["subprograms"]):
            self.subprograms.append([""]*256)
        assert(len(self.subprograms) <= 7)

        self.stack_size = level.level["limitations"]["stack_size"]
        self.memory_size = level.level["limitations"]["memory_size"]

        self.disabled_commands = copy(level.level["limitations"]["disabled"])
        if len(self.subprograms) == 1:
            self.add_disabled_command("CALL")
            self.add_disabled_command("RETURN")
        if self.stack_size == 0:
            self.add_disabled_command("POP")
            self.add_disabled_command("PUSH")
        if self.memory_size == 0:
            self.add_disabled_command("STORE")
            self.add_disabled_command("LOAD")
        if not grid_coords:
            self.add_disabled_command("ROW")
            self.add_disabled_command("COLUMN")

        self.subprogram_tabs = [Tab(i) for i in range(len(self.subprograms))]
        self.test_tabs = [Tab(i) for i in range(len(self.tests))]

    def open_subprogram_page(self, page_index):
        self.cursor_x = 0
        self.cursor_y = 0
        self.selected_subprogram = page_index
        self.program_scroll = 0

    def add_disabled_command(self, command):
        if not command in self.disabled_commands:
            self.disabled_commands.append(command)

    def draw(self):
        if self.state == self.STATE_LEVEL_SELECTOR:
            self.draw_level_selector()
        elif self.state == self.STATE_EDITING_CODE or self.state == self.STATE_PLAYING_LEVEL:
            self.draw_level_player()

    def draw_level_selector(self):
        y = BORDER_SIZE
        x = self.difficulty_buttons_start_x

        for i, difficulty in enumerate(self.difficulties):
            button = difficulty.button

            if i == self.selected_difficulty_index:
                button.draw_selected(display_surface, x, y)
            else:
                if self.hovering_above is not None and self.hovering_above == difficulty.name:
                    button.draw_hovering(display_surface, x, y)
                else:
                    button.draw_not_hovering(display_surface, x, y)

            text = difficulty.name_dark if button.hovering_timer != 0 else difficulty.name_light
            text_size = text.get_size()
            display_surface.blit(text, (x + (button.width - text_size[0])//2, y + (button.height - text_size[1])//2)) 
            x += button.width
            x += BORDER_SIZE

        x = BORDER_SIZE
        y = self.LEVEL_SELECTOR_LEVELS_Y
        display_surface.blit(self.level_selector_border, (x, y))

        if self.selected_difficulty.scroll_bar is not None:
            scroll_bar_y = y + self.LEVEL_SELECTOR_SCROLL_SIZE + 2 + (self.selected_difficulty.scroll * self.selected_difficulty.scroll_step)
            display_surface.blit(self.selected_difficulty.scroll_bar, (self.LEVEL_SELECTOR_SCROLL_X + 4, scroll_bar_y))

        if self.hovering_above is not None and self.hovering_above == "scroll_up":
            self.level_selector_scroll_up.draw_hovering(display_surface, self.LEVEL_SELECTOR_SCROLL_X, y)
        else:
            self.level_selector_scroll_up.draw_not_hovering(display_surface, self.LEVEL_SELECTOR_SCROLL_X, y)
        arrow_up_to_draw = arrow_up_dark if self.level_selector_scroll_up.hovering_timer != 0 else arrow_up_light
        display_surface.blit(arrow_up_to_draw, (self.LEVEL_SELECTOR_SCROLL_X, y))

        for i in range(self.LEVEL_SELECTOR_LEVELS_PER_SCREEN):
            if i >= len(self.selected_difficulty.levels):
                break
            level = self.selected_difficulty.levels[self.selected_difficulty.scroll + i]
            level_button = self.selected_difficulty.level_buttons[self.selected_difficulty.scroll + i]
            if self.hovering_above is not None and self.hovering_above == f"{self.selected_difficulty.name}_level_{self.selected_difficulty.scroll + i}":
                level_button.draw_hovering(display_surface, x + 4, y + 4)
            else:
                level_button.draw_not_hovering(display_surface, x + 4, y + 4)

            if level_button.hovering_timer != 0:
                title_to_draw = level.title_dark
                description_to_draw = level.description_dark
            else:
                title_to_draw = level.title_light
                description_to_draw = level.description_light
            display_surface.blit(title_to_draw, (x + 8, y + 4))
            display_surface.blit(description_to_draw, (x + 12, y + self.LEVEL_SELECTOR_LEVEL_HEIGHT - description_to_draw.get_height()))

            y += self.LEVEL_SELECTOR_LEVEL_HEIGHT + 2


        if self.hovering_above is not None and self.hovering_above == "scroll_down":
            self.level_selector_scroll_down.draw_hovering(display_surface, self.LEVEL_SELECTOR_SCROLL_X, screen_height - BORDER_SIZE - self.LEVEL_SELECTOR_SCROLL_SIZE)
        else:
            self.level_selector_scroll_down.draw_not_hovering(display_surface, self.LEVEL_SELECTOR_SCROLL_X, screen_height - BORDER_SIZE - self.LEVEL_SELECTOR_SCROLL_SIZE)
        arrow_down_to_draw = arrow_down_dark if self.level_selector_scroll_down.hovering_timer != 0 else arrow_down_light
        display_surface.blit(arrow_down_to_draw, (self.LEVEL_SELECTOR_SCROLL_X, screen_height - BORDER_SIZE - self.LEVEL_SELECTOR_SCROLL_SIZE))

    def draw_level_player(self):
        x = BORDER_SIZE
        y = BORDER_SIZE
        display_surface.blit(self.player_code_zone, (x, y))

        x += BORDER_SIZE + 2
        for i, subprogram_tab in enumerate(self.subprogram_tabs):
            if i == self.selected_subprogram:
                subprogram_tab.draw_selected(display_surface, x, y)
            elif self.hovering_above is not None and self.hovering_above == f"subprogram_tab_{i}":
                subprogram_tab.draw_hovering(display_surface, x, y)
            else:
                subprogram_tab.draw_not_hovering(display_surface, x, y)
            x += BORDER_SIZE - 2

        if self.state == self.STATE_EDITING_CODE:
            pygame.draw.rect(display_surface, WHITE_COLOR, (BORDER_SIZE + 4 + 2 + BORDER_SIZE + self.cursor_x*7, 6 + BORDER_SIZE*2 + (self.cursor_y - self.program_scroll)*15, 7, 15))
        elif self.state == self.STATE_PLAYING_LEVEL:
            pygame.draw.rect(display_surface, WHITE_COLOR, (BORDER_SIZE + 4 + 2 + BORDER_SIZE, 6 + BORDER_SIZE*2 + (self.running_line - self.program_scroll)*15, 7*17, 15))

        for i in range(0x1A + 1):
            actual_i = self.program_scroll + i
            display_surface.blit(self.program_line[actual_i], (BORDER_SIZE + 5, 6 + BORDER_SIZE*2 + i*15))
            if actual_i < len(self.subprograms[self.selected_subprogram]):
                for j, character in enumerate(self.subprograms[self.selected_subprogram][actual_i]):
                    character_surface = self.characters_light[character]
                    if (self.state == self.STATE_PLAYING_LEVEL and self.running_line == actual_i) or (self.state == self.STATE_EDITING_CODE and i == self.cursor_y and j == self.cursor_x):
                        character_surface = self.characters_dark[character]
                    display_surface.blit(character_surface, (BORDER_SIZE + 4 + 2 + BORDER_SIZE + j*7, 6 + BORDER_SIZE*2 + i*15))

        x = screen_width - BORDER_SIZE - self.PLAYER_MISSION_ZONE_WIDTH
        display_surface.blit(self.player_mission_zone, (x, y))
        x += 4
        y += BORDER_SIZE + 4
        for line in self.mission_info:
            display_surface.blit(line, (x, y))
            y += 15

        x = BORDER_SIZE + self.PLAYER_CODE_ZONE_WIDTH + 2
        y = screen_height - BORDER_SIZE - self.GRID_BORDER_HEIGHT - 2 - self.PLAYER_OUTPUT_ZONE_HEIGHT
        display_surface.blit(self.player_output_zone, (x, y))
        x += 4
        y += BORDER_SIZE + 2
        for line in self.error_messages:
            display_surface.blit(line, (x, y))
            y += 15

        y = screen_height - BORDER_SIZE - self.GRID_BORDER_HEIGHT
        display_surface.blit(self.player_grid_border, (x - 4, y))
        x += BORDER_SIZE*2 - 4
        for i, test_tab in enumerate(self.test_tabs):
            if i == self.selected_test:
                test_tab.draw_selected(display_surface, x, y)
            elif self.hovering_above is not None and self.hovering_above == f"test_tab_{i}":
                test_tab.draw_hovering(display_surface, x, y)
            else:
                test_tab.draw_not_hovering(display_surface, x, y)
            x += BORDER_SIZE - 2

        self.tests[self.selected_test].draw(display_surface)

    def interpret_line(self):
        self.jumped = False
        inst = self.subprograms[self.page][self.pc].split()
        if len(inst) == 0:
            return

        if inst[0] in self.disabled_commands:
            raise Exception("Attempt to use disabled command", self.pc)
        else:
            f = self.command_function.get(inst[0], None)
            if f is None:
                raise Exception("Attempt to use unknown command", self.pc)
            else:
                try:
                    f(*(inst[1:]))
                except Exception as msg:
                    raise Exception(msg.args[0], self.pc)

    def advance(self):
        if self.state == self.STATE_PLAYING_LEVEL:
            try:
                self.running_line = self.pc
                self.interpret_line()

                if self.tests[self.selected_test].check_done():
                    self.set_error_message("Completed task!")
                    self.stop_playing()
                    return

                if not self.jumped:
                    self.pc += 1
                    while self.pc <= 255 and len(self.subprograms[self.page][self.pc]) == 0:
                        self.pc += 1

                if self.pc >= 256:
                    raise Exception("Reached the end of the program without completing the task", -1)
            except Exception as e:
                error_msg, error_line = e.args
                self.set_error_message(error_msg, error_line)
                self.stop_playing()

    def set_error_message(self, message, error_line=-1):
        if message is None:
            self.error_messages = []
        else:
            self.error_messages = [rendertext(smallfont, line.upper(), False) for line in wrap(message, 47)]
            self.error_line = error_line

    def check_paint(self):
        self.registers["T"] = self.tests[self.selected_test].check_paint()

    def paint(self):
        self.tests[self.selected_test].paint()

    def read(self, reg):
        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = self.tests[self.selected_test].read()
        except KeyError:
            raise Exception("Bad operand, expected register name")
        except Exception as e:
            raise e

    def write(self, reg_or_val):
        try:
            value = int(reg_or_val)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad first operand, expected register name or number")

        self.tests[self.selected_test].write(value)

    def grab(self):
        self.tests[self.selected_test].grab()

    def drop(self):
        self.tests[self.selected_test].drop()

    def move_up(self):
        self.tests[self.selected_test].move_up()

    def move_right(self):
        self.tests[self.selected_test].move_right()

    def move_down(self):
        self.tests[self.selected_test].move_down()

    def move_left(self):
        self.tests[self.selected_test].move_left()

    def set_reg(self, reg, reg_or_val):
        try:
            value = int(reg_or_val)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_add(self, reg, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad third operand, expected register name or number")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value1 + value2
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_sub(self, reg, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad third operand, expected register name or number")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value1 - value2
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_mul(self, reg, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad third operand, expected register name or number")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value1 * value2
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_div(self, reg, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad third operand, expected register name or number")
        elif value2 == 0:
            # raise Exception("Attempt to divide by zero"
            raise Exception("Attempt to divide by zero")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value1 // value2
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_mod(self, reg, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad third operand, expected register name or number")
        elif value2 == 0:
            raise Exception("Attempt to divide by zero")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = value1 % value2
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_divmod(self, reg1, reg2, reg_or_val1, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad fourth operand, expected register name or number")
        elif value2 == 0:
            raise Exception("Attempt to divide by zero")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad third operand, expected register name or number")

        val, rem = divmod(value1, value2)
        try:
            if reg1 not in self.registers:
                raise KeyError
            self.registers[reg1] = val
        except KeyError:
            raise Exception("Bad first operand, expected register name")

        try:
            if reg2 not in self.registers:
                raise KeyError
            self.registers[reg2] = rem
        except KeyError:
            raise Exception("Bad second operand, expected register name")

    def do_function_call(self, reg_or_val):
        try:
            value = int(reg_or_val)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad operand, expected register name or number")
        elif value == 0:
            raise Exception("Cannot call page 0 (main program)")

        self.call_stack.append((self.page, self.pc))

        self.page = value
        self.pc = 0
        self.jumped = True

    def do_return(self):
        if len(self.call_stack) == 0:
            raise Exception("Can only return from a subprogram")
        else:
            self.page, self.pc = self.call_stack.pop()

    def get_column(self, reg):
        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = self.tests[self.selected_test].get_column()
        except KeyError:
            raise Exception("Bad operand, expected register name")

    def get_row(self, reg):
        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = self.tests[self.selected_test].get_row()
        except KeyError:
            raise Exception("Bad operand, expected register name")

    def do_push(self, reg_or_val):
        if len(self.stack) == self.stack_size:
            raise Exception("Attempt to push a full stack")

        try:
            value = int(reg_or_val)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad operand, expected register name or value")

        self.stack.append(value)

    def do_pop(self, reg):
        if len(self.stack) == 0:
            raise Exception("Attempt to pop an empty stack")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = self.stack.pop()
        except KeyError:
            raise Exception("Bad operand, expected register name")

    def do_store(self, reg_or_val1, reg_or_val2):
        try:
            address = int(reg_or_val1)
        except ValueError:
            address = self.registers.get(reg_or_val1, None)

        if address is None:
            raise Exception("Bad first operand, expected register name or number")
        elif address < 0 or address >= self.memory_size:
            raise Exception("Attempt to write outside of RAM bounds")

        try:
            value = int(reg_or_val1)
        except ValueError:
            value = self.registers.get(reg_or_val1, None)

        if value is None:
            raise Exception("Bad second operand, expected register name or number")

        self.memory[address] = value

    def do_load(self, reg, reg_or_val):
        try:
            address = int(reg_or_val)
        except ValueError:
            address = self.registers.get(reg_or_val, None)

        if address is None:
            raise Exception("Bad second operand, expected register name or number")
        elif address < 0 or address >= self.memory_size:
            raise Exception("Attempt to read outside of RAM bounds")

        try:
            if reg not in self.registers:
                raise KeyError
            self.registers[reg] = self.memory[address]
        except KeyError:
            raise Exception("Bad first operand, expected register name")

    def do_test(self, reg_or_val1, op, reg_or_val2):
        try:
            value2 = int(reg_or_val2)
        except ValueError:
            value2 = self.registers.get(reg_or_val2, None)

        if value2 is None:
            raise Exception("Bad second operand, expected register name or number")

        try:
            value1 = int(reg_or_val1)
        except ValueError:
            value1 = self.registers.get(reg_or_val1, None)

        if value1 is None:
            raise Exception("Bad first operand, expected register name or number")

        operations = {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            "<": lambda x, y: x < y,
            "<=": lambda x, y: x <= y,
            ">": lambda x, y: x > y,
            ">=": lambda x, y: x >= y,
        }

        try:
            self.registers["T"] = int(operations[op](value1, value2))
        except KeyError:
            raise Exception("Bad operation, check manual to see allowed operations")

    def do_jump(self, reg_or_val):
        try:
            value = int(reg_or_val, 16)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad operand, expected register name or hex number")

        self.pc = value
        self.jumped = True

    def do_jump_true(self, reg_or_val):
        if self.registers["T"] != 0:
            self.do_jump(reg_or_val)

    def do_jump_false(self, reg_or_val):
        if self.registers["T"] == 0:
            self.do_jump(reg_or_val)

    def do_relative_jump(self, reg_or_val):
        try:
            value = int(reg_or_val)
        except ValueError:
            value = self.registers.get(reg_or_val, None)

        if value is None:
            raise Exception("Bad operand, expected register name or number")

        self.pc += value

if __name__ == "__main__":
    TkinterWindow().withdraw()

    try:
        try:
            configfile = open(os.path.join(storage_folder, "config.json"))
        except OSError as e:
            config = dict()
        else:
            with configfile:
                config = loadjson(configfile)
                if type(config) is not dict:
                    raise ValueError("Config file should hold a json object!")

        pygame.init()
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        pygame.key.set_repeat(400, 50)

        display_surface = pygame.Surface((screen_width, screen_height))
        bigfont = pygame.font.Font("FifteenNarrow.ttf", 30)
        smallfont = pygame.font.Font("FifteenNarrow.ttf", 15)
        coordsfont = pygame.font.Font("FifteenNarrow.ttf", 12)

        game = AssemBlocks()
        game.mainloop()
    except SystemExit as msg:
        raise SystemExit from msg
    except Exception as e:
        traceback.print_exc()
        error = traceback.extract_tb(get_exception_info()[2])[-1]
        messagebox.showerror("AssemBlocks error", "An error occured at line {}: {}\n\n{}\nPlease report this to the creator of the application with a description of what you were doing at the time.".format(error.lineno, error.line, "\n".join(err for err in traceback.format_exception_only(type(e), e))))
