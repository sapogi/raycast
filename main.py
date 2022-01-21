import pygame
import math
import pygame_menu
from collections import deque

# Глобальные переменные константы
size = width, height = 1200, 800
half_width = width // 2
half_height = height // 2
fps = 60
tile = 100

fov = math.pi / 3
half_fov = fov / 2
num_rays = 300
max_depth = 80
delta_angle = fov / num_rays
dist = num_rays / (2 * math.tan(half_fov))
proj_coeff = 3 * dist * tile
scale = width // num_rays

player_pos = (1750, 10)
player_angle = 0
player_speed = 5

texture_width = 1500
texture_height = 1000
texture_scale = texture_width // tile

with open('map.txt', 'r', encoding='utf-8') as map:
    text_map = map.readlines()

# Помещение карты в множество и создание карты коллизий
world_map = set()
collision_walls = []
for j, row in enumerate(text_map):
    for i, char in enumerate(row):
        if char == '1':
            world_map.add((i * tile, j * tile))
            collision_walls.append(pygame.Rect(i * tile, j * tile, tile, tile))


def mapping(a, b):
    return (a // tile) * tile, (b // tile) * tile


def ray_casting(player,
                texture):  # Функция которая возращает список со стенами в нужном формате для их отображения относительно текущей позиции
    # и напровления игрока
    walls = []
    ox, oy = player.pos
    xm, ym = mapping(ox, oy)
    cur_angle = player.angle - half_fov
    for ray in range(num_rays):
        sin_a = math.sin(cur_angle)
        cos_a = math.cos(cur_angle)
        sin_a = sin_a if sin_a else 0.000001
        cos_a = cos_a if cos_a else 0.000001

        x, dx = (xm + tile, 1) if cos_a >= 0 else (xm, -1)
        for i in range(0, width, tile):
            depth_v = (x - ox) / cos_a
            yv = oy + depth_v * sin_a
            if mapping(x + dx, yv) in world_map:
                break
            x += dx * tile

        y, dy = (ym + tile, 1) if sin_a >= 0 else (ym, -1)
        for i in range(0, height, tile):
            depth_h = (y - oy) / sin_a
            xh = ox + depth_h * cos_a
            if mapping(xh, y + dy) in world_map:
                break
            y += dy * tile

        depth, offset, texture = (depth_v, yv, texture) if depth_v < depth_h else (depth_h, xh, texture)
        offset = int(offset) % tile
        depth *= math.cos(player.angle - cur_angle)
        depth = max(depth, 0.00001)
        proj_height = min(int(proj_coeff / depth), 2 * height)

        wall_column = texture.subsurface(offset * texture_scale, 0, texture_scale, texture_height)
        wall_column = pygame.transform.scale(wall_column, (scale, proj_height))
        wall_pos = (ray * scale, half_height - proj_height // 2)

        walls.append((depth, wall_column, wall_pos))
        cur_angle += delta_angle
    return walls


class Driwing:  # функция для отрисовки всех объектов на крате
    def __init__(self, screen, screen_map):
        self.screen = screen
        self.screen_map = screen_map
        self.texture = pygame.image.load('textures/wood.jpg').convert()

    def world(self, world_objects):
        for obj in sorted(world_objects, key=lambda n: n[0], reverse=True):
            if obj[0]:
                _, temp_object, object_pos = obj
                self.screen.blit(temp_object, object_pos)


class Player:  # Класс игрока
    def __init__(self):
        self.x, self.y = player_pos
        self.angle = player_angle
        self.sensitivity = 0.004
        self.side = 50
        self.rect = pygame.Rect(*player_pos, self.side, self.side)

    @property
    def pos(self):
        return (self.x, self.y)

    #
    def detect_collision(self, dx, dy):  # Метод для обнаружения столкновения игрока со стенами
        next_rect = self.rect.copy()
        next_rect.move_ip(dx, dy)
        hit_indexes = next_rect.collidelistall(collision_walls)

        if len(hit_indexes):
            delta_x, delta_y = 0, 0
            for hit_index in hit_indexes:
                hit_rect = collision_walls[hit_index]
                if dx > 0:
                    delta_x += next_rect.right - hit_rect.left
                else:
                    delta_x += hit_rect.right - next_rect.left
                if dy > 0:
                    delta_y += next_rect.bottom - hit_rect.top
                else:
                    delta_y += hit_rect.bottom - next_rect.top
            if abs(delta_x - delta_y) < 10:
                dx, dy = 0, 0
            elif delta_x > delta_y:
                dy = 0
            elif delta_y > delta_x:
                dx = 0
        self.x += dx
        self.y += dy

    def movement(self):  # Метод для общего перемещения игрока
        self.keys_control()
        self.mouse_control()
        self.rect.center = self.x, self.y
        self.angle %= math.pi * 2

    def keys_control(self):  # метод для движения
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            exit()

        if keys[pygame.K_w]:
            dx = player_speed * cos_a
            dy = player_speed * sin_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_s]:
            dx = -player_speed * cos_a
            dy = -player_speed * sin_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_a]:
            dx = player_speed * sin_a
            dy = -player_speed * cos_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_d]:
            dx = -player_speed * sin_a
            dy = player_speed * cos_a
            self.detect_collision(dx, dy)
        if keys[pygame.K_LEFT]:
            self.angle -= 0.02
        if keys[pygame.K_RIGHT]:
            self.angle += 0.02

    def mouse_control(self):  # Метод для поворота мыши
        if pygame.mouse.get_focused():
            difference = pygame.mouse.get_pos()[0] - half_width
            pygame.mouse.set_pos((half_width, half_height))
            self.angle += difference * self.sensitivity


