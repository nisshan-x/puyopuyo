from multiprocessing.pool import INIT
import sys, random
import pygame
from pygame.locals import *
from pygame.time import Clock
import numpy as np
from enum import Enum
import copy


class GameState(Enum):
    INITIAL = 0
    SPAWN = 1
    FALLING = 2
    FLOATING = 3
    ON_PUYO = 4
    RENSA = 5
    GAMEOVER = 6


class Puyo:

    disp_w = 280
    disp_h = 380
    ROW_NUM = 13
    COL_NUM = 6

    PUYO_RADIUS = 12
    EYE_RADIUS_BIG = 5
    EYE_RADIUS_SMALL = 3
    EYE_POS_BIG = [(-4, -1), (4, -1)]
    EYE_POS_SMALL = [(-4, -3), (4, -3)]
    EYE_NUM = 2

    BORDER = 20
    DISP_FIELD_TOP_LEFT = (20, 40)

    C_BLACK = (0, 0, 0)
    C_WHITE = (255, 255, 255)
    C_BROWN = (50, 0, 0)
    C_RED = (255, 0, 0)
    C_BLUE = (0, 0, 255)
    C_GREEN = (0, 180, 0)
    C_YELLOW = (190, 160, 0)
    C_PURPLE = (192, 48, 192)

    colors = [C_BLACK, C_RED, C_BLUE, C_GREEN, C_YELLOW, C_PURPLE]

    Puyo_Type_list = range(6)
    # BLANK = 0
    # RED = 1
    # BLUE = 2
    # GREEN = 3
    # YELLOW = 4
    # PURPLE = 5

    rensa_num = 0
    rensa_status = False
    score_rensa_num = 0

    my_tick = 0

    init_puyo_pos = [2, 0]
    init_sub_puyo_pos = [3, 0]
    cur_puyo_pos = copy.copy(init_puyo_pos)
    cur_sub_puyo_pos = copy.copy(init_sub_puyo_pos)
    cur_puyo_color = Puyo_Type_list[0]  # blank
    cur_sub_puyo_color = Puyo_Type_list[0]  # blank
    next_puyo_color = Puyo_Type_list[0]  # blank
    next_sub_puyo_color = Puyo_Type_list[0]  # blank

    sub_puyo_muki = 0  # 0:right, 1:down, 2:left, 3:up
    next_sub_puyo_muki = 0
    MUKI_NUM = 4

    falling_speed = 20
    speed_up_counter = 0
    SPEED_UP_INTERVAL = 2000

    game_state = GameState.INITIAL
    game_restart = False
    game_pause = False

    joy_button_num = 0
    PS3_BTN_NUM = 17
    joy_btn = [0] * PS3_BTN_NUM
    pre_joy_btn = [0] * PS3_BTN_NUM
    joy_btn_pressed = [0] * PS3_BTN_NUM

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.disp_w, self.disp_h))
        self.DISP_FIELD_SIZE = (
            self.PUYO_RADIUS * 2 * self.COL_NUM,
            self.PUYO_RADIUS * 2 * (self.ROW_NUM - 1),
        )
        pygame.display.set_caption("PUYO PUYO")  # title
        self.clock = Clock()
        pygame.key.set_repeat(200, 200)

        self.puyo_field = np.full((self.COL_NUM, self.ROW_NUM), 0)  # Row 12+1, Column 6

        self.sub_puyo_muki = 0
        self.next_sub_puyo_muki = 0
        self.cur_puyo_color = self.next_puyo_color
        self.cur_sub_puyo_color = self.next_sub_puyo_color
        self.next_puyo_color = random.randint(1, 5)
        self.next_sub_puyo_color = random.randint(1, 5)
        self.cur_puyo_pos = copy.copy(self.init_puyo_pos)
        self.cur_sub_puyo_pos = copy.copy(self.init_sub_puyo_pos)
        self.game_state = GameState.SPAWN

        # BGM
        pygame.mixer.init(frequency=44100)  # 初期設定
        pygame.mixer.music.set_volume(0.5)
        self.play_bgm()

        # Font
        self.font1 = pygame.font.SysFont(None, 50)
        self.text1 = self.font1.render("GAME OVER", True, (255, 255, 255))
        self.font2 = pygame.font.SysFont(None, 18)
        self.text2 = self.font2.render("Rensa", True, (255, 255, 255))

        # Joystick
        pygame.joystick.init()
        try:
            self.joy = pygame.joystick.Joystick(0)  # create a joystick instance
            self.joy.init()  # init instance
            print("Joystick Name: " + self.joy.get_name())
            self.joy_button_num = self.joy.get_numbuttons()
        except pygame.error:
            print("Joystick was not detected!")

    def __del__(self):
        pygame.quit()
        sys.exit()

    def play_bgm(self):
        self.sound_bgm = pygame.mixer.Sound("sound/puyopuyo_bgm.mp3")
        self.sound_bgm.play(-1)

    def play_effect_delete(self):
        self.sound_delete = pygame.mixer.Sound("sound/puyopuyo_effect_delete.mp3")
        self.sound_delete.play()

    def draw_puyo(self, color, x, y, main_flag):
        pygame.draw.circle(
            self.screen,
            color,
            (x, y),
            self.PUYO_RADIUS - 2,
        )
        if main_flag:
            pygame.draw.circle(
                self.screen, self.C_WHITE, (x, y), self.PUYO_RADIUS - 2, 1
            )

        # eyes
        for i in range(self.EYE_NUM):
            pygame.draw.circle(
                self.screen,
                self.C_WHITE,
                (
                    x + self.EYE_POS_BIG[i][0],
                    y + self.EYE_POS_BIG[i][1],
                ),
                self.EYE_RADIUS_BIG,
            )
            pygame.draw.circle(
                self.screen,
                color,
                (
                    x + self.EYE_POS_SMALL[i][0],
                    y + self.EYE_POS_SMALL[i][1],
                ),
                self.EYE_RADIUS_SMALL,
            )

    def is_main_puyo(self, c, r):
        if self.cur_puyo_pos[0] == c and self.cur_puyo_pos[1] == r:
            return True
        else:
            return False

    def draw_puyos(self):
        for c in range(self.COL_NUM):
            for r in range(self.ROW_NUM):
                if self.puyo_field[c][r]:
                    self.draw_puyo(
                        self.colors[self.puyo_field[c][r]],
                        self.DISP_FIELD_TOP_LEFT[0] + self.PUYO_RADIUS * (2 * c + 1),
                        self.DISP_FIELD_TOP_LEFT[1] + self.PUYO_RADIUS * (2 * r - 1),
                        self.is_main_puyo(c, r),
                    )

    def draw_hidden_bar(self):
        pygame.draw.rect(
            self.screen,
            self.C_BLACK,
            (
                self.DISP_FIELD_TOP_LEFT[0],
                self.DISP_FIELD_TOP_LEFT[1] - self.PUYO_RADIUS * 2,
                self.PUYO_RADIUS * 2 * self.COL_NUM,
                self.PUYO_RADIUS * 2,
            ),
        )

    def draw_frame(self):
        pygame.draw.rect(
            self.screen,
            self.C_BROWN,
            (
                self.DISP_FIELD_TOP_LEFT[0] - self.BORDER,
                self.DISP_FIELD_TOP_LEFT[1] - self.BORDER,
                self.DISP_FIELD_SIZE[0] + self.BORDER * 2,
                self.DISP_FIELD_SIZE[1] + self.BORDER * 2,
            ),
            self.BORDER,
        )
        pygame.draw.rect(
            self.screen,
            self.C_BROWN,
            (
                self.DISP_FIELD_TOP_LEFT[0] + self.DISP_FIELD_SIZE[0],
                self.DISP_FIELD_TOP_LEFT[1] - self.BORDER,
                self.PUYO_RADIUS * 6 + self.BORDER,
                self.PUYO_RADIUS * 8 + self.BORDER,
            ),
            self.BORDER,
        )

    def draw_next_puyo(self):
        self.draw_puyo(
            self.colors[self.next_puyo_color],
            self.DISP_FIELD_TOP_LEFT[0]
            + self.DISP_FIELD_SIZE[0]
            + self.PUYO_RADIUS * 4,
            self.DISP_FIELD_TOP_LEFT[1] + self.PUYO_RADIUS * 2,
            False,
        )
        self.draw_puyo(
            self.colors[self.next_sub_puyo_color],
            self.DISP_FIELD_TOP_LEFT[0]
            + self.DISP_FIELD_SIZE[0]
            + self.PUYO_RADIUS * 4,
            self.DISP_FIELD_TOP_LEFT[1] + self.PUYO_RADIUS * 4,
            False,
        )

    def check_chained_list_sub(self, col, row, del_check_puyo, chained_list, cur_col):
        if self.puyo_field[col][row] == cur_col:
            chained_list.append((col, row))
            chained_list = self.check_chained_list(
                col, row, del_check_puyo, chained_list
            )
        return chained_list

    def check_chained_list(self, col, row, del_check_puyo, chained_list):
        del_check_puyo[col][row] = True
        if self.puyo_field[col][row] == self.Puyo_Type_list[0]:  # BLANK
            return chained_list

        cur_col = self.puyo_field[col][row]

        # left
        next_col = col - 1
        next_row = row
        if col > 0 and del_check_puyo[next_col][next_row] == False:
            chained_list = self.check_chained_list_sub(
                next_col, next_row, del_check_puyo, chained_list, cur_col
            )
        # top
        next_col = col
        next_row = row - 1
        if row > 0 and del_check_puyo[next_col][next_row] == False:
            chained_list = self.check_chained_list_sub(
                next_col, next_row, del_check_puyo, chained_list, cur_col
            )
        # right
        next_col = col + 1
        next_row = row
        if col < self.COL_NUM - 1 and del_check_puyo[next_col][next_row] == False:
            chained_list = self.check_chained_list_sub(
                next_col, next_row, del_check_puyo, chained_list, cur_col
            )
        # Bottom
        next_col = col
        next_row = row + 1
        if row < self.ROW_NUM - 1 and del_check_puyo[next_col][next_row] == False:
            chained_list = self.check_chained_list_sub(
                next_col, next_row, del_check_puyo, chained_list, cur_col
            )

        return chained_list

    def check_droppable(self):
        droppable = False
        for c in range(self.COL_NUM):
            tmp = self.puyo_field[c].copy()
            blank_list = np.where(tmp == self.Puyo_Type_list[0])

            # check droppable
            if blank_list[0] != []:
                if blank_list[0][0] != 0:
                    droppable = True
                    # print("    droppable", droppable)
                else:
                    for i, index in enumerate(blank_list[0]):
                        if i + 1 < len(blank_list[0]):
                            if blank_list[0][i] + 1 != blank_list[0][i + 1]:
                                droppable = True
                                # print("    droppable", droppable)
        return droppable

    # Need to call check_droppable() before calling drop()
    def drop(self):
        for c in range(self.COL_NUM):
            tmp = self.puyo_field[c].copy()

            # drop
            tmp = np.delete(tmp, np.where(tmp == self.Puyo_Type_list[0]))
            while len(tmp) < self.ROW_NUM:
                tmp = np.insert(tmp, 0, self.Puyo_Type_list[0])

            self.puyo_field[c] = tmp.copy()
        return True

    def delete(self):
        del_check_puyo = np.full((self.COL_NUM, self.ROW_NUM), False)
        no_chain_to_delete_flag = True
        for c in range(self.COL_NUM):
            # print("c", c)
            for r in reversed(range(1, self.ROW_NUM)):
                # print("r", r)
                chained_list = [(c, r)]
                chained_list = self.check_chained_list(
                    c, r, del_check_puyo, chained_list
                )
                if len(chained_list) >= 4:
                    # print(len(chained_list), chained_list)

                    # delete
                    for item in chained_list:
                        # set BLANK
                        self.puyo_field[item[0]][item[1]] = self.Puyo_Type_list[0]
                    if no_chain_to_delete_flag:
                        self.rensa_num += 1
                        self.rensa_status = True
                        self.score_rensa_num = self.rensa_num

                        self.play_effect_delete()
                        pygame.time.delay(250)

                    no_chain_to_delete_flag = False

        # print("rensa_num", self.rensa_num)

        if no_chain_to_delete_flag and not self.check_droppable():
            self.rensa_status = False
            self.rensa_num = 0

    def rotate_left_or_right(self, direction):
        if direction == "left":
            self.next_sub_puyo_muki = (self.sub_puyo_muki - 1) % self.MUKI_NUM
        else:
            self.next_sub_puyo_muki = (self.sub_puyo_muki + 1) % self.MUKI_NUM

        if self.next_sub_puyo_muki == 0:  # go right
            self.rotate_and_go_right()
        if self.next_sub_puyo_muki == 1:  # go down
            self.rotate_and_go_down()
        if self.next_sub_puyo_muki == 2:  # go left
            self.rotate_and_go_left()
        if self.next_sub_puyo_muki == 3:  # go up
            self.rotate_and_go_up()

    def rotate_and_go_right(self):
        # 右にぷよがあるか？ もしくは右に壁があるか？
        if (self.cur_puyo_pos[0] == self.COL_NUM - 1) or (
            self.cur_puyo_pos[0] < self.COL_NUM - 1
            and self.puyo_field[self.cur_puyo_pos[0] + 1][self.cur_puyo_pos[1]]
            != self.Puyo_Type_list[0]
        ):
            # メインの左にぷよがあるか？ もしくは左に壁があるか？
            if (self.cur_puyo_pos[0] == 0) or (
                self.cur_puyo_pos[0] > 0
                and self.puyo_field[self.cur_puyo_pos[0] - 1][self.cur_puyo_pos[1]]
                != self.Puyo_Type_list[0]
            ):
                pass
            else:
                # メインを左に1つずらす
                # メインの元の位置にサブを置く
                main_color = self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]]
                # メインを新しい位置に置く
                self.puyo_field[self.cur_puyo_pos[0] - 1][
                    self.cur_puyo_pos[1]
                ] = main_color
                sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                    self.cur_sub_puyo_pos[1]
                ]
                # サブを新しい位置(=元のメインの位置)に置く
                self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]] = sub_color
                # サブの元の位置にブランクを置く
                self.puyo_field[self.cur_sub_puyo_pos[0]][
                    self.cur_sub_puyo_pos[1]
                ] = self.Puyo_Type_list[0]
                # メインとサブの位置と向きを更新する
                self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
                self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
                self.cur_puyo_pos[0] -= 1
                self.sub_puyo_muki = self.next_sub_puyo_muki

        else:
            # 右の位置にサブを置く
            sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ]
            # サブを新しい位置に置く
            self.puyo_field[self.cur_puyo_pos[0] + 1][self.cur_puyo_pos[1]] = sub_color
            # サブの元の位置にブランクを置く
            self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ] = self.Puyo_Type_list[0]
            # サブの位置と向きを更新する
            self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0] + 1
            self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
            self.sub_puyo_muki = self.next_sub_puyo_muki

    def rotate_and_go_down(self):
        # サブを下にしたい。
        # メインが最下層にあるか？　もしくは下にぷよがあるか？
        if self.cur_puyo_pos[1] == self.ROW_NUM - 1:
            # メインを上に1つ上げる
            # メインの元の位置にサブを置く
            main_color = self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]]
            # メインを新しい位置に置く
            self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1] - 1] = main_color
            sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ]
            # サブを新しい位置(=元のメインの位置)に置く
            self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]] = sub_color
            # サブの元の位置にブランクを置く
            self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ] = self.Puyo_Type_list[0]
            # メインとサブの位置と向きを更新する
            self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
            self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
            self.cur_puyo_pos[1] -= 1
            self.sub_puyo_muki = self.next_sub_puyo_muki
        elif (
            self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1] + 1]
            != self.Puyo_Type_list[0]
        ):
            # メインを上に1つ上げる
            # メインの元の位置にサブを置く
            main_color = self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]]
            # メインを新しい位置に置く
            self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1] - 1] = main_color
            sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ]
            # サブを新しい位置(=元のメインの位置)に置く
            self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]] = sub_color
            # サブの元の位置にブランクを置く
            self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ] = self.Puyo_Type_list[0]
            # メインとサブの位置と向きを更新する
            self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
            self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
            self.cur_puyo_pos[1] -= 1
            self.sub_puyo_muki = self.next_sub_puyo_muki
        else:
            # 下の位置にサブを置く
            # サブを新しい位置に置く
            self.puyo_field[self.cur_puyo_pos[0]][
                self.cur_puyo_pos[1] + 1
            ] = self.puyo_field[self.cur_sub_puyo_pos[0]][self.cur_sub_puyo_pos[1]]
            # サブの元の位置にブランクを置く
            self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ] = self.Puyo_Type_list[0]
            # サブの位置と向きを更新する
            self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
            self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1] + 1
            self.sub_puyo_muki = self.next_sub_puyo_muki

    def rotate_and_go_left(self):
        # 左にぷよがあるか？ もしくは左に壁があるか？
        if (self.cur_puyo_pos[0] == 0) or (
            self.cur_puyo_pos[0] > 0
            and self.puyo_field[self.cur_puyo_pos[0] - 1][self.cur_puyo_pos[1]]
            != self.Puyo_Type_list[0]
        ):
            # メインの右にぷよがあるか？ もしくは右に壁があるか？
            if (self.cur_puyo_pos[0] == self.COL_NUM - 1) or (
                self.cur_puyo_pos[0] < self.COL_NUM - 1
                and self.puyo_field[self.cur_puyo_pos[0] + 1][self.cur_puyo_pos[1]]
                != self.Puyo_Type_list[0]
            ):
                pass
            else:
                # メインを右に1つずらす
                # メインの元の位置にサブを置く
                main_color = self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]]
                # メインを新しい位置に置く
                self.puyo_field[self.cur_puyo_pos[0] + 1][
                    self.cur_puyo_pos[1]
                ] = main_color
                sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                    self.cur_sub_puyo_pos[1]
                ]
                # サブを新しい位置(=元のメインの位置)に置く
                self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]] = sub_color
                # サブの元の位置にブランクを置く
                self.puyo_field[self.cur_sub_puyo_pos[0]][
                    self.cur_sub_puyo_pos[1]
                ] = self.Puyo_Type_list[0]
                # メインとサブの位置と向きを更新する
                self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
                self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
                self.cur_puyo_pos[0] += 1
                self.sub_puyo_muki = self.next_sub_puyo_muki

        else:
            # 左の位置にサブを置く
            sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ]
            # サブを新しい位置に置く
            self.puyo_field[self.cur_puyo_pos[0] - 1][self.cur_puyo_pos[1]] = sub_color
            # サブの元の位置にブランクを置く
            self.puyo_field[self.cur_sub_puyo_pos[0]][
                self.cur_sub_puyo_pos[1]
            ] = self.Puyo_Type_list[0]
            # サブの位置と向きを更新する
            self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0] - 1
            self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1]
            self.sub_puyo_muki = self.next_sub_puyo_muki

    def rotate_and_go_up(self):
        # サブを上にしたい
        # メインの上の位置にサブを置く
        # 　サブを新しい位置に置く
        self.puyo_field[self.cur_puyo_pos[0]][
            self.cur_puyo_pos[1] - 1
        ] = self.puyo_field[self.cur_sub_puyo_pos[0]][self.cur_sub_puyo_pos[1]]
        # サブの元の位置にブランクを置く
        self.puyo_field[self.cur_sub_puyo_pos[0]][
            self.cur_sub_puyo_pos[1]
        ] = self.Puyo_Type_list[0]
        # サブの位置と向きを更新する
        self.cur_sub_puyo_pos[0] = self.cur_puyo_pos[0]
        self.cur_sub_puyo_pos[1] = self.cur_puyo_pos[1] - 1
        self.sub_puyo_muki = self.next_sub_puyo_muki

    def move(self, direction):
        if direction == "left":
            # 左に動かす
            # メインかサブが左端にある場合
            if self.cur_puyo_pos[0] == 0 or self.cur_sub_puyo_pos[0] == 0:
                # 　何もしない
                return
            # サブの位置がメインの上か下の場合
            if self.sub_puyo_muki == 1 or self.sub_puyo_muki == 3:
                # メインの左隣りに何かある、もしくはサブの左隣りに何かある場合
                if (
                    self.puyo_field[self.cur_puyo_pos[0] - 1][self.cur_puyo_pos[1]]
                    != self.Puyo_Type_list[0]
                    or self.puyo_field[self.cur_sub_puyo_pos[0] - 1][
                        self.cur_sub_puyo_pos[1]
                    ]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 左へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] - 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] - 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　メインとサブの元の位置にブランクを置く
                    self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] -= 1
                    self.cur_sub_puyo_pos[0] -= 1
                    # サブの位置がメインの左の場合
            elif self.sub_puyo_muki == 2:
                # サブの左隣りに何かある場合
                if (
                    self.puyo_field[self.cur_sub_puyo_pos[0] - 1][
                        self.cur_sub_puyo_pos[1]
                    ]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 左へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] - 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] - 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　メインの元の位置にブランクを置く
                    self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] -= 1
                    self.cur_sub_puyo_pos[0] -= 1
            else:  # サブの位置がメインの右の場合
                # メインの左隣りに何かある場合
                if (
                    self.puyo_field[self.cur_puyo_pos[0] - 1][self.cur_puyo_pos[1]]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 左へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] - 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] - 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　サブの元の位置にブランクを置く
                    self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] -= 1
                    self.cur_sub_puyo_pos[0] -= 1

        else:  # right
            # 右に動かす
            # メインかサブが右端にある場合
            if (
                self.cur_puyo_pos[0] == self.COL_NUM - 1
                or self.cur_sub_puyo_pos[0] == self.COL_NUM - 1
            ):
                # 　何もしない
                return
            # サブの位置がメインの上か下の場合
            if self.sub_puyo_muki == 1 or self.sub_puyo_muki == 3:
                # メインの右隣りに何かある、もしくはサブの右隣りに何かある場合
                if (
                    self.puyo_field[self.cur_puyo_pos[0] + 1][self.cur_puyo_pos[1]]
                    != self.Puyo_Type_list[0]
                    or self.puyo_field[self.cur_sub_puyo_pos[0] + 1][
                        self.cur_sub_puyo_pos[1]
                    ]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 右へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] + 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] + 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　メインとサブの元の位置にブランクを置く
                    self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] += 1
                    self.cur_sub_puyo_pos[0] += 1
            # サブの位置がメインの左の場合
            elif self.sub_puyo_muki == 2:
                # メインの右隣りに何かある場合
                if (
                    self.puyo_field[self.cur_puyo_pos[0] + 1][self.cur_puyo_pos[1]]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 右へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] + 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] + 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　サブの元の位置にブランクを置く
                    self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] += 1
                    self.cur_sub_puyo_pos[0] += 1
            else:  # サブの位置がメインの右の場合
                # サブの右隣りに何かある場合
                if (
                    self.puyo_field[self.cur_sub_puyo_pos[0] + 1][
                        self.cur_sub_puyo_pos[1]
                    ]
                    != self.Puyo_Type_list[0]
                ):
                    # 　何もしない
                    return
                else:
                    # 右へ動かす
                    # 　新しい位置にメインとサブを置く
                    main_color = self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ]
                    sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                        self.cur_sub_puyo_pos[1]
                    ]
                    self.puyo_field[self.cur_puyo_pos[0] + 1][
                        self.cur_puyo_pos[1]
                    ] = main_color
                    self.puyo_field[self.cur_sub_puyo_pos[0] + 1][
                        self.cur_sub_puyo_pos[1]
                    ] = sub_color
                    # 　メインの元の位置にブランクを置く
                    self.puyo_field[self.cur_puyo_pos[0]][
                        self.cur_puyo_pos[1]
                    ] = self.Puyo_Type_list[0]
                    # 　メインとサブの位置を更新する
                    self.cur_puyo_pos[0] += 1
                    self.cur_sub_puyo_pos[0] += 1

    def loop(self):
        # Update key input
        for event in pygame.event.get(KEYDOWN):
            if event.key == K_DOWN:
                self.my_tick = self.falling_speed
            elif event.key == K_LEFT:
                self.move("left")
            elif event.key == K_RIGHT:
                self.move("right")
            elif event.key == K_q:
                pygame.quit()
                sys.exit()
            elif event.key == K_w:
                # randomize puyo for test
                self.puyo_field = np.random.randint(0, 6, (self.COL_NUM, self.ROW_NUM))
            elif event.key == K_z:  # rotate left
                if self.game_state == GameState.FLOATING:
                    self.rotate_left_or_right("left")
            elif event.key == K_x:  # rotate right
                if self.game_state == GameState.FLOATING:
                    self.rotate_left_or_right("right")
            elif event.key == K_r:
                self.game_restart = True
            elif event.key == K_p:
                self.game_pause = not self.game_pause

        # こっちでキーイベントを拾うと、激しくリピートする
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[K_DOWN]:
            self.my_tick = self.falling_speed

        # update joystick event
        if pygame.joystick.get_count():
            for i in range(self.joy_button_num):
                self.pre_joy_btn[i] = self.joy_btn[i]
                self.joy_btn[i] = self.joy.get_button(i)

                if self.pre_joy_btn[i] == False and self.joy_btn[i]:
                    self.joy_btn_pressed[i] = True
                else:
                    self.joy_btn_pressed[i] = False

            if self.joy_btn[14]:  # down - log press
                self.my_tick = self.falling_speed
            elif self.joy_btn_pressed[15]:  # left
                self.move("left")
            elif self.joy_btn_pressed[16]:  # right
                self.move("right")
            elif self.joy_btn_pressed[4] and self.joy_btn_pressed[5]:  # L and R
                pygame.quit()
                sys.exit()
            elif (
                self.joy_btn_pressed[2] and self.joy_btn_pressed[3]
            ):  # triangle and square
                # randomize puyo for test
                self.puyo_field = np.random.randint(0, 6, (self.COL_NUM, self.ROW_NUM))
            elif self.joy_btn_pressed[0]:  # cross - rotate left
                if self.game_state == GameState.FLOATING:
                    self.rotate_left_or_right("left")
            elif self.joy_btn_pressed[1]:  # circle - rotate right
                if self.game_state == GameState.FLOATING:
                    self.rotate_left_or_right("right")
            elif self.joy_btn_pressed[9]:  # start
                self.game_restart = True
            elif self.joy_btn_pressed[8]:  # select
                self.game_pause = not self.game_pause

        # spawn new puyo
        if self.game_state == GameState.SPAWN:
            self.sub_puyo_muki = 0
            self.next_sub_puyo_muki = 0
            self.cur_puyo_color = self.next_puyo_color
            self.cur_sub_puyo_color = self.next_sub_puyo_color
            self.next_puyo_color = random.randint(1, 5)
            self.next_sub_puyo_color = random.randint(1, 5)
            self.cur_puyo_pos = copy.copy(self.init_puyo_pos)
            self.cur_sub_puyo_pos = copy.copy(self.init_sub_puyo_pos)

            if (
                self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1]]
                != self.Puyo_Type_list[0]
                or self.puyo_field[self.cur_sub_puyo_pos[0]][self.cur_sub_puyo_pos[1]]
                != self.Puyo_Type_list[0]
            ):
                self.game_state = GameState.GAMEOVER

            else:
                self.puyo_field[self.cur_puyo_pos[0]][
                    self.cur_puyo_pos[1]
                ] = self.cur_puyo_color
                self.puyo_field[self.cur_sub_puyo_pos[0]][
                    self.cur_sub_puyo_pos[1]
                ] = self.cur_sub_puyo_color
                self.game_state = GameState.FALLING

        # puyo is falling
        if self.game_state == GameState.FALLING:
            # メインかサブが最下段にあれば
            if (
                self.cur_sub_puyo_pos[1] == self.ROW_NUM - 1
                or self.cur_puyo_pos[1] == self.ROW_NUM - 1
            ):
                self.game_state = GameState.ON_PUYO
            else:
                # サブの向きがメインの左か右のとき
                if self.sub_puyo_muki == 0 or self.sub_puyo_muki == 2:
                    # メインの下に何かある もしくは サブの下に何かある 場合
                    if (
                        self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1] + 1]
                        != self.Puyo_Type_list[0]
                        or self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1] + 1
                        ]
                        != self.Puyo_Type_list[0]
                    ):
                        # 状態を着地とする
                        self.game_state = GameState.ON_PUYO
                    # メインの下にもサブの下にも何もない 場合
                    else:
                        # サブとメインを1つ下にずらす
                        main_color = self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1]
                        ]
                        sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1]
                        ]
                        self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1] + 1
                        ] = main_color
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1] + 1
                        ] = sub_color
                        self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1]
                        ] = self.Puyo_Type_list[0]
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1]
                        ] = self.Puyo_Type_list[0]
                        self.cur_puyo_pos[1] += 1
                        self.cur_sub_puyo_pos[1] += 1
                        # 状態を浮きとする
                        self.game_state = GameState.FLOATING

                # サブの向きがメインの上のとき
                elif self.sub_puyo_muki == 3:
                    # メインの下に何かある場合
                    if (
                        self.puyo_field[self.cur_puyo_pos[0]][self.cur_puyo_pos[1] + 1]
                        != self.Puyo_Type_list[0]
                    ):
                        # 状態を着地とする
                        self.game_state = GameState.ON_PUYO

                    # メインの下に何もない場合
                    else:
                        # サブとメインを1つ下にずらす
                        main_color = self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1]
                        ]
                        sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1]
                        ]
                        self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1] + 1
                        ] = main_color
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1] + 1
                        ] = sub_color
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1]
                        ] = self.Puyo_Type_list[0]
                        self.cur_puyo_pos[1] += 1
                        self.cur_sub_puyo_pos[1] += 1
                        # 状態を浮きとする
                        self.game_state = GameState.FLOATING

                # サブの向きがメインの下のとき
                else:
                    # サブの下に何かある場合
                    if (
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1] + 1
                        ]
                        != self.Puyo_Type_list[0]
                    ):
                        # 状態を着地とする
                        self.game_state = GameState.ON_PUYO
                    # サブの下に何もない場合
                    else:
                        # サブとメインを1つ下にずらす
                        main_color = self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1]
                        ]
                        sub_color = self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1]
                        ]
                        self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1] + 1
                        ] = main_color
                        self.puyo_field[self.cur_sub_puyo_pos[0]][
                            self.cur_sub_puyo_pos[1] + 1
                        ] = sub_color
                        self.puyo_field[self.cur_puyo_pos[0]][
                            self.cur_puyo_pos[1]
                        ] = self.Puyo_Type_list[0]
                        self.cur_puyo_pos[1] += 1
                        self.cur_sub_puyo_pos[1] += 1
                        # 状態を浮きとする
                        self.game_state = GameState.FLOATING

        if self.game_state == GameState.ON_PUYO:
            self.drop()
            self.game_state = GameState.RENSA

        if self.game_state == GameState.FLOATING:
            if self.my_tick % self.falling_speed == 0:
                self.game_state = GameState.FALLING

        if self.game_state == GameState.RENSA:
            if self.check_droppable():
                self.drop()
            else:
                self.delete()
                if self.rensa_status == False:
                    self.game_state = GameState.SPAWN

        if self.game_state == GameState.GAMEOVER:
            self.sound_bgm.stop()

        # draw
        self.screen.fill((0, 0, 0))
        self.draw_puyos()
        self.draw_hidden_bar()
        self.draw_frame()
        self.draw_next_puyo()

        if self.game_state == GameState.GAMEOVER:
            self.screen.blit(self.text1, (20, 150))

        self.screen.blit(self.text2, (200, 150))  # rensa
        self.text3 = self.font2.render(str(self.score_rensa_num), True, (255, 255, 255))
        self.screen.blit(self.text3, (220, 170))

        # Update display
        pygame.display.update()

        # Check event to terminate.
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        # debug
        # print("self.game_state", self.game_state)

        if not self.game_pause:
            self.my_tick += 1

            self.speed_up_counter += 1
            if self.speed_up_counter % self.SPEED_UP_INTERVAL == 0:
                if self.falling_speed > 2:
                    self.falling_speed -= 1

            print("self.falling_speed", self.falling_speed)

        self.clock.tick(30)

        return self.game_restart
