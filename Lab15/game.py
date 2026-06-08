import pyray as pr
from entities import Player, Guard, Rock, Camera
import math

class Game:
    def __init__(self, difficulty="NORMAL"):
        self.walls = [
            pr.Rectangle(0, 0, 800, 20),
            pr.Rectangle(0, 580, 800, 20),
            pr.Rectangle(0, 0, 20, 600),
            pr.Rectangle(780, 0, 20, 600),
            
            # Mały zamknięty pokój w prawym górnym rogu dla wyjścia (EXIT)
            pr.Rectangle(600, 20, 20, 150),
            pr.Rectangle(600, 170, 80, 20)
        ]
        
        self.doors = [
            pr.Rectangle(680, 170, 100, 20) # Blokuje dół pokoju wyjściowego (drzwi)
        ]
        
        self.hiding_spots = []
        if difficulty != "HARD":
            self.hiding_spots.append(pr.Rectangle(350, 250, 100, 100)) # Duża kryjówka na środku mapy
        
        self.keys = [
            pr.Rectangle(100, 500, 20, 20)
        ]
        
        self.cameras = [
            Camera(400, 20, 90, 60, 40) # Środek u góry, skierowana w dół (kamera)
        ]
        
        self.artifacts = [pr.Rectangle(400, 450, 30, 30)]
        if difficulty in ["NORMAL", "HARD"]:
            self.artifacts.append(pr.Rectangle(650, 400, 30, 30))
            self.artifacts.append(pr.Rectangle(200, 150, 30, 30))
            
        self.exit_rect = pr.Rectangle(700, 50, 60, 60)
        
        self.player = Player(100, 100)
        
        self.guards = [
            Guard([(150, 150), (150, 450), (550, 450), (550, 150)]), # Patroluje po dużym kwadracie
        ]
        
        if difficulty == "HARD":
            self.guards.append(Guard([(400, 350), (400, 50)]))
            self.guards.append(Guard([(250, 250), (550, 250)]))
        
        for g in self.guards:
            if difficulty == "EASY":
                g.speed = 50
                g.chase_speed = 80
                g.vision_range = 100
            elif difficulty == "HARD":
                g.speed = 95
                g.chase_speed = 140
                g.vision_range = 220
        
        self.rocks = []
        
        self.state = "PLAYING" # PLAYING, WIN, LOSS
        
        # Audio
        pr.init_audio_device()
        self.snd_distract = pr.load_sound("distract.wav")
        self.snd_caught = pr.load_sound("caught.wav")
        self.snd_win = pr.load_sound("win.wav")

    def __del__(self):
        pr.unload_sound(self.snd_distract)
        pr.unload_sound(self.snd_caught)
        pr.unload_sound(self.snd_win)
        pr.close_audio_device()

    def trigger_alarm(self):
        if self.state == "PLAYING":
            pr.play_sound(self.snd_caught)
            for g in self.guards:
                g._become_suspicious(self.player.x, self.player.y)
                g.state = Guard.STATE_CHASE

    def update(self, dt):
        if self.state != "PLAYING": return

        # Obsługa ruchu gracza
        dx, dy = self.player.update(dt)
        
        # Sprawdzanie odblokowania drzwi (jeśli gracz ma klucz)
        for i in range(len(self.doors) - 1, -1, -1):
            if pr.check_collision_circle_rec(pr.Vector2(self.player.x, self.player.y), self.player.radius + 5, self.doors[i]):
                if self.player.keys_inventory > 0:
                    self.doors.pop(i)
                    self.player.keys_inventory -= 1
        
        # Obsługa kolizji w osi X
        self.player.x += dx
        if self._check_wall_collision(self.player.x, self.player.y, self.player.radius):
            self.player.x -= dx
            
        # Obsługa kolizji w osi Y
        self.player.y += dy
        if self._check_wall_collision(self.player.x, self.player.y, self.player.radius):
            self.player.y -= dy

        # Sprawdzanie czy gracz znajduje się w kryjówce
        self.player.is_hidden = False
        for hs in self.hiding_spots:
            if pr.check_collision_circle_rec(pr.Vector2(self.player.x, self.player.y), self.player.radius, hs):
                self.player.is_hidden = True
                break

        # Check Keys
        for i in range(len(self.keys) - 1, -1, -1):
            if pr.check_collision_circle_rec(pr.Vector2(self.player.x, self.player.y), self.player.radius, self.keys[i]):
                self.keys.pop(i)
                self.player.keys_inventory += 1

        # Mechanika rzutu kamieniem (dźwięk odwracający uwagę)
        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_RIGHT):
            mx = pr.get_mouse_x()
            my = pr.get_mouse_y()
            self.rocks.append(Rock(self.player.x, self.player.y, mx, my))
            pr.play_sound(self.snd_distract)

        # Update Rocks
        for r in self.rocks:
            r.update(dt)

        # Update Cameras
        for c in self.cameras:
            c.update(dt)
            if c.can_see(self.player):
                self.trigger_alarm()

        # Aktualizacja stanu i pozycji strażników (wykorzystanie maszyny stanów FSM)
        for g in self.guards:
            g.update(dt, self.player, self.rocks, self._check_wall_collision)
            
            # Guard Caught Player Check
            if g.state == Guard.STATE_CHASE and g._distance_to(self.player.x, self.player.y) < (g.radius + self.player.radius):
                self.state = "LOSS"
                pr.play_sound(self.snd_caught)

        # Podnoszenie artefaktów
        for i in range(len(self.artifacts) - 1, -1, -1):
            if pr.check_collision_circle_rec(pr.Vector2(self.player.x, self.player.y), self.player.radius, self.artifacts[i]):
                self.artifacts.pop(i)
                
        self.player.has_artifact = len(self.artifacts) == 0

        # Warunek wygranej
        if self.player.has_artifact:
            if pr.check_collision_circle_rec(pr.Vector2(self.player.x, self.player.y), self.player.radius, self.exit_rect):
                self.state = "WIN"
                pr.play_sound(self.snd_win)

    def _check_wall_collision(self, x, y, radius):
        for w in self.walls:
            if pr.check_collision_circle_rec(pr.Vector2(x, y), radius, w):
                return True
                
        # Check Doors
        for d in self.doors:
            if pr.check_collision_circle_rec(pr.Vector2(x, y), radius, d):
                return True
                
        return False

    def draw(self):
        pr.clear_background(pr.RAYWHITE)
        
        # Draw Hiding Spots
        for hs in self.hiding_spots:
            pr.draw_rectangle_rec(hs, pr.DARKBLUE)
            
        # Draw Exit
        pr.draw_rectangle_rec(self.exit_rect, pr.GREEN if self.player.has_artifact else pr.DARKGREEN)
        pr.draw_text("EXIT", int(self.exit_rect.x + 10), int(self.exit_rect.y + 20), 20, pr.WHITE)

        # Draw Artifacts
        for art in self.artifacts:
            pr.draw_rectangle_rec(art, pr.GOLD)
            pr.draw_text("ART", int(art.x), int(art.y + 10), 10, pr.BLACK)

        # Draw Keys
        for k in self.keys:
            pr.draw_rectangle_rec(k, pr.SKYBLUE)
            pr.draw_text("KEY", int(k.x), int(k.y - 10), 10, pr.BLACK)

        # Draw Walls & Doors
        for w in self.walls:
            pr.draw_rectangle_rec(w, pr.DARKGRAY)
        for d in self.doors:
            pr.draw_rectangle_rec(d, pr.BROWN)
            pr.draw_text("LOCK", int(d.x - 5), int(d.y + 40), 10, pr.WHITE)
            
        # Draw Rocks
        for r in self.rocks:
            r.draw()
            
        # Draw Cameras
        for c in self.cameras:
            c.draw()
            
        # Draw Guards
        for g in self.guards:
            g.draw()
            
        # Draw Player
        self.player.draw()
