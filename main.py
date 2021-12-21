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
player_speed = 2

text_map = [
    '111111111111',
    '1..........1',
    '1..........1',
    '1..........1',
    '1..111.111.1',
    '1..........1',
    '1..........1',
    '111111111111'
]

world_map = set()
for j, row in enumerate(text_map):
    for i, char in enumerate(row):
        if char == '1':
            world_map.add((i * tile, j * tile))


def mapping(a, b):
    return (a // tile) * tile, (b // tile) * tile


def ray_casting(screen, player_pos, player_angle):
    ox, oy = player_pos
    xm, ym = mapping(ox, oy)
    cur_angle = player_angle - half_fov
    for ray in range(num_rays):
        sin_a = math.sin(cur_angle)
        cos_a = math.cos(cur_angle)
        sin_a = sin_a if sin_a else 0.000001
        cos_a = cos_a if cos_a else 0.000001

        x, dx = (xm + tile, 1) if cos_a >= 0 else (xm, -1)
        for i in range(0, width, tile):
            depth_v = (x - ox) / cos_a
            y = oy + depth_v * sin_a
            if mapping(x + dx, y) in world_map:
                break
            x += dx * tile

        y, dy = (ym + tile, 1) if sin_a >= 0 else (ym, -1)
        for i in range(0, height, tile):
            depth_h = (y - oy) / sin_a
            x = ox + depth_h * cos_a
            if mapping(x, y + dy) in world_map:
                break
            y += dy * tile

        depth = depth_v if depth_v < depth_h else depth_h
        depth *= math.cos(player_angle - cur_angle)
        proj_height = proj_coeff / depth
        color = (255, 255, 255)
        pygame.draw.rect(screen, color, (ray * scale, half_height - proj_height // 2, scale, proj_height))
        cur_angle += delta_angle


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


pygame.init()
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
player = Player()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
    player.movement()
    screen.fill((0, 0, 0))

    pygame.draw.rect(screen, (0, 0, 0), (0, 0, width, half_height))
    pygame.draw.rect(screen, (0, 0, 0), (0, half_height, width, half_height))

    ray_casting(screen, player.pos, player.angle)

    pygame.display.flip()
    clock.tick(fps)
