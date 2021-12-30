import pygame
import math

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

player_pos = (half_width, half_height)
player_angle = 0
player_speed = 5

texture_width = 1500
texture_height = 1000
texture_scale = texture_width // tile

with open('map.txt', 'r', encoding='utf-8') as map:
    text_map = map.readlines()

world_map = set()
for j, row in enumerate(text_map):
    for i, char in enumerate(row):
        if char == '1':
            world_map.add((i * tile, j * tile))


def mapping(a, b):
    return (a // tile) * tile, (b // tile) * tile


def ray_casting(player, texture):
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


class Driwing:
    def __init__(self, screen, screen_map):
        self.screen = screen
        self.screen_map = screen_map
        self.texture = pygame.image.load('textures/wood.jpg').convert()

    def world(self, world_objects):
        for obj in sorted(world_objects, key=lambda n: n[0], reverse=True):
            if obj[0]:
                _, objectt, object_pos = obj
                self.screen.blit(objectt, object_pos)


class Player:
    def __init__(self):
        self.x, self.y = player_pos
        self.angle = player_angle

    @property
    def pos(self):
        return (self.x, self.y)

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.x += player_speed * cos_a
            self.y += player_speed * sin_a
        if keys[pygame.K_s]:
            self.x += -player_speed * cos_a
            self.y += -player_speed * sin_a
        if keys[pygame.K_a]:
            self.x += player_speed * sin_a
            self.y += -player_speed * cos_a
        if keys[pygame.K_d]:
            self.x += -player_speed * sin_a
            self.y += player_speed * cos_a
        if keys[pygame.K_LEFT]:
            self.angle -= 0.02
        if keys[pygame.K_RIGHT]:
            self.angle += 0.02

        self.angle %= math.pi * 2


class World_Object:
    def __init__(self, object, static, pos, shift, scale):
        self.object = object
        self.static = static
        self.pos = self.x, self.y = pos[0] * tile, pos[1] * tile
        self.shift = shift
        self.scale = scale

    def locate(self, player, walls):
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
            sprite_pos = (current_ray * scale - proj_height // 2, half_height - proj_height // 2 + shift)
            sprite = pygame.transform.scale(self.object, (proj_height, proj_height))
            return (distance, sprite, sprite_pos)
        else:
            return (False,)


class Sprites:
    def __init__(self):
        self.types = {
            'stas': pygame.image.load('sprites/pes.png').convert_alpha()
        }
        self.objects = [
            World_Object(self.types['stas'], True, (7.1, 3.1), -0.5, 0.1)
        ]


pygame.init()
screen = pygame.display.set_mode(size)
sprites = Sprites()
clock = pygame.time.Clock()
player = Player()
driwing = Driwing(screen, world_map)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
    player.movement()
    screen.fill((0, 0, 0))

    pygame.draw.rect(screen, (192, 192, 192), (0, 0, width, half_height))
    pygame.draw.rect(screen, (0, 0, 0), (0, half_height, width, half_height))
    walls = ray_casting(player, driwing.texture)
    driwing.world(walls + [obj.locate(player, walls) for obj in sprites.objects])

    pygame.display.flip()
    clock.tick(fps)
