# coding: utf-8
#
"""Pygame front‑end for the PythonBots arena.

This module wraps the core ``Arena`` and ``Bot`` classes with rendering
logic using pygame. It also implements various particle effects and
sound playback. The code has been updated for Python 3 and English
comments but retains Portuguese method and variable names for
compatibility.
"""

import pygame
import random
import os
import pythonbots.arena
import pythonbots.bot
from pythonbots.constants import *
from math import sin, cos
from numpy import linspace

#
# Constantes graficas
#
CORES = (
(255,0,0),
(0,255,0),
(0,0,255),
(255,255,0),
(255,0,255),
(0,255,255),
(255,255,255),
(255,100,50),
(50,255,100),
(100,50,255),
(255,40,120),
(40,255,120),
(120,50,255),
)

AREA_INFERIOR = 70
BOT_INFO_X = 140
BOT_INFO_Y = 65
MAX_MSG = 4

#
# Classe bot extendida para tratar callbacks
#
class Bot(pythonbots.bot.Bot):

        # Callback hooks mapped to the English core API
        def on_wall_collision(self):
                if self.arena.text_mode:
                        return
                if getattr(self.arena, 'sound', False) and getattr(self.arena, 'mixer', False):
                        self.arena.snd_wall_collision.play(0, 20)
                px = 0 if self.position.x <= RADIUS else (ARENA_WIDTH if self.position.x >= ARENA_WIDTH - RADIUS else self.position.x)
                py = 0 if self.position.y <= RADIUS else (ARENA_HEIGHT if self.position.y >= ARENA_HEIGHT - RADIUS else self.position.y)
                vx = -self.velocity.x if self.position.x <= RADIUS or self.position.x >= ARENA_WIDTH - RADIUS else self.velocity.x
                vy = -self.velocity.y if self.position.y <= RADIUS or self.position.y >= ARENA_HEIGHT - RADIUS else self.velocity.y

                # sparks from wall collision
                for _ in range(10):
                        self.arena.sparks.append({'life': PI / 2, 'pos': [px, py], 'vel': (vx * 2 + random.uniform(-1, 1), vy * 2 + random.uniform(-1, 1))})

        def on_bot_collision(self, other):
                if self.arena.text_mode:
                        return
                if getattr(self.arena, 'sound', False) and getattr(self.arena, 'mixer', False):
                        self.arena.snd_bot_collision.play(0, 30)
                pos = (self.position + other.position) / 2
                vel = (self.velocity + other.velocity) / 2
                for _ in range(4):
                        self.arena.sparks.append({'life': PI / 2, 'pos': [pos.x, pos.y], 'vel': (vel.x * 2 + random.uniform(-2, 2), vel.y * 2 + random.uniform(-2, 2))})

        def on_shot_collision(self, shot):
                if self.arena.text_mode:
                        return
                if not self.active:
                        # ensure time_of_death exists
                        self.time_of_death = getattr(self, 'time_of_death', self.arena.ticks)
                        self.time_of_death = (self.arena.ticks + self.time_of_death * 2) / 3
                if getattr(self.arena, 'sound', False) and getattr(self.arena, 'mixer', False):
                        self.arena.snd_shot_collision.play(0, 25)
                self.arena.smokes.append({'life': PI / 2, 'pos': (shot.position.x, shot.position.y), 'col': (255, 255, 0), 'rad': 10})

        def die(self):
                self.arena.showMsg(str(self) + ' was killed by ' + (str(self.killed_by) if self.killed_by else 'accident') + '.')
                if self.arena.text_mode:
                        return
                if getattr(self.arena, 'sound', False) and getattr(self.arena, 'mixer', False):
                        self.arena.snd_death.play()
                self.time_of_death = self.arena.ticks

                # sparks on the side panel
                for _ in range(100):
                        px = random.uniform(ARENA_WIDTH, BOT_INFO_X + ARENA_WIDTH)
                        py = random.uniform(self.index * BOT_INFO_Y, self.index * BOT_INFO_Y + BOT_INFO_Y) if px <= ARENA_WIDTH + 10 or px >= (BOT_INFO_X + ARENA_WIDTH) - 10 else random.choice((self.index * BOT_INFO_Y, self.index * BOT_INFO_Y + BOT_INFO_Y))
                        self.arena.sparks.append({
                                'life': PI / 2,
                                'pos': [px, py],
                                'vel': (
                                        (px - (ARENA_WIDTH + BOT_INFO_X / 2)) / 12.0 + random.uniform(-1, 1),
                                        (py - (self.index * BOT_INFO_Y + BOT_INFO_Y / 2)) / 12.0 + random.uniform(-1, 1),
                                ),
                        })

                # smoke zone
                for _ in range(10):
                        self.arena.smokes.append({
                                'life': PI / 2,
                                'pos': (
                                        self.position.x + random.uniform(-RADIUS / 2, RADIUS / 2),
                                        self.position.y + random.uniform(-RADIUS / 2, RADIUS / 2),
                                ),
                                'col': (255, random.randint(0, 255), random.randint(0, 100)),
                                'rad': RADIUS * 4,
                        })

                for _ in range(20):
                        self.arena.sparks.append({
                                'life': PI / 2,
                                'pos': [self.position.x, self.position.y],
                                'vel': (
                                        self.velocity.x * 2 + random.uniform(-4, 4),
                                        self.velocity.y * 2 + random.uniform(-4, 4),
                                ),
                        })

                for _ in range(20):
                        self.arena.debris.append({
                                'life': PI / 2,
                                'pos': [
                                        self.position.x + random.uniform(-RADIUS, RADIUS),
                                        self.position.y + random.uniform(-RADIUS, RADIUS),
                                ],
                                'vel': [
                                        self.velocity.x * 2 + random.uniform(-4, 4),
                                        self.velocity.y * 2 + random.uniform(-4, 4),
                                ],
                                'col': CORES[self.index],
                        })