class World_Object:  # Класс для объектов внутри игры отображаемых ввиде спрайтов
    def __init__(self, parameters, pos):
        self.object = parameters['sprite']
        self.viewing_angles = parameters['viewing_angles']
        self.shift = parameters['shift']
        self.scale = parameters['scale']
        self.animation = parameters['animation'].copy()
        self.animation_dist = parameters['animation_dist']
        self.animation_speed = parameters['animation_speed']
        self.animation_count = 0
        self.pos = self.x, self.y = pos[0] * tile, pos[1] * tile
        if self.viewing_angles:
            self.sprite_angles = [frozenset(range(i, i + 45)) for i in range(0, 360, 45)]
            self.sprite_positions = {angle: pos for angle, pos in zip(self.sprite_angles, self.object)}

    def locate(self, player, walls):  # метод для обнаружения этих объектов на карте
        dx, dy = self.x - player.x, self.y - player.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        theta = math.atan2(dy, dx)
        gamma = theta - player.angle
        if dx > 0 and 180 <= math.degrees(player.angle) <= 360 or dx < 0 and dy < 0:
            gamma += math.pi * 2

        delta_rays = int(gamma / delta_angle)
        current_ray = num_rays // 2 - 1 + delta_rays
        distance *= math.cos(half_fov - current_ray * delta_angle)

        if 0 <= current_ray <= num_rays - 1 and distance < walls[current_ray][0]:
            proj_height = int(proj_coeff / distance * scale)
            shift = (proj_height // 2) * self.shift
            sprite_object = self.object
            if self.animation and distance < self.animation_dist:
                sprite_object = self.animation[0]
                if self.animation_count < self.animation_speed:
                    self.animation_count += 1
                else:
                    self.animation.rotate()
                    self.animation_count = 0
            sprite_pos = (current_ray * scale - proj_height // 2, half_height - proj_height // 2 + shift)
            sprite = pygame.transform.scale(sprite_object, (proj_height, proj_height))
            return (distance, sprite, sprite_pos)
        else:
            return (False,)


class Sprites:  # Класс для хранения всех объектов World_Object
    def __init__(self):
        self.sprite_parameters = {
            'mob': {
                'sprite': pygame.image.load('sprites/mob/base/0.png').convert_alpha(),
                'viewing_angles': None,
                'shift': -0.7,
                'scale': 0.4,
                'animation': deque(
                    [pygame.image.load(f'sprites/mob/death/{i}.png').convert_alpha() for i in range(4)]),
                'animation_dist': 800,
                'animation_speed': 10,
            }}
        self.objects = [
            World_Object(self.sprite_parameters['mob'], (10.5, 30.5))
        ]


def start_game():  # Функция с главным игровым циклом
    sprites = Sprites()
    clock = pygame.time.Clock()
    player = Player()
    driwing = Driwing(screen, world_map)
    pygame.mouse.set_visible(False)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        player.movement()
        if 1000 < player.x < 1100 and 2700 < player.y < 2800:
            break
        screen.fill((0, 0, 0))

        pygame.draw.rect(screen, (192, 192, 192), (0, 0, width, half_height))
        pygame.draw.rect(screen, (0, 0, 0), (0, half_height, width, half_height))
        walls = ray_casting(player, driwing.texture)
        driwing.world(walls + [obj.locate(player, walls) for obj in sprites.objects])

        pygame.display.flip()
        clock.tick(fps)


# создание начального меню
pygame.init()
screen = pygame.display.set_mode(size)
menu = pygame_menu.Menu('start menu', 400, 300, theme=pygame_menu.themes.THEME_GREEN)
menu.add.button('Play', start_game)
menu.add.button('Quit', pygame_menu.events.EXIT)
menu.mainloop(screen)
