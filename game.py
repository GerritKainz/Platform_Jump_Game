import pygame, sys, keyboard, json, random
from time import sleep, time
from pygame import Rect, Vector2
from pygame.font import Font
from pygame.mixer import Sound

with open('game_data.json', 'r') as file: data = json.load(file)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, currentplayer):
        super().__init__()
        self.image =pygame.image.load(f'pictures/player/{currentplayer}/jump.png')
        self.rect = self.image.get_rect(midbottom = pos)
        self.xspeed = 0
        self.last_xspeed = 0
        self.yspeed = 0
        self.gravity = 0.8
        self.jump = False
        self.dead = False
        
    def update_pictures(self, paths_dict):
        self.big        = pygame.image.load(paths_dict["big"])
        self.running1_r = pygame.image.load(paths_dict["running1"])
        self.running2_r = pygame.image.load(paths_dict["running2"])
        self.jump_r     = pygame.image.load(paths_dict["jump"])
        self.dead_r     = pygame.image.load(paths_dict["dead"])
        self.running1_l = pygame.transform.flip(self.running1_r, True, False)
        self.running2_l = pygame.transform.flip(self.running2_r, True, False)
        self.jump_l     = pygame.transform.flip(self.jump_r    , True, False)
        self.dead_l     = pygame.transform.flip(self.jump_r    , True, False)
        self.running1_r .set_colorkey((255, 255, 255))
        self.running2_r .set_colorkey((255, 255, 255))
        self.jump_r     .set_colorkey((255, 255, 255))
        self.running1_l .set_colorkey((255, 255, 255))
        self.running2_l .set_colorkey((255, 255, 255))
        self.jump_l     .set_colorkey((255, 255, 255))

class Platform(pygame.sprite.Sprite):
    def __init__(self, img, pos, type = 'normal'):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect(midbottom = pos)
        self.type = type
        self.speed = 0

    def update(self): #only gets called for the falling ones
        self.speed += 0.3
        self.rect.y += self.speed
        if self.rect.y > 10000: self.kill()

class Coin(pygame.sprite.Sprite):
    def __init__(self, img, pos):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect(center = pos)

class Fragment(pygame.sprite.Sprite):
    def __init__(self, pos, color):
        super().__init__()
        self.size = 7
        self.image = pygame.surface.Surface((self.size, self.size))
        self.color = color
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center = pos)
        self.speed = random.randint(2, 5)
        self.dir = Vector2(1, 0).rotate(random.randint(0, 360))

    def update(self):
        self.rect.center += self.speed * self.dir
        self.size *= 0.97
        self.image = pygame.surface.Surface((self.size, self.size))
        self.image.fill(self.color)
        if self.size < 1: self.kill()

