import pyray as pr
import math

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.base_speed = 150
        self.sprint_speed = 250
        self.color = pr.BLUE
        self.has_artifact = False
        
        self.stamina = 100.0
        self.is_sprinting = False
        self.is_hidden = False
        self.keys_inventory = 0

    def update(self, dt):
        dx = 0
        dy = 0
        if pr.is_key_down(pr.KEY_W): dy -= 1
        if pr.is_key_down(pr.KEY_S): dy += 1
        if pr.is_key_down(pr.KEY_A): dx -= 1
        if pr.is_key_down(pr.KEY_D): dx += 1

        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length

        # Mechanika biegania (sprint) ograniczona staminą
        speed = self.base_speed
        self.is_sprinting = False
        
        if pr.is_key_down(pr.KEY_LEFT_SHIFT) and self.stamina > 0 and length > 0:
            speed = self.sprint_speed
            self.stamina -= 40 * dt
            self.is_sprinting = True
        else:
            self.stamina = min(100.0, self.stamina + 20 * dt)

        return dx * speed * dt, dy * speed * dt

    def draw(self):
        c = pr.fade(self.color, 0.4) if self.is_hidden else self.color
        pr.draw_circle(int(self.x), int(self.y), self.radius, c)
        
        if self.has_artifact:
            pr.draw_circle(int(self.x), int(self.y), 4, pr.YELLOW)
            
        if self.keys_inventory > 0:
            pr.draw_circle(int(self.x) + 12, int(self.y) - 12, 4, pr.SKYBLUE)
            
        # Rysowanie paska staminy, jeśli nie jest pełny
        if self.stamina < 100:
            pr.draw_rectangle(int(self.x) - 15, int(self.y) - 20, 30, 4, pr.RED)
            pr.draw_rectangle(int(self.x) - 15, int(self.y) - 20, int(30 * (self.stamina / 100.0)), 4, pr.GREEN)


class Rock:
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        self.tx = tx
        self.ty = ty
        self.speed = 300
        self.radius = 4
        self.active = True
        
        dx = tx - x
        dy = ty - y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.vx = (dx/dist) * self.speed
            self.vy = (dy/dist) * self.speed
        else:
            self.vx = 0
            self.vy = 0

    def update(self, dt):
        if not self.active: return
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Check if reached target approx
        dist = math.sqrt((self.tx - self.x)**2 + (self.ty - self.y)**2)
        if dist < 10:
            self.active = False

    def draw(self):
        if self.active:
            pr.draw_circle(int(self.x), int(self.y), self.radius, pr.GRAY)