#
# Classe tiro extendida para tratar callbacks
#
class Tiro(pythonbots.arena.Shot):

        def on_wall_collision(self, arena):
                if arena.text_mode:
                        return
                arena.smokes.append({'life': PI / 2, 'pos': (self.position.x, self.position.y), 'col': (255, 255, 255), 'rad': 6})

#
# classe Arena extendida para desenhar com pygame
#
class Arena(pythonbots.arena.Arena):

        def __init__(self, text_mode, *args, **kargs):
                super().__init__(*args, **kargs)

                self.text_mode = text_mode
                # UI toggles
                self.show_arcs = True
                self.show_names = True
                self.sound = True

                if not self.text_mode:
                        pygame.init()
                        pygame.display.set_mode((ARENA_WIDTH + BOT_INFO_X, ARENA_HEIGHT + AREA_INFERIOR))
                        pygame.display.set_caption('Pythonbots')
                        self.screen = pygame.display.get_surface()

                        # fonts
                        self.font1 = pygame.font.Font(None, 12)
                        self.font2 = pygame.font.Font(None, 16)

                        # sounds
                        if pygame.mixer.get_init():
                                self.snd_shot = pygame.mixer.Sound(os.path.join('snd', 'tiro.wav'))
                                self.snd_shot.set_volume(.1)
                                self.snd_bot_collision = pygame.mixer.Sound(os.path.join('snd', 'colisao.wav'))
                                self.snd_bot_collision.set_volume(.15)
                                self.snd_shot_collision = pygame.mixer.Sound(os.path.join('snd', 'colisao.wav'))
                                self.snd_shot_collision.set_volume(.1)
                                self.snd_wall_collision = pygame.mixer.Sound(os.path.join('snd', 'colisao.wav'))
                                self.snd_wall_collision.set_volume(.06)
                                self.snd_death = pygame.mixer.Sound(os.path.join('snd', 'morte.wav'))
                                self.snd_death.set_volume(.5)
                                self.mixer = True
                        else:
                                self.mixer = False

        # metodo sobreescrevido para funcionar com bot extendido
        def start(self):
                self.shots = []
                self.bots = []
                self.msg = ['round started.']
                self.ticks = 0
                self.done = False
                if not self.text_mode:
                        self.debris = []
                        self.sparks = []
                        self.smokes = []
                pythonbots.bot.bot_index_count = 0
                for f in self.functions:
                        self.bots.append(Bot(self, f))

        # adiciona tiro ao sistema(overloaded)
        def add_shot(self, bot):
                self.shots.append(Tiro(bot))
                if not self.text_mode and getattr(self, 'sound', False) and self.mixer:
                        self.snd_shot.play(0, 15)

        def update(self):
                """Advance visuals (particle lifetimes) after the core update."""
                super().update()

                if self.text_mode:
                        return

                # update smokes
                for f in list(self.smokes):
                        if 'vel' in f:
                                f['pos'][0] += f['vel'][0]
                                f['pos'][1] += f['vel'][1]
                        f['life'] -= 0.08
                        if f['life'] <= 0:
                                self.smokes.remove(f)

                # update sparks
                for f in list(self.sparks):
                        f['pos'][0] += f['vel'][0]
                        f['pos'][1] += f['vel'][1]
                        f['life'] -= 0.1
                        if f['life'] <= 0:
                                self.sparks.remove(f)

                # update debris
                for f in list(self.debris):
                        f['pos'][0] += f['vel'][0]
                        f['pos'][1] += f['vel'][1]
                        f['vel'][0] *= 0.8
                        f['vel'][1] *= 0.8
                        f['life'] -= 0.005
                        if f['life'] <= 0:
                                self.debris.remove(f)

                # occasional bot effects already handled; leave physics to core

        def showMsg(self, msg: str) -> None:
                """Display a message either to the console or on screen."""
                if self.text_mode:
                        print(msg)
                else:
                        self.msg.insert(0, msg)
                        if len(self.msg) > MAX_MSG:
                                self.msg.pop()

        def draw(self) -> None:
                if self.text_mode:
                        return

                # clear screen
                self.screen.fill((0, 0, 0))

                vivos = self.alive_count()

                # draw bots
                for bot in self.bots:
                        if self.show_arcs and bot.active:
                                pygame.draw.aalines(
                                        self.screen,
                                        (50, 50, 50),
                                        True,
                                        [
                                                (bot.position.x + cos(bot.direction + bot.cannon) * RADIUS, bot.position.y + sin(bot.direction + bot.cannon) * RADIUS)
                                        ]
                                        + [
                                                (
                                                        bot.position.x + cos((bot.direction + bot.cannon) + x) * VISION_RANGE,
                                                        bot.position.y + sin((bot.direction + bot.cannon) + x) * VISION_RANGE,
                                                )
                                                for x in linspace(-bot.scan_arc / 2.0, bot.scan_arc / 2.0, 10)
                                        ],
                                )

                        if self.show_names:
                                name = self.font1.render(bot.func.__name__, False, CORES[bot.index])
                                self.screen.blit(name, (bot.position.x - name.get_size()[0] / 2, bot.position.y + RADIUS))

                        # draw body
                        pygame.draw.aalines(
                                self.screen,
                                CORES[bot.index] if bot.active else (50, 50, 50),
                                True,
                                (
                                        (bot.position.x + cos(bot.direction) * RADIUS, bot.position.y + sin(bot.direction) * RADIUS),
                                        (bot.position.x + cos(bot.direction + 2.5) * RADIUS, bot.position.y + sin(bot.direction + 2.5) * RADIUS),
                                        (bot.position.x + cos(bot.direction - 2.5) * RADIUS, bot.position.y + sin(bot.direction - 2.5) * RADIUS),
                                ),
                        )

                        # draw cannon
                        pygame.draw.aaline(
                                self.screen,
                                CORES[bot.index] if bot.active else (50, 50, 50),
                                (bot.position.x, bot.position.y),
                                (bot.position.x + cos(bot.direction + bot.cannon) * RADIUS, bot.position.y + sin(bot.direction + bot.cannon) * RADIUS),
                        )

                        if vivos == 1 and bot.active and not self.done:
                                self.showMsg(str(bot) + ' won the match!')
                                self.done = True

                # draw shots
                for shot in self.shots:
                        pygame.draw.line(self.screen, (255, 255, 255), (shot.position.x, shot.position.y), (shot.position.x + shot.velocity.x, shot.position.y + shot.velocity.y))

                # tie condition
                if (vivos == 0 or self.ticks > MAX_TIME) and not self.done:
                        self.showMsg('the match was a tie.')
                        self.done = True

                # arena border
                pygame.draw.rect(self.screen, (255, 255, 255), ((0, 0), (ARENA_WIDTH, ARENA_HEIGHT)), 2)

                # clear side/bottom areas
                pygame.draw.rect(self.screen, (0, 0, 0), ((0, ARENA_HEIGHT), (ARENA_WIDTH + BOT_INFO_X, AREA_INFERIOR)))
                pygame.draw.rect(self.screen, (0, 0, 0), ((ARENA_WIDTH, 0), (BOT_INFO_X, ARENA_HEIGHT)))

                for bot in self.bots:
                        pygame.draw.rect(self.screen, CORES[bot.index] if bot.active else (80, 80, 80), ((ARENA_WIDTH, bot.index * BOT_INFO_Y), (BOT_INFO_X, BOT_INFO_Y)), 1)
                        name = self.font2.render(bot.func.__name__, False, CORES[bot.index] if bot.active else (80, 80, 80))
                        self.screen.blit(name, (ARENA_WIDTH + 4, bot.index * BOT_INFO_Y + 2))
                        pygame.draw.rect(self.screen, (255, 100, 100) if bot.active else (80, 80, 80), ((ARENA_WIDTH + 4, bot.index * BOT_INFO_Y + 32), (bot.temperature / MAX_TEMPERATURE * (BOT_INFO_X - 8), 14)))
                        if bot.active:
                                phealth = bot.health / MAX_HEALTH
                                pygame.draw.rect(self.screen, (0, 255, 0) if phealth >= .666 else ((255, 255, 0) if phealth >= .333 else (255, 0, 0)), ((ARENA_WIDTH + 4, bot.index * BOT_INFO_Y + 16), (phealth * (BOT_INFO_X - 8), 14)))
                                pygame.draw.line(self.screen, (255, 0, 0), (ARENA_WIDTH + 4 + (DANGEROUS_TEMPERATURE / MAX_TEMPERATURE * (BOT_INFO_X - 8)), bot.index * BOT_INFO_Y + 32), (ARENA_WIDTH + 4 + (DANGEROUS_TEMPERATURE / MAX_TEMPERATURE * (BOT_INFO_X - 8)), bot.index * BOT_INFO_Y + 45))
                        s = self.score[bot.index]
                        sinfo = self.font2.render(f"{s['wins']} / {s['ties']} / {s['losses']}", False, CORES[bot.index] if bot.active else (80, 80, 80))
                        self.screen.blit(sinfo, (ARENA_WIDTH + 4, bot.index * BOT_INFO_Y + 48))

                # bottom bar text
                texto = self.font2.render('(Q)quit - show (N)ames - show (A)rcs - (S)ound - (ESC) next round - (P)ause - (J K) changes fps', False, (255, 255, 255))
                self.screen.blit(texto, (1, ARENA_HEIGHT + 6))
                texto = self.font2.render('match: ' + str(self.round + 1) + ' / ' + str(self.rounds) + '        time: ' + str(self.ticks) + ' / ' + str(MAX_TIME), False, (255, 255, 255))
                self.screen.blit(texto, (1, ARENA_HEIGHT + 26))
                for i, m in enumerate(self.msg):
                        texto = self.font2.render(m, False, (255 - (i * (255 / MAX_MSG)), 255 - (i * (255 / MAX_MSG)), 255 - (i * (255 / MAX_MSG))))
                        self.screen.blit(texto, (ARENA_WIDTH - texto.get_size()[0], ARENA_HEIGHT + 6 + i * 16))

                # draw smokes
                for f in self.smokes:
                        s = sin(f['life'])
                        pygame.draw.circle(self.screen, (int(f['col'][0] * s), int(f['col'][1] * s), int(f['col'][2] * s)), tuple(map(int, f['pos'])), int(f['rad'] + 4 - s * f['rad']), 4)

                # draw sparks
                for f in self.sparks:
                        s = sin(f['life'])
                        pygame.draw.line(self.screen, (s * 255, s * 200, 0), f['pos'], (f['pos'][0] + f['vel'][0], f['pos'][1] + f['vel'][1]), 1)

                # draw debris
                for f in self.debris:
                        s = sin(f['life'])
                        pygame.draw.line(self.screen, (f['col'][0] * s, f['col'][1] * s, f['col'][2] * s), f['pos'], (f['pos'][0] + f['vel'][0], f['pos'][1] + f['vel'][1]), 2)

                pygame.display.flip()