class Game():
    def __init__(self):
        # variables
        self.fps = data["framerate"]
        self.frame = 0
        self.state = 'menu'
        if data["darkmode"] == 'dark': 
            self.background_color = (50, 50, 50)
            self.textcolor = (250, 250, 250)
        else:             
            self.background_color = (250, 250, 250)
            self.textcolor = (50, 50, 50)
        self.platform_width = 96
        self.platform_height = 32
        self.ground_height = 650
        self.score = 0
        self.key_moveleft    = data["left_key"]
        self.key_moveright   = data["right_key"]
        self.key_jump        = data["jump_key"]
        self.key_duck        = data["duck_key"]
        self.current_level   = data["currentlevel"]
        self.highscore       = data["highscores"][self.current_level]
        self.current_player  = data["currentplayer"]
        self.surviving_speed = data["playerstats"]["survivingspeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]
        self.jump_speed      = data["playerstats"]["jumpspeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]
        self.duck_speed      = data["playerstats"]["duckspeed"][self.current_player]
        self.move_speed      = data["playerstats"]["movespeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]
        self.coins           = data["coins"]
        self.coinspropability = data["levelstats"]["coinspropability"][self.current_level]
        self.height_difference = data["levelstats"]["heightdifference"][self.current_level]
        self.difficulty_increase = data["levelstats"]["difficultyincrease"][self.current_level]
        self.player = Player((screen_width / 2, self.ground_height), self.current_player)
        self.load_images()
        self.player.update_pictures(data["playerimgpaths"][self.current_player])
        self.changeplayer = False
        self.changelevel = False
        self.highscore_broken = False
        self.end_animation = True
        self.start_frame = 0
        # sound
        self.volume_effects = data["volume_effects"]
        self.volume_music = data["volume_music"]
        self.death_sound = Sound('sounds/smashsound.mp3')
        self.error_sound = Sound('sounds/error.mp3')
        self.kaching_sound = Sound('sounds/ka-ching.mp3')
        self.jump_sound = Sound('sounds/jump_sound.mp3')
        self.background_music_level = Sound('sounds/Music1.mp3')
        self.background_music_start = Sound('sounds/Music2.mp3')
        self.highscore_sound = Sound('sounds/highscore.mp3')
        self.death_sound.set_volume(self.volume_effects)
        self.error_sound.set_volume(self.volume_effects)
        self.kaching_sound.set_volume(self.volume_effects)
        self.jump_sound.set_volume(self.volume_effects)
        self.highscore_sound.set_volume(self.volume_effects)
        self.background_music_start.set_volume(self.volume_music)
        self.background_music_level.set_volume(self.volume_music)
        # keys
        self.jump_key_text           = font_30.render(f'Jump Key: {self.key_jump}',      True, self.textcolor)
        self.left_key_text           = font_30.render(f'Left Key: {self.key_moveleft}',  True, self.textcolor)
        self.right_key_text          = font_30.render(f'Right Key:{self.key_moveright}', True, self.textcolor)
        self.duck_key_text           = font_30.render(f'Duck Key: {self.key_duck}',      True, self.textcolor)
        self.jump_key_text_rect      = self.jump_key_text.get_rect(topleft = (10, screen_height * 0.10))
        self.left_key_text_rect      = self.left_key_text.get_rect(topleft = (10, screen_height * 0.15))
        self.right_key_text_rect     = self.right_key_text.get_rect(topleft= (10, screen_height * 0.20))
        self.duck_key_text_rect      = self.duck_key_text.get_rect(topleft = (10, screen_height * 0.25))
        # sprites
        self.platform_images = [pygame.image.load(path) for path in data["platformimgpaths"]]
        self.ground_surf = pygame.transform.scale(pygame.image.load(data["platformimgpaths"][data["platformtypes"][self.current_level][0]["imageindex"]]), (screen_width, self.platform_height/self.platform_width*screen_width))
        self.ground_sprite = Platform(self.ground_surf, (screen_width / 2, screen_height))
        self.platform_group = pygame.sprite.Group(self.ground_sprite)
        self.fallingplatforms = pygame.sprite.Group()
        self.explodingplatforms = pygame.sprite.Group()
        self.coin_group = pygame.sprite.Group()
        # images
        self.coin_img            = pygame.transform.scale(pygame.image.load('pictures/coin_1.png'), (25, 25))
        if data["darkmode"] == "dark":
            self.pause_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/pause_button_light.png'), (40, 40))
            self.exit_button_img     = pygame.transform.scale(pygame.image.load('pictures/menu/exit_button_light.png'), (35, 35))
            self.start_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_light.png'), (60, 50))
            self.arrow_button_right  = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_light.png'), (20, 50))
            self.arrow_button_left   = pygame.transform.flip(self.arrow_button_right, True, False)
            self.settings_back_arrow = pygame.transform.scale(self.arrow_button_left, (50, 40))
            self.pause_button_img.set_colorkey((50, 50, 50))
            self.exit_button_img.set_colorkey((50, 50, 50))
            self.start_button_img.set_colorkey((50, 50, 50))
            self.arrow_button_left.set_colorkey((50, 50, 50))
            self.arrow_button_right.set_colorkey((50, 50, 50))
        else:
            self.pause_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/pause_button_dark.png'), (40, 40))
            self.exit_button_img     = pygame.transform.scale(pygame.image.load('pictures/menu/exit_button_dark.png'), (35, 35))
            self.start_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_dark.png'), (60, 50))
            self.arrow_button_right  = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_dark.png'), (20, 50))
            self.arrow_button_left   = pygame.transform.flip(self.arrow_button_right, True, False)
            self.settings_back_arrow = pygame.transform.scale(self.arrow_button_left, (50, 40))
            self.pause_button_img.set_colorkey(((250, 250, 250)))
            self.exit_button_img.set_colorkey((250, 250, 250))
            self.start_button_img.set_colorkey((250, 250, 250))
            self.arrow_button_left.set_colorkey((250, 250, 250))
            self.arrow_button_right.set_colorkey((250, 250, 250))
        self.arrow_button_left   = pygame.transform.flip(self.arrow_button_right, True, False)
        self.lock_img            = pygame.transform.scale(pygame.image.load('pictures/menu/lock_1.png'), (50, 70))
        self.settings_back_arrow = pygame.transform.scale(self.arrow_button_left, (50, 40))
        self.jump_upgrade_img    = pygame.transform.scale(pygame.image.load('pictures/menu/jump_upgrade.png')   , (80, 100))
        self.speed_upgrade_img   = pygame.transform.scale(pygame.image.load('pictures/menu/speed_upgrade.png')  , (80, 100))
        self.survive_upgrade_img = pygame.transform.scale(pygame.image.load('pictures/menu/survive_upgrade.png'), (80, 100))
        self.pause_button_img.set_colorkey((255, 255, 255))
        # texts
        self.darktext = font_30.render(f'Dark', True, self.textcolor)
        self.lighttext = font_30.render(f'Light', True, self.textcolor)
        # rects
        self.pause_button_rect = self.pause_button_img.get_rect(topright = (screen_width - 20, 10))
        self.start_button_rect = self.start_button_img.get_rect(bottomright = (screen_width - 10, screen_height - 10))
        self.continuerect = Rect(0, 0, 200, 40); self.continuerect.center = (screen_width/2, 250)
        self.restartrect  = Rect(0, 0, 200, 40); self.restartrect.center  = (screen_width/2, 300)
        self.menurect     = Rect(0, 0, 200, 40); self.menurect.center     = (screen_width/2, 350)
        self.quitrect     = Rect(0, 0, 200, 40); self.quitrect.center     = (screen_width/2, 400)
        self.playerscrollleftrect = self.arrow_button_left.get_rect(midleft = (10, screen_height/2))
        self.playerscrollrightrect = self.arrow_button_right.get_rect(midright = (screen_width - 10, screen_height/2))
        self.levelscrollleftrect = self.arrow_button_left.get_rect(midleft = (10, screen_height*0.75))
        self.levelscrollrightrect = self.arrow_button_right.get_rect(midright = (screen_width - 10, screen_height*0.75))
        self.buyrect = Rect(0, 0, 350, 200)
        self.buyrect.center = (screen_width/2, screen_height/2)
        self.cancelrect = Rect(0, 0, self.buyrect.width/2, 50)
        self.cancelrect.bottomleft = self.buyrect.bottomleft
        self.confirmrect = Rect(0, 0, self.buyrect.width/2, 50)
        self.confirmrect.bottomright = self.buyrect.bottomright
        self.exit_button_rect = self.exit_button_img.get_rect(topright = (screen_width - 10, 10))
        self.settings_text_rect = Rect(0, 0, 200, 50)
        self.settings_text_rect.midtop = (screen_width/2, 10)
        self.settings_back_rect = self.settings_back_arrow.get_rect(topleft = (10, 10))
        self.volume_effects_base = Rect(20, 0.3  * screen_height - 5, 150, 10)
        self.volume_music_base =   Rect(20, 0.35 * screen_height - 5, 150, 10)
        self.volume_effects_button = Rect(0, 0, 30, 30)
        self.volume_music_button =   Rect(0, 0, 30, 30)
        self.volume_effects_button.center = (20 + self.volume_effects * 150, 0.3  * screen_height)
        self.volume_music_button.center =   (20 + self.volume_music   * 150, 0.35 * screen_height)
        self.reset_data_rect = Rect(10, 0.4 * screen_height, 100, 30)
        self.jump_upgrade_rect = Rect(0, 0, 125, 170)
        self.jump_upgrade_rect.topleft = (31, 70)
        self.speed_upgrade_rect = self.jump_upgrade_rect.copy()
        self.speed_upgrade_rect.midtop = (screen_width/2, 70)
        self.survive_upgrade_rect = self.jump_upgrade_rect.copy()
        self.survive_upgrade_rect.topright = (screen_width - 31, 70)
        self.darkrect = self.darktext.get_rect(topleft = (20, screen_height * 0.5))
        self.lightrect = self.lighttext.get_rect(topleft = (self.darkrect.right + 5, self.darkrect.top))
        
    def load_images(self):
        with open('game_data.json', 'w') as file:
            data["playerimgpaths"] = []
            for i in range(10):
                dict = {}
                try: 
                    a = pygame.image.load(f'pictures/player/{i}/big.png')
                    dict["big"]      = f'pictures/player/{i}/big.png'
                    dict["running1"] = f'pictures/player/{i}/running1.png'
                    dict["running2"] = f'pictures/player/{i}/running2.png'
                    dict["dead"]     = f'pictures/player/{i}/dead.png'
                    dict["jump"]     = f'pictures/player/{i}/jump.png'
                except: 
                    self.num_players = i - 1
                    break
                data["playerimgpaths"].append(dict)
            data["platformimgpaths"] = []
            for i in range(20):
                try: 
                    a = pygame.image.load(f'pictures/level/{i}.png')
                    data["platformimgpaths"].append(f'pictures/level/{i}.png')
                except: 
                    self.num_levels = len(data["platformtypes"])
                    break
            json.dump(data, file, indent=1)

    def draw_background(self):
        screen.fill(self.background_color)

    def draw_player(self):
        if self.player.xspeed != 0: self.player.last_xspeed = self.player.xspeed
        if self.player.last_xspeed >= 0: #when moving to right or not moving
            if self.player.jump or self.player.xspeed == 0: self.player.image = self.player.jump_r
            elif not self.player.dead and self.player.xspeed > 0 and self.frame % 18 < 9: self.player.image = self.player.running1_r
            else: self.player.image = self.player.running2_r
            if self.player.dead: self.player.image = self.player.dead_r
        else: #when moving to the left
            if self.player.jump or self.player.xspeed == 0: self.player.image = self.player.jump_l
            elif not self.player.dead and self.player.xspeed < 0 and self.frame % 18 < 9: self.player.image = self.player.running1_l
            else: self.player.image = self.player.running2_l
            if self.player.dead: self.player.image = self.player.dead_l
        game.player.rect = game.player.image.get_rect(midbottom = game.player.rect.midbottom)

        screen.blit(self.player.image, self.player.rect)

    def move_player_x(self):
        if keyboard.is_pressed(self.key_moveleft) and self.player.rect.left > 0: 
            self.player.rect.x -= self.move_speed
            self.player.xspeed = -1 * self.move_speed
        elif keyboard.is_pressed(self.key_moveright) and self.player.rect.right < screen_width: 
            self.player.rect.x += self.move_speed
            self.player.xspeed = self.move_speed
        else: self.player.xspeed = 0

    def move_player_y(self):
        if keyboard.is_pressed(self.key_jump) and not self.player.jump: 
            self.jump_sound.play()
            self.player.jump = True
            self.player.yspeed = self.jump_speed
        if keyboard.is_pressed(self.key_duck) and self.player.jump: self.player.yspeed = self.duck_speed
        self.player.yspeed += self.player.gravity
        self.player.rect.y += self.player.yspeed

    def collide_player_x(self):
        for platform in self.platform_group:
            if self.player.rect.colliderect(platform.rect):
                if self.player.xspeed > 0: #moving to the right
                    self.player.rect.right = platform.rect.left
                if self.player.xspeed < 0: #moving to the left
                    self.player.rect.left = platform.rect.right
    
    def collide_player_y(self):
        self.coll = False
        for platform in self.platform_group:
            if self.player.rect.colliderect(platform.rect):
                self.coll = True
                if self.player.yspeed >= 0: #moving down
                    if platform.type == 'fall': 
                        self.fallingplatforms.add(platform)
                    if platform.type == 'explode': 
                        self.platform_group.remove(platform)
                        self.explode(platform)
                    if self.player.yspeed > self.surviving_speed or platform.type == 'kill': 
                        self.state = 'dead'
                        self.death_sound.play()
                        with open('game_data.json', 'w') as f:
                            data["highscores"][self.current_level] = self.highscore
                            json.dump(data, f, indent=1)
                    self.player.rect.bottom = platform.rect.top
                    self.player.jump = False
                    self.player.yspeed = 0
                if self.player.yspeed < 0: #moving up
                    if platform.type == 'kill':
                        self.state = 'dead'
                        self.death_sound.play()
                        with open('game_data.json', 'w') as f:
                            data["highscores"][self.current_level] = self.highscore
                            json.dump(data, f, indent=1)
                    else:
                        self.player.rect.top = platform.rect.bottom
                        self.player.jump = True
                        self.player.yspeed = 0
        if not self.coll and not self.player.jump: #doesn't allow for jumping when running off a tile and falling down
            self.player.jump = True
 
    def move_player(self):
        self.move_player_x()
        self.collide_player_x()
        self.move_player_y()
        self.collide_player_y()

    def scroll(self): 
        if self.player.rect.y < screen_height / 2:
            self.player.rect.y += 10
            for platform in self.platform_group.sprites():
                platform.rect.y += 10
            for coin in self.coin_group.sprites():
                coin.rect.y += 10
        if self.player.rect.y > screen_height *0.8 and self.platform_group.sprites()[0].rect.top > self.ground_height:
            self.player.rect.y -= (self.player.rect.y - screen_height/2 + 100) * 0.1
            for platform in self.platform_group.sprites():
                platform.rect.y -= (self.player.rect.y - screen_height/2 + 100) * 0.1
            for coin in self.coin_group.sprites():
                coin.rect.y -= (self.player.rect.y - screen_height/2 + 100) * 0.1 

        # generate new platform if needed
        if self.platform_group.sprites()[-1].rect.y > 0: 
            choice = [-1, 1]
            platformx = self.platform_group.sprites()[-1].rect.centerx
            if self.platform_group.sprites()[-1].rect.left < 10: choice = [1] # next platform only to the right if last platform is on the left of screen
            if self.platform_group.sprites()[-1].rect.right > screen_width - 10: choice = [-1]
            distance = int(data["levelstats"]["heightdifference"][self.current_level][0] + self.difficulty_increase * self.score)
            platformx += random.randrange(min(150, distance - 50), distance) * random.choice(choice)

            if platformx < self.platform_width/2: platformx = self.platform_width/2
            if platformx > screen_width -  self.platform_width/2: platformx = screen_width - self.platform_width/2

            platformy = self.platform_group.sprites()[-1].rect.top - random.randint(int(data["levelstats"]["heightdifference"][self.current_level][0] + self.difficulty_increase * self.score), int(data["levelstats"]["heightdifference"][self.current_level][1] + self.difficulty_increase * self.score))
            self.new_platform((platformx, platformy))
            
    def new_platform(self, pos):
        imageindex, platformtype = self.get_platform()
        image = self.platform_images[imageindex] #choose random one from json file with propability, get type
        self.platform_group.add(Platform(image, pos, platformtype))
        if random.randint(0, 100) < self.coinspropability:
            self.coin_group.add(Coin(self.coin_img, (pos[0] + random.randint(int(-self.platform_width/3), int(self.platform_width/3)), pos[1] - 50)))
        twoplatformsprop = data["levelstatsdefault"]["twoplatformsprop"][self.current_level]
        imageindex, platformtype1 = self.get_platform()
        while platformtype == 'kill' and platformtype1 == 'kill': imageindex, platformtype1 = self.get_platform() #avoid having two kill platforms at the same height
        image = self.platform_images[imageindex]
        if pos[0] < screen_width/2 and (random.randint(0, 100) <= twoplatformsprop or platformtype == 'kill'):
            new_x = random.randint(pos[0] + self.platform_width + 100, screen_width - self.platform_width/2)
            new_y = pos[1] + random.randint(-20, 20)
            self.platform_group.add(Platform(image, (new_x, new_y), platformtype1))
            if random.randint(0, 100) < self.coinspropability:
                self.coin_group.add(Coin(self.coin_img, (new_x + random.randint(int(-self.platform_width/3), int(self.platform_width/3)), new_y - 50)))
        if pos[0] > screen_width/2 and (random.randint(0, 100) <= twoplatformsprop or platformtype == 'kill'):
            new_x = random.randint(self.platform_width/2, pos[0] - self.platform_width - 100)
            new_y = pos[1] + random.randint(-20, 20)
            self.platform_group.add(Platform(image, (new_x, new_y), platformtype1))
            if random.randint(0, 100) < self.coinspropability:
                self.coin_group.add(Coin(self.coin_img, (new_x + random.randint(int(-self.platform_width/3), int(self.platform_width/3)), new_y - 50)))

    def get_platform(self):
        list = data["platformtypes"][self.current_level]
        rand = random.randint(0, 100)
        sum = 0
        for dict in list:
            sum += dict["propability"]
            if sum >= rand: return dict["imageindex"], dict["type"]

    def explode(self, platform):
        mask = pygame.mask.from_surface(platform.image)
        for x in range(0, platform.rect.width, 4):
            for y in range(0, platform.rect.height, 4):
                if mask.get_at((x, y)) == 1: self.explodingplatforms.add(Fragment((x + platform.rect.x, y +platform.rect.y), platform.image.get_at((x, y))))

    def blit_score(self):
        self.current_score = round((self.player.rect.bottom - self.platform_group.sprites()[0].rect.top) * -0.1)
        self.score = max(self.score, self.current_score)
        self.highscore = max(self.score, self.highscore)
        if self.highscore > data["highscores"][self.current_level] and not self.highscore_broken: 
            self.highscore_sound.play()
            self.highscore_broken = True
            self.start_frame = self.frame
            self.end_animation = False
        score_text = font_30.render(f'Score: {self.score}', True, self.textcolor)
        highscore_text = font_30.render(f'High: {self.highscore}', True, self.textcolor)
        screen.blit(score_text, score_text.get_rect(topleft = (10, 40)))
        screen.blit(highscore_text, highscore_text.get_rect(topleft = (10, 60)))
        cointext = font_30.render(f'{self.coins}', True, self.textcolor)
        screen.blit(cointext, cointext.get_rect(topleft = (40, 10)))
        screen.blit(self.coin_img, self.coin_img.get_rect(topleft = (10, 10)))

    def highscore_animation(self):
        i = self.frame - self.start_frame
        font = Font(None, min(60, 60))
        r = 0; g = 0; b = 0
        if i % 10 > 5: 
            r = self.textcolor[0]
            g = self.textcolor[0]
            b = self.textcolor[0]
        else: r = self.textcolor[0]
        text = font.render('New Highscore!', True, (r, g, b))
        text_rect = text.get_rect(center = (screen_width/2, screen_height*0.4))
        screen.blit(text, text_rect)
        if i > 100: 
            self.end_animation = True
            self.explode_highscore(text, text_rect)

    def explode_highscore(self, text, text_rect):
        mask = pygame.mask.from_surface(text)
        for x in range(0, text_rect.width, 3):
            for y in range(0, text_rect.height, 3):
                if mask.get_at((x, y)) == 1: self.explodingplatforms.add(Fragment((x + text_rect.x, y + text_rect.y), text.get_at((x, y))))

    def collect_coin(self):
        for coin in self.coin_group.sprites():
            if coin.rect.colliderect(self.player.rect): 
                coin.kill()
                self.coins += 1

    def reset_level(self):
        self.score = 0
        self.highscore = data["highscores"][self.current_level]
        self.highscore_broken = False
        self.end_animation = True
        self.coinspropability= data["levelstats"]["coinspropability"][self.current_level]
        self.height_difference= data["levelstats"]["heightdifference"][self.current_level]
        self.difficulty_increase = data["levelstats"]["difficultyincrease"][self.current_level]
        self.platform_group.empty()
        self.fallingplatforms.empty()
        self.explodingplatforms.empty()
        self.coin_group.empty()
        self.ground_height = 650
        self.ground_surf = pygame.transform.scale(pygame.image.load(data["platformimgpaths"][data["platformtypes"][self.current_level][0]["imageindex"]]), (screen_width, self.platform_height/self.platform_width*screen_width))
        self.ground_sprite = Platform(self.ground_surf, (screen_width / 2, screen_height))
        self.platform_group.add(self.ground_sprite)
        self.player.__init__((screen_width / 2, self.ground_height), self.current_player)
        self.player.rect.bottom = self.ground_height
        
    def blit_pause_button(self):
        screen.blit(self.pause_button_img, self.pause_button_rect)

    def click_pause_button(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.pause_button_rect.collidepoint(mouse_pos): self.state = 'pause'

    def blit_pause_menu(self):
        pygame.draw.rect(screen, self.textcolor, self.continuerect.union(self.quitrect).inflate(20, 20))
        pygame.draw.rect(screen, self.background_color, self.continuerect)
        pygame.draw.rect(screen, self.background_color, self.restartrect)
        pygame.draw.rect(screen, self.background_color, self.menurect)
        pygame.draw.rect(screen, self.background_color, self.quitrect)
        continuetext = font_30.render('Continue', True, self.textcolor)
        restarttext  = font_30.render('Restart',  True, self.textcolor)
        menutext     = font_30.render('Menu',     True, self.textcolor)
        quittext     = font_30.render('Quit',     True, self.textcolor)
        screen.blit(continuetext, continuetext.get_rect(center = self.continuerect.center))
        screen.blit(restarttext, restarttext.get_rect(center = self.restartrect.center))
        screen.blit(menutext, menutext.get_rect(center = self.menurect.center))
        screen.blit(quittext, quittext.get_rect(center = self.quitrect.center))

    def click_pause_menu(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.continuerect.collidepoint(mouse_pos): self.state = 'game'
            if self.restartrect.collidepoint(mouse_pos):
                self.state = 'game'
                with open('game_data.json', 'w') as f:
                    data["highscores"][self.current_level] = self.highscore
                    json.dump(data, f, indent=1)
                self.reset_level()
            if self.menurect.collidepoint(mouse_pos): 
                while pygame.mouse.get_pressed(3)[0]:
                    pygame.event.get()
                    sleep(0.01)
                self.state = 'menu'
                with open('game_data.json', 'w') as f:
                    data["highscores"][self.current_level] = self.highscore
                    json.dump(data, f, indent=1)
                self.background_music_level.stop()
                self.background_music_start.play(-1)
            if self.quitrect.collidepoint(mouse_pos): 
                self.save()
                pygame.quit()
                sys.exit()

    def blit_gameovermenu(self):
        gameovertext = font_80.render(f'Game over!', True, self.textcolor)
        screen.blit(gameovertext, gameovertext.get_rect(center = (screen_width/2, screen_height*0.3)))
        pygame.draw.rect(screen, self.textcolor, self.restartrect.union(self.quitrect).inflate(20, 20))
        pygame.draw.rect(screen, self.background_color, self.restartrect)
        pygame.draw.rect(screen, self.background_color, self.menurect)
        pygame.draw.rect(screen, self.background_color, self.quitrect)
        restarttext  = font_30.render('Restart',  True, self.textcolor)
        menutext     = font_30.render('Menu',     True, self.textcolor)
        quittext     = font_30.render('Quit',     True, self.textcolor)
        screen.blit(restarttext, restarttext.get_rect(center = self.restartrect.center))
        screen.blit(menutext, menutext.get_rect(center = self.menurect.center))
        screen.blit(quittext, quittext.get_rect(center = self.quitrect.center))

    def click_gameover(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.restartrect.collidepoint(mouse_pos):
                self.reset_level()
                self.state = 'game'
            if self.menurect.collidepoint(mouse_pos): 
                while pygame.mouse.get_pressed(3)[0]: #wait until mouse not pressed to avoid clicking on the player when getting to menu
                    pygame.event.get()
                    sleep(0.01)
                self.state = 'menu'
                self.background_music_level.stop()
                self.background_music_start.play(-1)
            if self.quitrect.collidepoint(mouse_pos): 
                self.save()
                pygame.quit()
                sys.exit()

    def blit_menu_players(self):
        playercenterimg = pygame.transform.scale(pygame.image.load(data["playerimgpaths"][self.current_player]["big"]), (100, 110))
        self.playercenterrect = playercenterimg.get_rect(center = (screen_width/2, screen_height/2))
        screen.blit(playercenterimg, self.playercenterrect)
        pygame.draw.rect(screen, self.textcolor, self.playercenterrect.inflate(10, 10), 5)
        if data["playerslocked"][self.current_player] == "True":
                screen.blit(self.lock_img, self.lock_img.get_rect(center = self.playercenterrect.center))
                cointext = font_40.render(f'{data["playervalues"][self.current_player]}', True, self.textcolor)
                screen.blit(cointext, cointext.get_rect(topleft = self.playercenterrect.midbottom + Vector2(-20, 10)))
                screen.blit(self.coin_img, self.coin_img.get_rect(topleft = self.playercenterrect.bottomleft + Vector2(0, 10)))

        if self.current_player > 0:
            playerleftimg = pygame.transform.scale(pygame.image.load(data["playerimgpaths"][self.current_player - 1]["big"]), (80, 88))
            self.playerleftrect = playerleftimg.get_rect(center = (screen_width*0.25, screen_height/2))
            screen.blit(playerleftimg, self.playerleftrect)
            pygame.draw.rect(screen, self.textcolor, self.playerleftrect.inflate(10, 10), 5)
            screen.blit(self.arrow_button_left, self.playerscrollleftrect)
            if data["playerslocked"][self.current_player - 1] == "True":
                screen.blit(pygame.transform.scale(self.lock_img, (40, 56)), self.lock_img.get_rect(center = self.playerleftrect.center))
        else: self.playerleftrect = Rect(0, 0, 0, 0)

        if self.current_player < self.num_players:
            playerrightimg = pygame.transform.scale(pygame.image.load(data["playerimgpaths"][self.current_player + 1]["big"]), (80, 88))
            self.playerrightrect = playerrightimg.get_rect(center = (screen_width*0.75, screen_height/2))
            screen.blit(playerrightimg, self.playerrightrect)
            pygame.draw.rect(screen, self.textcolor, self.playerrightrect.inflate(10, 10), 5)
            screen.blit(self.arrow_button_right, self.playerscrollrightrect)
            if data["playerslocked"][self.current_player + 1] == "True":
                screen.blit(pygame.transform.scale(self.lock_img, (40, 56)), self.lock_img.get_rect(center = self.playerrightrect.center))
        else: self.playerrightrect = Rect(0, 0, 0, 0)

    def blit_menu_levels(self):
        levelcenterimg = pygame.transform.scale(pygame.image.load(data["platformimgpaths"][data["platformtypes"][self.current_level][0]["imageindex"]]), (100, 110))
        self.levelcenterrect = levelcenterimg.get_rect(center = (screen_width/2, screen_height*0.75))
        screen.blit(levelcenterimg, self.levelcenterrect)
        pygame.draw.rect(screen, self.textcolor, self.levelcenterrect.inflate(10, 10), 5)
        if data["levelslocked"][self.current_level] == "True":
                screen.blit(self.lock_img, self.lock_img.get_rect(center = self.levelcenterrect.center))
                cointext = font_40.render(f'{data["levelvalues"][self.current_level]}', True, self.textcolor)
                screen.blit(cointext, cointext.get_rect(topleft = self.levelcenterrect.midbottom + Vector2(-20, 10)))
                screen.blit(self.coin_img, self.coin_img.get_rect(topleft = self.levelcenterrect.bottomleft + Vector2(0, 10)))

        if self.current_level > 0:
            levelleftimg = pygame.transform.scale(pygame.image.load(data["platformimgpaths"][data["platformtypes"][self.current_level - 1][0]["imageindex"]]), (80, 88))
            self.levelleftrect = levelleftimg.get_rect(center = (screen_width*0.25, screen_height*0.75))
            screen.blit(levelleftimg, self.levelleftrect)
            pygame.draw.rect(screen, self.textcolor, self.levelleftrect.inflate(10, 10), 5)
            screen.blit(self.arrow_button_left, self.levelscrollleftrect)
            if data["levelslocked"][self.current_level - 1] == "True":
                screen.blit(self.lock_img, self.lock_img.get_rect(center = self.levelleftrect.center))
        else: self.levelleftrect = Rect(0, 0, 0, 0)

        if self.current_level < self.num_levels - 1:
            levelrightimg = pygame.transform.scale(pygame.image.load(data["platformimgpaths"][data["platformtypes"][self.current_level + 1][0]["imageindex"]]), (80, 88))
            self.levelrightrect = levelrightimg.get_rect(center = (screen_width*0.75, screen_height*0.75))
            screen.blit(levelrightimg, self.levelrightrect)
            pygame.draw.rect(screen, self.textcolor, self.levelrightrect.inflate(10, 10), 5)
            screen.blit(self.arrow_button_right, self.levelscrollrightrect)
            if data["levelslocked"][self.current_level + 1] == "True":
                screen.blit(self.lock_img, self.lock_img.get_rect(center = self.levelrightrect.center))
        else: self.levelrightrect = Rect(0, 0, 0, 0)

    def blit_menu(self):
        screen.fill(self.background_color)
        screen.blit(self.start_button_img, self.start_button_rect)
        self.blit_menu_players()
        self.blit_menu_levels()
        cointext = font_30.render(f'{self.coins}', True, self.textcolor)
        screen.blit(cointext, cointext.get_rect(topleft = (40, 10)))
        screen.blit(self.coin_img, self.coin_img.get_rect(topleft = (10, 10)))
        screen.blit(self.exit_button_img, self.exit_button_rect)
        settings_text = font_40.render('Settings', True, self.textcolor)
        screen.blit(settings_text, settings_text.get_rect(center = self.settings_text_rect.center))
        # upgrades for players
        pygame.draw.rect(screen, self.textcolor, self.jump_upgrade_rect, 3)
        pygame.draw.rect(screen, self.textcolor, self.speed_upgrade_rect, 3)
        pygame.draw.rect(screen, self.textcolor, self.survive_upgrade_rect, 3)
        screen.blit(self.jump_upgrade_img, self.jump_upgrade_img.get_rect(midtop = self.jump_upgrade_rect.midtop + Vector2(0, 10)))
        screen.blit(self.speed_upgrade_img, self.speed_upgrade_img.get_rect(midtop = self.speed_upgrade_rect.midtop + Vector2(0, 10)))
        screen.blit(self.survive_upgrade_img, self.survive_upgrade_img.get_rect(midtop = self.survive_upgrade_rect.midtop + Vector2(0, 10)))

        if data["playerstats"]["upgradelevel"][self.current_player]["jump"] < 9:
            cointext = font_40.render(f'{data["playerstats"]["upgradecost"][self.current_player]["jump"][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]}', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(topleft = self.jump_upgrade_rect.midbottom + Vector2(-10, 10)))
            screen.blit(self.coin_img, self.coin_img.get_rect(topleft = self.jump_upgrade_rect.bottomleft + Vector2(10, 10)))
        else: 
            cointext = font_40.render('Max Level', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(midtop = self.jump_upgrade_rect.midbottom + Vector2(0, 10)))
        leveltext = font_40.render(f'Level {data["playerstats"]["upgradelevel"][self.current_player]["jump"] + 1}', True, self.textcolor)
        screen.blit(leveltext, leveltext.get_rect(midbottom = self.jump_upgrade_rect.midbottom + Vector2(0, -10)))

        if data["playerstats"]["upgradelevel"][self.current_player]["speed"] < 9:
            cointext = font_40.render(f'{data["playerstats"]["upgradecost"][self.current_player]["speed"][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]}', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(topleft = self.speed_upgrade_rect.midbottom + Vector2(-10, 10)))
            screen.blit(self.coin_img, self.coin_img.get_rect(topleft = self.speed_upgrade_rect.bottomleft + Vector2(10, 10)))
        else: 
            cointext = font_40.render('Max Level', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(midtop = self.speed_upgrade_rect.midbottom + Vector2(0, 10)))
        leveltext = font_40.render(f'Level {data["playerstats"]["upgradelevel"][self.current_player]["speed"] + 1}', True, self.textcolor)
        screen.blit(leveltext, leveltext.get_rect(midbottom = self.speed_upgrade_rect.midbottom + Vector2(0, -10)))

        if data["playerstats"]["upgradelevel"][self.current_player]["survive"] < 9:
            cointext = font_40.render(f'{data["playerstats"]["upgradecost"][self.current_player]["survive"][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]}', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(topleft = self.survive_upgrade_rect.midbottom + Vector2(-10, 10)))
            screen.blit(self.coin_img, self.coin_img.get_rect(topleft = self.survive_upgrade_rect.bottomleft + Vector2(10, 10)))
        else: 
            cointext = font_40.render('Max Level', True, self.textcolor)
            screen.blit(cointext, cointext.get_rect(midtop = self.survive_upgrade_rect.midbottom + Vector2(0, 10)))
        leveltext = font_40.render(f'Level {data["playerstats"]["upgradelevel"][self.current_player]["survive"] + 1}', True, self.textcolor)
        screen.blit(leveltext, leveltext.get_rect(midbottom = self.survive_upgrade_rect.midbottom + Vector2(0, -10)))

    def scroll_players(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if (self.playerscrollleftrect.collidepoint(mouse_pos) or self.playerleftrect.collidepoint(mouse_pos)) and self.current_player > 0 and not self.changeplayer: 
                self.current_player -= 1
                self.changeplayer = True
            elif (self.playerscrollrightrect.collidepoint(mouse_pos) or self.playerrightrect.collidepoint(mouse_pos)) and self.current_player < self.num_players and not self.changeplayer: 
                self.current_player += 1
                self.changeplayer = True
        else: self.changeplayer = False
        self.surviving_speed = data["playerstats"]["survivingspeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]
        self.jump_speed      = data["playerstats"]["jumpspeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]
        self.duck_speed      = data["playerstats"]["duckspeed"][self.current_player]
        self.move_speed      = data["playerstats"]["movespeed"][self.current_player][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]

    def scroll_levels(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if (self.levelscrollleftrect.collidepoint(mouse_pos) or self.levelleftrect.collidepoint(mouse_pos)) and self.current_level > 0 and not self.changelevel: 
                self.current_level -= 1
                self.changelevel = True
            elif (self.levelscrollrightrect.collidepoint(mouse_pos) or self.levelrightrect.collidepoint(mouse_pos)) and self.current_level < self.num_levels - 1 and not self.changelevel: 
                self.current_level += 1
                self.changelevel = True
        else: self.changelevel = False # avoid changing levels over and over when holding mouse
    
    def click_menu(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.start_button_rect.collidepoint(mouse_pos):
                if data["levelslocked"][self.current_level] == "True":
                    self.not_unlocked('level')
                elif data["playerslocked"][self.current_player] == "True":
                    self.not_unlocked('player')
                else:
                    self.reset_level()
                    self.player.update_pictures(data["playerimgpaths"][self.current_player])
                    self.state = 'game'
                    self.background_music_start.stop()
                    self.background_music_level.play(-1)
            
            if self.playercenterrect.collidepoint(mouse_pos) and data["playerslocked"][self.current_player] == "True":
                self.buy_thing('player')
            if self.levelcenterrect.collidepoint(mouse_pos) and data["levelslocked"][self.current_level] == "True":
                self.buy_thing('level')
            if self.exit_button_rect.collidepoint(mouse_pos): 
                self.save()
                pygame.quit()
                sys.exit()
            if self.settings_text_rect.collidepoint(mouse_pos): self.state = 'settings'

        self.scroll_players()
        self.scroll_levels()
        self.upgrade_players()

    def wait_until_clicked(self, listofrects, waitforrelease):
        if waitforrelease: 
            while pygame.mouse.get_pressed(3)[0]: 
                pygame.event.get()
                sleep(0.01) # wait until mouse not pressed anymore
        while not pygame.mouse.get_pressed(3)[0]:
            pygame.event.get()
            sleep(0.01)      # wait until pressed again
        mouse_pos = pygame.mouse.get_pos() #get mouse position
        pointrect = Rect(mouse_pos[0], mouse_pos[1], 1, 1) #make a tiny rect on the mouse pos
        if pointrect.collidelist(listofrects) == -1: #if mouse pos collides with any of the given rectangles: return the rectangle
            return self.wait_until_clicked(listofrects, True) #listofrects[pointrect.collidelist(listofrects)]
        else:             return listofrects[pointrect.collidelist(listofrects)] #else: recursively call itself to start again

    def blit_not_enough_money(self, morecoins):
        self.error_sound.play()
        pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
        text1 = font_40.render(f"Not enough coins!", True, self.textcolor)
        text2 = font_40.render(f'You need {morecoins} more', True, self.textcolor)
        screen.blit(text1, text1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
        screen.blit(text2, text2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
        confirmtext = font_40.render(f'OK', True, self.textcolor)
        screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
        pygame.display.update()
        self.wait_until_clicked([self.confirmrect], True)

    def not_unlocked(self, type):
        self.error_sound.play()
        pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
        text1 = font_40.render(f"You haven't unlocked", True, self.textcolor)
        text2 = font_40.render(f'this {type}!', True, self.textcolor)
        screen.blit(text1, text1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
        screen.blit(text2, text2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
        confirmtext = font_40.render(f'OK', True, self.textcolor)
        screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
        pygame.display.update()
        self.wait_until_clicked([self.confirmrect], True)

    def buy_thing(self, type):
        pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
        if type == 'player': value = data["playervalues"][self.current_player]
        else:  value = data["levelvalues"][self.current_level]
        buytext1 = font_40.render(f'Do you want to buy this', True, self.textcolor)
        buytext2 = font_40.render(f'{type} for {value} coins?', True, self.textcolor)
        screen.blit(buytext1, buytext1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
        screen.blit(buytext2, buytext2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
        confirmtext = font_40.render(f'OK', True, self.textcolor)
        canceltext = font_40.render(f'Cancel', True, self.textcolor)
        screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
        screen.blit(canceltext, canceltext.get_rect(center = self.cancelrect.center))
        pygame.display.update()
        collrect = self.wait_until_clicked([self.cancelrect, self.confirmrect], waitforrelease=True)
        if collrect == self.confirmrect:
            with open('game_data.json', 'w') as file:
                if type == 'player': 
                    if self.coins >= data["playervalues"][self.current_player]:
                        self.coins -= data["playervalues"][self.current_player]
                        data["playerslocked"][self.current_player] = "False"
                        self.kaching_sound.play()
                    else: 
                        self.blit_not_enough_money(morecoins = data["playervalues"][self.current_player] - self.coins)
                if type == 'level': 
                    if self.coins >= data["levelvalues"][self.current_level]:
                        self.coins -= data["levelvalues"][self.current_level]
                        data["levelslocked"][self.current_level] = "False"
                        self.kaching_sound.play()
                    else: 
                        self.blit_not_enough_money(morecoins = data["levelvalues"][self.current_level]   - self.coins)
                json.dump(data, file, indent=1)
            
    def upgrade_players(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.jump_upgrade_rect.collidepoint(mouse_pos) and data["playerstats"]["upgradelevel"][self.current_player]["jump"] < 9:
                pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
                buytext1 = font_40.render(f'Jump higher!', True, self.textcolor)
                buytext2 = font_40.render(f'Upgrade for {data["playerstats"]["upgradecost"][self.current_player]["jump"][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]} coins?', True, self.textcolor)
                screen.blit(buytext1, buytext1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
                screen.blit(buytext2, buytext2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
                confirmtext = font_40.render(f'OK', True, self.textcolor)
                canceltext = font_40.render(f'Cancel', True, self.textcolor)
                screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
                screen.blit(canceltext, canceltext.get_rect(center = self.cancelrect.center))
                pygame.display.update()
                collrect = self.wait_until_clicked([self.cancelrect, self.confirmrect], waitforrelease=True)
                if collrect == self.confirmrect:
                    if self.coins >= data["playerstats"]["upgradecost"][self.current_player]["jump"][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]:
                        self.coins -= data["playerstats"]["upgradecost"][self.current_player]["jump"][data["playerstats"]["upgradelevel"][self.current_player]["jump"]]
                        self.kaching_sound.play()
                        with open('game_data.json', 'w') as f:
                            data["playerstats"]["upgradelevel"][self.current_player]["jump"] += 1
                            json.dump(data, f, indent=1)
                    else: self.blit_not_enough_money(data["playerstats"]["upgradecost"][self.current_player]["jump"][data["playerstats"]["upgradelevel"][self.current_player]["jump"]] - self.coins)
            
            if self.speed_upgrade_rect.collidepoint(mouse_pos) and data["playerstats"]["upgradelevel"][self.current_player]["speed"] < 9:
                pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
                buytext1 = font_40.render(f'Run faster!', True, self.textcolor)
                buytext2 = font_40.render(f'Upgrade for {data["playerstats"]["upgradecost"][self.current_player]["speed"][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]} coins?', True, self.textcolor)
                screen.blit(buytext1, buytext1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
                screen.blit(buytext2, buytext2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
                confirmtext = font_40.render(f'OK', True, self.textcolor)
                canceltext = font_40.render(f'Cancel', True, self.textcolor)
                screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
                screen.blit(canceltext, canceltext.get_rect(center = self.cancelrect.center))
                pygame.display.update()
                collrect = self.wait_until_clicked([self.cancelrect, self.confirmrect], waitforrelease=True)
                if collrect == self.confirmrect:
                    if self.coins >= data["playerstats"]["upgradecost"][self.current_player]["speed"][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]:
                        self.coins -= data["playerstats"]["upgradecost"][self.current_player]["speed"][data["playerstats"]["upgradelevel"][self.current_player]["speed"]]
                        self.kaching_sound.play()
                        with open('game_data.json', 'w') as f:
                            data["playerstats"]["upgradelevel"][self.current_player]["speed"] += 1
                            json.dump(data, f, indent=1)
                    else: self.blit_not_enough_money(data["playerstats"]["upgradecost"][self.current_player]["speed"][data["playerstats"]["upgradelevel"][self.current_player]["speed"]] - self.coins)
            
            if self.survive_upgrade_rect.collidepoint(mouse_pos) and data["playerstats"]["upgradelevel"][self.current_player]["survive"] < 9:
                pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
                buytext1 = font_40.render(f'Survive from higher!', True, self.textcolor)
                buytext2 = font_40.render(f'Upgrade for {data["playerstats"]["upgradecost"][self.current_player]["survive"][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]} coins?', True, self.textcolor)
                screen.blit(buytext1, buytext1.get_rect(center = self.buyrect.center + Vector2(0, -30)))
                screen.blit(buytext2, buytext2.get_rect(center = self.buyrect.center + Vector2(0, 10)))
                confirmtext = font_40.render(f'OK', True, self.textcolor)
                canceltext = font_40.render(f'Cancel', True, self.textcolor)
                screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
                screen.blit(canceltext, canceltext.get_rect(center = self.cancelrect.center))
                pygame.display.update()
                collrect = self.wait_until_clicked([self.cancelrect, self.confirmrect], waitforrelease=True)
                if collrect == self.confirmrect:
                    if self.coins >= data["playerstats"]["upgradecost"][self.current_player]["survive"][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]:
                        self.coins -= data["playerstats"]["upgradecost"][self.current_player]["survive"][data["playerstats"]["upgradelevel"][self.current_player]["survive"]]
                        self.kaching_sound.play()
                        with open('game_data.json', 'w') as f:
                            data["playerstats"]["upgradelevel"][self.current_player]["survive"] += 1
                            json.dump(data, f, indent=1)
                    else: self.blit_not_enough_money(data["playerstats"]["upgradecost"][self.current_player]["survive"][data["playerstats"]["upgradelevel"][self.current_player]["survive"]] - self.coins)       

    def blit_settings(self):
        screen.fill(self.background_color)
        screen.blit(self.settings_back_arrow, self.settings_back_rect)
        screen.blit(self.exit_button_img, self.exit_button_rect)
        screen.blit(self.jump_key_text, self.jump_key_text_rect)
        screen.blit(self.duck_key_text, self.duck_key_text_rect)
        screen.blit(self.left_key_text, self.left_key_text_rect)
        screen.blit(self.right_key_text, self.right_key_text_rect)

        pygame.draw.rect(screen, self.textcolor, self.volume_effects_base)   
        pygame.draw.rect(screen, (255, 0, 0), self.volume_effects_button)
        self.volume_effects_text = font_30.render(f'Volume Effects: {round(self.volume_effects, 2)}', True, self.textcolor)
        self.volume_effects_text_rect = self.volume_effects_text.get_rect(midleft = (self.volume_effects_base.right + 20, self.volume_effects_base.top))
        screen.blit(self.volume_effects_text, self.volume_effects_text_rect)

        pygame.draw.rect(screen, self.textcolor, self.volume_music_base)   
        pygame.draw.rect(screen, (255, 0, 0), self.volume_music_button)
        self.volume_music_text = font_30.render(f'Volume Music: {round(self.volume_music, 2)}', True, self.textcolor)
        self.volume_music_text_rect = self.volume_music_text.get_rect(midleft = (self.volume_music_base.right + 20, self.volume_music_base.top))
        screen.blit(self.volume_music_text, self.volume_music_text_rect)

        reset_data_text = font_30.render(f'Reset Data', True, self.textcolor)
        screen.blit(reset_data_text, reset_data_text.get_rect(center = self.reset_data_rect.center))

        screen.blit(self.darktext, self.darkrect)
        screen.blit(self.lighttext, self.lightrect)
        if data["darkmode"] == 'dark': pygame.draw.rect(screen, self.textcolor, self.darkrect.inflate(4, 4), 3)
        else:                          pygame.draw.rect(screen, self.textcolor, self.lightrect.inflate(4, 4), 3)

    def change_volume(self):
        if pygame.mouse.get_pressed()[0]: #if left mouse button is pressed
            mouse_pos = pygame.mouse.get_pos()
            if self.volume_effects_button.collidepoint(mouse_pos): #clicks the red button 
                while True:
                    pygame.event.get()
                    if pygame.mouse.get_pressed()[0]: #if left mouse button is still pressed
                        mouse_pos = pygame.mouse.get_pos()
                        self.volume_effects = (mouse_pos[0] - 20) / 150
                        if self.volume_effects > 1: self.volume_effects = 1
                        if self.volume_effects < 0: self.volume_effects = 0
                        self.volume_effects_button.center = (20 + self.volume_effects * 150, 0.3 * screen_height)
                        self.volume_effects_text = font_30.render(f'Volume Effects: {round(self.volume_effects, 2)}', True, self.textcolor)
                        self.volume_effects_text_rect = self.volume_effects_text.get_rect(midleft = (self.volume_effects_base.right + 20, self.volume_effects_base.top))
                        self.blit_settings()
                        pygame.display.update()
                        self.death_sound.set_volume(self.volume_effects)
                        self.error_sound.set_volume(self.volume_effects)
                        self.kaching_sound.set_volume(self.volume_effects)
                        self.highscore_sound.set_volume(self.volume_effects)
                        self.jump_sound.set_volume(self.volume_effects)
                    else: break #stop loop
            if self.volume_music_button.collidepoint(mouse_pos):
                while True:
                    pygame.event.get()
                    if pygame.mouse.get_pressed()[0]: 
                        mouse_pos = pygame.mouse.get_pos()
                        self.volume_music = (mouse_pos[0] - 20) / 150
                        if self.volume_music > 1: self.volume_music = 1
                        if self.volume_music < 0: self.volume_music = 0
                        self.volume_music_button.center = (20 + self.volume_music * 150, 0.35 * screen_height)
                        self.volume_music_text = font_30.render(f'Volume Music: {round(self.volume_music, 2)}', True, self.textcolor)
                        self.volume_music_text_rect = self.volume_music_text.get_rect(midleft = (self.volume_music_base.right + 20, self.volume_music_base.top))
                        self.blit_settings()
                        pygame.display.update()
                        self.background_music_start.set_volume(self.volume_music)
                        self.background_music_level.set_volume(self.volume_music)
                    else: break 

    def change_key(self):
        pygame.event.get()
        if pygame.mouse.get_pressed()[0]: #if left mouse button is pressed
            mouse_pos = pygame.mouse.get_pos()
            if self.jump_key_text_rect.collidepoint(mouse_pos):
                #jump key text is pressed
                pygame.draw.rect(screen, (0, 255, 0), self.jump_key_text_rect, 3)
                pygame.display.update()
                sleep(0.1)
                #wait for keyboard input and set jump key to the pressed key
                self.key_jump = str(keyboard.read_key())
            if self.left_key_text_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (0, 255, 0), self.left_key_text_rect, 3)
                pygame.display.update()
                sleep(0.1)
                self.key_moveleft = str(keyboard.read_key())
            if self.right_key_text_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (0, 255, 0), self.right_key_text_rect, 3)
                pygame.display.update()
                sleep(0.1)
                self.key_moveright = str(keyboard.read_key())
            if self.duck_key_text_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (0, 255, 0), self.duck_key_text_rect, 3)
                pygame.display.update()
                sleep(0.1)
                self.key_duck = str(keyboard.read_key())

            self.jump_key_text           = font_30.render(f'Jump Key: {self.key_jump}',      True, self.textcolor)
            self.left_key_text           = font_30.render(f'Left Key: {self.key_moveleft}',  True, self.textcolor)
            self.right_key_text          = font_30.render(f'Right Key: {self.key_moveright}', True, self.textcolor)
            self.duck_key_text           = font_30.render(f'Duck Key: {self.key_duck}',      True, self.textcolor)
            self.jump_key_text_rect      = self.jump_key_text.get_rect(topleft = (10, screen_height * 0.10))
            self.left_key_text_rect      = self.left_key_text.get_rect(topleft = (10, screen_height * 0.15))
            self.right_key_text_rect     = self.right_key_text.get_rect(topleft= (10, screen_height * 0.20))
            self.duck_key_text_rect      = self.duck_key_text.get_rect(topleft = (10, screen_height * 0.25))

    def click_settings(self):
        if pygame.mouse.get_pressed(3)[0]: 
            mouse_pos = pygame.mouse.get_pos()
            if self.settings_back_rect.collidepoint(mouse_pos): self.state = 'menu'
            if self.exit_button_rect.collidepoint(mouse_pos): 
                    self.save()
                    pygame.quit()
                    sys.exit()
            if self.reset_data_rect.collidepoint(mouse_pos):
                self.reset_data()
            if self.darkrect.collidepoint(mouse_pos) and data["darkmode"] != "dark": 
                self.background_color = (50, 50, 50)
                self.textcolor = (250, 250, 250)
                self.darktext = font_30.render(f'Dark', True, self.textcolor)
                self.lighttext = font_30.render(f'Light', True, self.textcolor)
                self.pause_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/pause_button_light.png'), (40, 40))
                self.exit_button_img     = pygame.transform.scale(pygame.image.load('pictures/menu/exit_button_light.png'), (35, 35))
                self.start_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_light.png'), (60, 50))
                self.arrow_button_right  = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_light.png'), (20, 50))
                self.arrow_button_left   = pygame.transform.flip(self.arrow_button_right, True, False)
                self.settings_back_arrow = pygame.transform.scale(self.arrow_button_left, (50, 40))
                self.pause_button_img.set_colorkey((50, 50, 50))
                self.exit_button_img.set_colorkey((50, 50, 50))
                self.start_button_img.set_colorkey((50, 50, 50))
                self.arrow_button_left.set_colorkey((50, 50, 50))
                self.arrow_button_right.set_colorkey((50, 50, 50))
                with open('game_data.json', 'w') as f:
                    data["darkmode"] = "dark"
                    json.dump(data, f, indent=1)
            if self.lightrect.collidepoint(mouse_pos) and data["darkmode"] != "light": 
                self.background_color = (250, 250, 250)
                self.textcolor = (50, 50, 50)
                self.darktext = font_30.render(f'Dark', True, self.textcolor)
                self.lighttext = font_30.render(f'Light', True, self.textcolor)
                self.pause_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/pause_button_dark.png'), (40, 40))
                self.exit_button_img     = pygame.transform.scale(pygame.image.load('pictures/menu/exit_button_dark.png'), (35, 35))
                self.start_button_img    = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_dark.png'), (60, 50))
                self.arrow_button_right  = pygame.transform.scale(pygame.image.load('pictures/menu/play_level_dark.png'), (20, 50))
                self.arrow_button_left   = pygame.transform.flip(self.arrow_button_right, True, False)
                self.settings_back_arrow = pygame.transform.scale(self.arrow_button_left, (50, 40))
                self.pause_button_img.set_colorkey(((250, 250, 250)))
                self.exit_button_img.set_colorkey((250, 250, 250))
                self.start_button_img.set_colorkey((250, 250, 250))
                self.arrow_button_left.set_colorkey((250, 250, 250))
                self.arrow_button_right.set_colorkey((250, 250, 250))
                with open('game_data.json', 'w') as f:
                    data["darkmode"] = "light"
                    json.dump(data, f, indent=1)

    def reset_data(self):
        pygame.draw.rect(screen, (200, 200, 200), self.buyrect)
        text1 = font_40.render('Do you really want to ', True, self.textcolor)
        text2 = font_40.render('reset all the data?', True, self.textcolor)
        text3 = font_40.render('You will lose all progress!', True, self.textcolor)
        screen.blit(text1, text1.get_rect(center = self.buyrect.center + Vector2(0, -50)))
        screen.blit(text2, text2.get_rect(center = self.buyrect.center + Vector2(0, -20)))
        screen.blit(text3, text3.get_rect(center = self.buyrect.center + Vector2(0, 10)))
        confirmtext = font_40.render(f'OK', True, self.textcolor)
        canceltext = font_40.render(f'Cancel', True, self.textcolor)
        screen.blit(confirmtext, confirmtext.get_rect(center = self.confirmrect.center))
        screen.blit(canceltext, canceltext.get_rect(center = self.cancelrect.center))
        pygame.display.update()
        collrect = self.wait_until_clicked([self.cancelrect, self.confirmrect], waitforrelease=True)
        if collrect == self.confirmrect:
            with open('game_data.json', 'w') as file:
                self.coins             = 0
                self.current_level     = 0
                self.current_player    = 0
                self.volume_effects    = 0.1
                self.volume_music      = 0.1
                data["coins"]          = 0
                data["currentlevel"]   = 0
                data["currentplayer"]  = 0
                data["jump_key"]       = 'w'
                data["duck_key"]       = 's'
                data["left_key"]       = 'a'
                data["right_key"]      = 'd'
                data["volume_effects"] = 0.1
                data["volume_music"]   = 0.1
                data["highscores"]     = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                data["playerstats"]    = data["playerstatsdefault"]
                data["levelstats"]     = data["levelstatsdefault"]
                data["playerslocked"]  = ["False", "True", "True", "True", "True", "True", "True", "True", "True", "True"]
                data["levelslocked"]   = ["False", "True", "True", "True", "True", "True", "True", "True", "True", "True"]
                data["darkmode"]       = "light"
                json.dump(data, file, indent=None)

    def save(self):
        with open('game_data.json', 'w') as f:
            data["coins"]          = self.coins
            data["currentlevel"]   = self.current_level
            data["currentplayer"]  = self.current_player
            data["jump_key"]       = self.key_jump
            data["duck_key"]       = self.key_duck
            data["left_key"]       = self.key_moveleft
            data["right_key"]      = self.key_moveright
            data["volume_effects"] = round(self.volume_effects, 2)
            data["volume_music"]   = round(self.volume_music  , 2)
            json.dump(data, f, indent=1)

pygame.init()

screen_size = screen_width, screen_height = (data["width"], data["height"])
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('')
pygame.display.set_icon(pygame.image.load('pictures/icon.png'))
clock = pygame.time.Clock()
font_30 = Font(None, 30)
font_40 = Font(None, 40)
font_80 = Font(None, 80)

game = Game()

def main():
    game.background_music_start.play(-1)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keyboard.is_pressed('esc'):
                game.save()
                pygame.quit()
                sys.exit()

        if game.state == 'game':
            game.move_player()
            game.scroll()
            game.collect_coin()
            game.fallingplatforms.update()
            game.explodingplatforms.update()

            game.draw_background()
            game.platform_group.draw(screen)
            game.fallingplatforms.draw(screen)
            game.explodingplatforms.draw(screen)
            game.coin_group.draw(screen)
            game.draw_player()
            game.blit_score()
            if not game.end_animation: game.highscore_animation()
            game.blit_pause_button()
            game.click_pause_button()
        
        if game.state == 'dead': 
            game.blit_gameovermenu()
            game.click_gameover()

        if game.state == 'pause':
            game.blit_pause_menu()
            game.click_pause_menu()

        if game.state == 'menu':
            game.blit_menu()
            game.click_menu()

        if game.state == 'settings':
            game.blit_settings()
            game.click_settings()
            game.change_key()
            game.change_volume()

        pygame.display.update()
        clock.tick(game.fps)
        game.frame += 1


if __name__ == '__main__': 
    main()


# scrolling background ?

# different background music for the levels

# special abilities for players:
# -double jump ?
# -super speed
# -immortal
# -extra money for reached score
# -...

# -name and better pictures for levels and players in menu

# -damage system with health instead of surviving speed ?


# start_time = time()
# fps = 1/ (time() - start_time)
# start_time = time()
# if fps < 50: print(round(fps))