class Guard:
    STATE_PATROL = 0
    STATE_SUSPICIOUS = 1
    STATE_CHASE = 2
    STATE_RETURN = 3

    def __init__(self, path_points):
        self.path = path_points
        self.path_idx = 0
        self.x = self.path[0][0]
        self.y = self.path[0][1]
        self.radius = 12
        self.speed = 70
        self.chase_speed = 110
        self.state = self.STATE_PATROL
        self.vision_range = 150
        
        self.dir_x = 1.0
        self.dir_y = 0.0
        
        # For suspicious state
        self.suspicious_timer = 0
        self.target_x = 0
        self.target_y = 0

    def update(self, dt, player, rocks, wall_col_func):
        # Maszyna stanów (FSM) dla sztucznej inteligencji strażnika
        if self.state == self.STATE_PATROL:
            self._move_towards(self.path[self.path_idx][0], self.path[self.path_idx][1], self.speed, dt, wall_col_func)
            if self._distance_to(self.path[self.path_idx][0], self.path[self.path_idx][1]) < 15:
                self.path_idx = (self.path_idx + 1) % len(self.path)
            
            # Sprawdzenie czy gracz znajduje się w polu widzenia (FOV)
            if self._can_see(player):
                self.state = self.STATE_CHASE
            
            # Sprawdzenie czy gracz biegnie (hałas w promieniu)
            if player.is_sprinting and self._distance_to(player.x, player.y) < 200:
                self._become_suspicious(player.x, player.y)
            
            # Sprawdzenie czy strażnik usłyszał rzucony kamień
            for rock in rocks:
                if not rock.active and self._distance_to(rock.x, rock.y) < 200:
                    self._become_suspicious(rock.x, rock.y)

        elif self.state == self.STATE_SUSPICIOUS:
            self._move_towards(self.target_x, self.target_y, self.speed, dt, wall_col_func)
            self.suspicious_timer -= dt
            if self.suspicious_timer <= 0:
                self.state = self.STATE_RETURN
            if self._can_see(player):
                self.state = self.STATE_CHASE

        elif self.state == self.STATE_CHASE:
            self._move_towards(player.x, player.y, self.chase_speed, dt, wall_col_func)
            if not self._can_see(player):
                self._become_suspicious(player.x, player.y)

        elif self.state == self.STATE_RETURN:
            # Powrót do najbliższego punktu patrolowego
            closest_idx = 0
            min_dist = 9999
            for i, p in enumerate(self.path):
                d = self._distance_to(p[0], p[1])
                if d < min_dist:
                    min_dist = d
                    closest_idx = i
            
            self._move_towards(self.path[closest_idx][0], self.path[closest_idx][1], self.speed, dt, wall_col_func)
            if self._distance_to(self.path[closest_idx][0], self.path[closest_idx][1]) < 15:
                self.path_idx = closest_idx
                self.state = self.STATE_PATROL
            
            if self._can_see(player):
                self.state = self.STATE_CHASE

    def _become_suspicious(self, tx, ty):
        self.state = self.STATE_SUSPICIOUS
        self.target_x = tx
        self.target_y = ty
        self.suspicious_timer = 3.0
        # Natychmiastowe odwrócenie się w stronę źródła dźwięku
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.dir_x = dx / dist
            self.dir_y = dy / dist

    def _move_towards(self, tx, ty, speed, dt, wall_col_func):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            # Aktualizacja kierunku patrzenia strażnika
            self.dir_x = dx / dist
            self.dir_y = dy / dist
            
            mx = self.dir_x * speed * dt
            my = self.dir_y * speed * dt
            
            self.x += mx
            if wall_col_func(self.x, self.y, self.radius):
                self.x -= mx
                
            self.y += my
            if wall_col_func(self.x, self.y, self.radius):
                self.y -= my

    def _distance_to(self, tx, ty):
        return math.sqrt((tx - self.x)**2 + (ty - self.y)**2)

    def _can_see(self, player):
        if player.is_hidden:
            return False
            
        dist = self._distance_to(player.x, player.y)
        if dist > self.vision_range:
            return False
            
        # Sprawdzenie Pola Widzenia (FOV 120 stopni)
        vx = (player.x - self.x) / dist
        vy = (player.y - self.y) / dist
        dot = self.dir_x * vx + self.dir_y * vy
        
        # cos(60 degrees) = 0.5
        return dot >= 0.5

    def draw(self):
        color = pr.RED
        if self.state == self.STATE_SUSPICIOUS: color = pr.ORANGE
        if self.state == self.STATE_RETURN: color = pr.MAROON
        
        pr.draw_circle(int(self.x), int(self.y), self.radius, color)
        
        # Rysowanie stożka widzenia strażnika
        if self.state == self.STATE_PATROL or self.state == self.STATE_RETURN or self.state == self.STATE_CHASE or self.state == self.STATE_SUSPICIOUS:
            cone_color = pr.RED if self.state == self.STATE_CHASE else pr.fade(pr.RED, 0.3)
            # Calculate left and right lines of the cone
            angle = math.atan2(self.dir_y, self.dir_x)
            left_angle = angle - math.radians(60)
            right_angle = angle + math.radians(60)
            
            lx = self.x + math.cos(left_angle) * self.vision_range
            ly = self.y + math.sin(left_angle) * self.vision_range
            rx = self.x + math.cos(right_angle) * self.vision_range
            ry = self.y + math.sin(right_angle) * self.vision_range
            
            pr.draw_line(int(self.x), int(self.y), int(lx), int(ly), cone_color)
            pr.draw_line(int(self.x), int(self.y), int(rx), int(ry), cone_color)
            pr.draw_line(int(lx), int(ly), int(rx), int(ry), pr.fade(cone_color, 0.2))


class Camera:
    def __init__(self, x, y, start_angle, sweep_range, speed):
        self.x = x
        self.y = y
        self.base_angle = start_angle
        self.sweep_range = sweep_range
        self.speed = speed
        self.current_offset = 0
        self.direction = 1
        self.vision_range = 200

    def update(self, dt):
        self.current_offset += self.direction * self.speed * dt
        if self.current_offset > self.sweep_range:
            self.current_offset = self.sweep_range
            self.direction = -1
        elif self.current_offset < -self.sweep_range:
            self.current_offset = -self.sweep_range
            self.direction = 1

    def can_see(self, player):
        if player.is_hidden:
            return False
            
        dist = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        if dist > self.vision_range:
            return False
            
        current_angle = math.radians(self.base_angle + self.current_offset)
        dir_x = math.cos(current_angle)
        dir_y = math.sin(current_angle)
        
        vx = (player.x - self.x) / dist
        vy = (player.y - self.y) / dist
        dot = dir_x * vx + dir_y * vy
        
        # Camera has narrower 60 degree FOV (30 each side, cos(30) ~ 0.866)
        return dot >= 0.866

    def draw(self):
        pr.draw_circle(int(self.x), int(self.y), 8, pr.DARKGRAY)
        
        current_angle = math.radians(self.base_angle + self.current_offset)
        dir_x = math.cos(current_angle)
        dir_y = math.sin(current_angle)
        
        left_angle = current_angle - math.radians(30)
        right_angle = current_angle + math.radians(30)
        
        lx = self.x + math.cos(left_angle) * self.vision_range
        ly = self.y + math.sin(left_angle) * self.vision_range
        rx = self.x + math.cos(right_angle) * self.vision_range
        ry = self.y + math.sin(right_angle) * self.vision_range
        
        pr.draw_line(int(self.x), int(self.y), int(lx), int(ly), pr.fade(pr.RED, 0.4))
        pr.draw_line(int(self.x), int(self.y), int(rx), int(ry), pr.fade(pr.RED, 0.4))
        pr.draw_line(int(lx), int(ly), int(rx), int(ry), pr.fade(pr.RED, 0.2))

