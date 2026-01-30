import pygame
from pygame.locals import *
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
import random
import time
import sys
import threading
import keyboard
from tkinter import messagebox
from collections import OrderedDict

class ZiplayiverCekirge2:
    def __init__(self, width=None, height=None, title="ZiplayiverCekirge2"):
        pygame.init()
        if width is None or height is None:
            display_info = pygame.display.Info()
            width = display_info.current_w if width is None else width
            height = display_info.current_h if height is None else height
        self.screen_width = width
        self.screen_height = height
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption(title)
        self.pixels = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        self.screen.fill((0, 0, 0))
        self.is_hidden = False
        self.is_fullscreen = False
        self.image_cache = OrderedDict()
        self.cache_limit = 256 
        self.horror_mode = False
        self.dirty_rects = [] 
        self.clock_obj = None 
        self.update_optimization = 4
        self.update_count = 0

    def _manage_cache(self, key):
        if key in self.image_cache:
            self.image_cache.move_to_end(key)
        if len(self.image_cache) > self.cache_limit:
            self.image_cache.popitem(last=False)

    def clock(self, fps=60):
        self.clock_obj = pygame.time.Clock()
        self.fps = max(1, fps)  # Ensure FPS is positive

    def tick(self):
        self.clock_obj.tick_busy_loop(self.fps)

    def set_screen(self, width=None, height=None):
        self.screen_width = width if width is not None else self.screen_width
        self.screen_height = height if height is not None else self.screen_height
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | (pygame.FULLSCREEN if self.is_fullscreen else 0)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
        self.pixels = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
        self.screen.fill((0, 0, 0))
        self.image_cache.clear()  # Clear cache on screen resize
        self.dirty_rects = []

    def get_screen(self):
        surface = pygame.display.get_surface()
        return surface.get_size() if surface else (self.screen_width, self.screen_height)

    def set_title(self, title="ZiplayiverCekirge2"):
        pygame.display.set_caption(title)

    def set_pixel(self, x=0, y=0, color=(255, 0, 0)):
        x, y = int(x), int(y)
        if self.horror_mode:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            color = tuple(max(min(h + random.randint(-5, 5), 255), 0) for h in color)
        if 0 <= x < self.screen_width and 0 <= y < self.screen_height:
            self.pixels[y, x] = color[:3]
            self.screen.set_at((x, y), color[:3])
            self.dirty_rects.append(pygame.Rect(x, y, 1, 1))

    def get_pixel(self, x=0, y=0):
        x, y = int(x), int(y)
        if 0 <= x < self.screen_width and 0 <= y < self.screen_height:
            return tuple(self.pixels[y, x])
        return (0, 0, 0)

    def circle(self, x=0, y=0, color=(255, 0, 0), size=16):
        x, y, size = int(x), int(y), int(size)
        if self.horror_mode:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            color = tuple(max(min(h + random.randint(-5, 5), 255), 0) for h in color)
            size = max(size + random.randint(-1, 1), 1)
        pygame.draw.circle(self.screen, color[:3], (x, y), size)
        self.dirty_rects.append(pygame.Rect(x - size, y - size, size * 2, size * 2))

    def rect(self, x=0, y=0, color=(255, 0, 0), width=16, height=16, alpha=255):
        x, y, width, height = int(x), int(y), int(width), int(height)
        if self.horror_mode:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            color = tuple(max(min(h + random.randint(-5, 5), 255), 0) for h in color)
            alpha = random.randint(128, 255)
        color = color[:3]
        rect = pygame.Rect(x, y, width, height)
        if alpha < 255:
            temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            temp_surface.fill(color + (alpha,))
            self.screen.blit(temp_surface, (x, y))
        else:
            pygame.draw.rect(self.screen, color, rect)
        self.dirty_rects.append(rect)

    def stick(self, x=0, y=0, x2=512, y2=512, color=(255, 0, 0), alpha=255):
        x, y, x2, y2 = int(x), int(y), int(x2), int(y2)
        if self.horror_mode:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            color = tuple(max(min(h + random.randint(-5, 5), 255), 0) for h in color)
        color = color[:3]
        if alpha < 255:
            temp_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            pygame.draw.line(temp_surface, color + (alpha,), (x, y), (x2, y2))
            self.screen.blit(temp_surface, (0, 0))
            self.dirty_rects.append(pygame.Rect(min(x, x2), min(y, y2), abs(x2 - x) + 1, abs(y2 - y) + 1))
        else:
            pygame.draw.line(self.screen, color, (x, y), (x2, y2))
            self.dirty_rects.append(pygame.Rect(min(x, x2), min(y, y2), abs(x2 - x) + 1, abs(y2 - y) + 1))

    def image(self, x=0, y=0, file="image.png", width=None, height=None, 
              color_changer=False, color=(255, 0, 0), color_force=32,
              sharpness=1.0, saturation=1.0, brightness=1.0, contrast=1.0, 
              alpha=255, rotate=0):
        x, y = int(x), int(y)
        color = color[:3]
        cache_key = (file, width, height, sharpness, saturation, brightness, contrast, alpha, rotate)
        if self.horror_mode:
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            saturation += random.randint(32, 64)
            contrast += random.randint(16, 32)
            brightness = random.uniform(0.1, 0.5)
            alpha = random.randint(128, 255)
            rotate += random.uniform(-1, 1)
        if cache_key in self.image_cache:
            pygame_img = self.image_cache[cache_key]
            self.screen.blit(pygame_img, (x, y))
            if color_changer:
                self.rect(x=x, y=y, width=width or pygame_img.get_width(), 
                         height=height or pygame_img.get_height(), color=color, alpha=color_force)
            self.dirty_rects.append(pygame.Rect(x, y, pygame_img.get_width(), pygame_img.get_height()))
            self._manage_cache(cache_key)
            return
        try:
            img = Image.open(file).convert("RGBA")
            img = ImageEnhance.Contrast(img).enhance(contrast)
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
            img = ImageEnhance.Color(img).enhance(saturation)
            img = ImageEnhance.Brightness(img).enhance(brightness)
            img_width, img_height = img.size
            width = img_width if width is None else int(width)
            height = img_height if height is None else int(height)
            # Use Pygame for scaling if no advanced PIL processing needed
            if sharpness == 1.0 and saturation == 1.0 and brightness == 1.0 and contrast == 1.0:
                pygame_img = pygame.image.load(file).convert_alpha()
                if (width != img_width or height != img_height) or rotate != 0:
                    pygame_img = pygame.transform.smoothscale(pygame_img, (width, height))
            else:
                resampler = Image.Resampling.BICUBIC if width > img_width or height > img_height else Image.Resampling.LANCZOS
                img = img.resize((width, height), resampler)
                data = img.tobytes()
                pygame_img = pygame.image.fromstring(data, img.size, "RGBA").convert_alpha()
            if rotate != 0:
                pygame_img = pygame.transform.rotate(pygame_img, -rotate)
            if alpha < 255:
                pygame_img.set_alpha(alpha)
            self.image_cache[cache_key] = pygame_img
            self.screen.blit(pygame_img, (x, y))
            if color_changer:
                self.rect(x=x, y=y, width=width, height=height, color=color, alpha=color_force)
            self.dirty_rects.append(pygame.Rect(x, y, width, height))
            self._manage_cache(cache_key)
        except Exception as e:
            print(f"Görüntü yükleme hatası: {e}")

    def text(self, text="Hello, World!", x=0, y=0, size=32, color=(255, 0, 0), alpha=255, font=None, sysfont=False):
        x, y, size = int(x), int(y), int(size)
        if self.horror_mode:
            font = "Arial"
            arab = {"a":"ا","b":"ب","c":"ج","d":"د","e":"ي","f":"ف","g":"ج","h":"ه","i":"ي","j":"ج","k":"ك","l":"ل","m":"م","n":"ن","o":"و","p":"ب","q":"ق","r":"ر","s":"س","t":"ت","u":"و","v":"ف","w":"و","x":"كس","y":"ي","z":"ز"}
            text = "".join([(arab[h.lower()] if h.lower() in arab else h) for h in text])
            x += random.randint(-1, 1)
            y += random.randint(-1, 1)
            color = tuple(int(max(min(h + random.randint(-5, 5), 255), 0)) for h in color)
            sysfont = True
            size = int(max(size / 1.5, 0.1))
        color = color[:3]
        cache_key = (text, size, tuple(color), alpha, font)
        if self.horror_mode:
            alpha = random.randint(128, 255)
        if cache_key in self.image_cache:
            text_surface = self.image_cache[cache_key]
            self.screen.blit(text_surface, (x, y))
            self.dirty_rects.append(text_surface.get_rect(topleft=(x, y)))
            self._manage_cache(cache_key)
            return
        try:
            font_obj = pygame.font.SysFont(font, size) if sysfont else pygame.font.Font(font, size) if font else pygame.font.SysFont(None, size)
            text_surface = font_obj.render(text, True, color)
            if alpha < 255:
                text_surface.set_alpha(alpha)
            self.image_cache[cache_key] = text_surface
            self.screen.blit(text_surface, (x, y))
            self.dirty_rects.append(text_surface.get_rect(topleft=(x, y)))
            self._manage_cache(cache_key)
        except Exception as e:
            print(f"Yazı oluşturma hatası: {e}")

    def fullscreen_size(self):
        display_info = pygame.display.Info()
        return (display_info.current_w, display_info.current_h)

    def mouse_pos(self):
        return pygame.mouse.get_pos()

    def fill(self, color=(255, 0, 0)):
        if self.horror_mode:
            color = tuple(max(min(h + random.randint(-5, 5), 255), 0) for h in color)
        self.pixels[:, :, :] = color[:3]
        self.screen.fill(color[:3])
        self.dirty_rects = [pygame.Rect(0, 0, self.screen_width, self.screen_height)]

    def hide(self):
        if not self.is_hidden:
            pygame.display.iconify()
            self.is_hidden = True

    def unhide(self):
        if self.is_hidden:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF | (pygame.FULLSCREEN if self.is_fullscreen else 0)
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
            self.is_hidden = False
            self.screen.fill(self.pixels[0, 0])
            self.update()

    def fullscreen(self):
        if not self.is_fullscreen:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
            self.is_fullscreen = True
            self.screen.fill(self.pixels[0, 0])
            self.update()

    def floatscreen(self):
        if self.is_fullscreen:
            flags = pygame.HWSURFACE | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
            self.is_fullscreen = False
            self.screen.fill(self.pixels[0, 0])
            self.update()

    def update(self):
        if self.horror_mode and random.random() < 0.05:  # Further reduce frequency
            self.text(
                text=random.choice(list("qwertyuopasdfghjklizxcvbnm")),
                x=random.randint(0, self.screen_width),
                y=random.randint(0, self.screen_height),
                size=random.randint(1, int(self.screen_width / 16))
            )
        if not self.is_hidden:
            if self.dirty_rects:
                pygame.display.update(self.dirty_rects)
                self.dirty_rects = []
                if self.update_count%self.update_optimization == 0:
                    pygame.display.flip()
                self.update_count += 1
            else:
                pygame.display.flip()
                

    def get_events(self):
        pygame.event.pump()
        return pygame.event.get([QUIT, MOUSEBUTTONDOWN, MOUSEWHEEL, KEYDOWN])

    def check_mouse_events(self, events):
        result = {"clicks": [], "scrolls": {"up": 0.0, "down": 0.0}}
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                result["clicks"].append([event.pos, "left" if event.button == 1 else "right"])
            elif event.type == MOUSEWHEEL:
                result["scrolls"]["up" if event.y > 0 else "down"] += abs(event.y) * 100
        return result

    def check_keyboard_events(self, events):
        return [pygame.key.name(event.key) for event in events if event.type == KEYDOWN]

    def run(self):
        running = True
        while running:
            events = self.get_events()
            for event in events:
                if event.type == QUIT:
                    running = False
            self.update()
            if self.clock_obj:
                self.tick()
        pygame.quit()

class ZiplayiverCekirge2_MusicEngine:
	def __init__(self):
		pygame.mixer.init()
		try:
			pygame.mixer.set_num_channels(9999)
		except:
			pygame.mixer.set_num_channels(999)
		self.max_channels = pygame.mixer.get_num_channels()
		self.channels = [pygame.mixer.Channel(i) for i in range(self.max_channels)]
		self.last_used_channel = None
		self.sound_cache = {}
		self.horror_mode = False

	def play_music(self, music_file, volume=1.0, channel=None, loop=False):
		if self.horror_mode:
			volume = 1
		if channel is None:
			channel = self.random_channel()
		if not (0 <= channel < self.max_channels):
			return
		cache_key = (music_file, volume)
		if cache_key in self.sound_cache:
			sound = self.sound_cache[cache_key]
		else:
			try:
				sound = pygame.mixer.Sound(music_file)
				self.sound_cache[cache_key] = sound
			except Exception as e:
				print(f"Müzik yükleme hatası: {e}")
				return
		self.channels[channel].set_volume(volume)
		self.channels[channel].play(sound, loops=-1 if loop else 0)
		self.last_used_channel = channel

	def set_music(self, volume=1.0, channel=None):
		if self.horror_mode:
			volume = 1
		if channel is None:
			channel = self.last_used_channel if self.last_used_channel is not None else self.random_channel()
		if 0 <= channel < self.max_channels:
			self.channels[channel].set_volume(max(0.0, min(1.0, volume)))

	def check_music(self, channel=None):
		if channel is None:
			channel = self.last_used_channel if self.last_used_channel is not None else 0
		if 0 <= channel < self.max_channels:
			return self.channels[channel].get_busy()
		return False

	def stop_music(self, channel=None):
		if channel is None:
			channel = self.last_used_channel if self.last_used_channel is not None else 0
		if 0 <= channel < self.max_channels:
			self.channels[channel].stop()

	def random_channel(self):
		return random.randint(0, self.max_channels - 1)

	def random_unused_channel(self):
		unused_channels = [i for i in range(self.max_channels) if not self.channels[i].get_busy()]
		if unused_channels:
			return random.choice(unused_channels)
		return self.random_channel()

	def play_music_manual(self, hz=450, samplerate=44100, duration=0.1, channel=None, loop=False, volume=1.0):
		if self.horror_mode:
			volume = 1
		if channel is None:
			channel = self.random_unused_channel()
		if not (0 <= channel < self.max_channels):
			return
		cache_key = (hz, samplerate, duration, volume)
		if cache_key in self.sound_cache:
			sound = self.sound_cache[cache_key]
		else:
			try:
				t = np.linspace(0, duration, int(samplerate * duration), False)
				audio_mono = 32767 * np.sin(hz * 2 * np.pi * t) * volume
				audio_mono = audio_mono.astype(np.int16)
				audio_stereo = np.zeros((len(audio_mono), 2), dtype=np.int16)
				audio_stereo[:, 0] = audio_mono
				audio_stereo[:, 1] = audio_mono
				sound = pygame.sndarray.make_sound(audio_stereo)
				self.sound_cache[cache_key] = sound
			except Exception as e:
				print(f"Manuel ses oluşturma hatası: {e}")
				return
		self.channels[channel].set_volume(max(0.0, min(1.0, volume)))
		self.channels[channel].play(sound, loops=-1 if loop else 0)
		self.last_used_channel = channel

	def play_music_manual_zpzkg2(self, data, channel=None, volume=1.0):
		if "\n" in data:
			vars = data[:data.find("\n")]
			melody = data[data.find("\n")+1:]
		else:
			vars = None
			melody = data
		varsdata = {"samplerate": 44100, "duration": 0.2, "volume": volume}
		if vars != None:
			for var in vars.split(","):
				varname = var[:var.find("=")]
				varval = float(var[var.find("=")+1:])
				varsdata[varname] = varval
		if melody != "":
			for m in melody.split(","):
				if channel == None:
					channelt = self.random_unused_channel()
				else:
					channelt = channel
				if "/" in m:
					if m.count("/") == 1:
						hz = m[:m.find("/")]
						if hz in varsdata:
							hz = varsdata[hz]
						else:
							hz = float(hz)
						duration = m[m.find("/")+1:]
						if duration in varsdata:
							duration = varsdata[duration]
						else:
							duration = float(duration)
						duration2 = duration
					elif m.count("/") == 2:
						hz = m[:m.find("/")]
						if hz in varsdata:
							hz = varsdata[hz]
						else:
							hz = float(hz)
						m = m[m.find("/")+1:]
						duration = m[:m.find("/")]
						if duration in varsdata:
							duration = varsdata[duration]
						else:
							duration = float(duration)
						m = m[m.find("/")+1:]
						if m in varsdata:
							duration2 = varsdata[m]
						else:
							duration2 = float(m)
					else:
						raise ValueError("ZPZKG2 Custom Manual Melody can't contain 3 or more high dots per value.")
				else:
					if m in varsdata:
						hz = varsdata[m]
					else:
						hz = float(m)
					duration = varsdata["duration"]
					duration2 = duration
				self.play_music_manual(hz=hz, duration=duration, samplerate=varsdata["samplerate"], channel=channelt, volume=varsdata["volume"])
				time.sleep(duration2)

import difflib
import time
import random
class GameSystem:
	def __init__(self, night):
		if engine.horror_mode:
			night = 6
		else:
			night = max(min(night, 5), 1)
		self.night = night
		if night == 1:
			self.cams = 6
		elif night == 2:
			self.cams  = 7
		elif night >= 3:
			self.cams = 8
		self.cams_data = {}
		for n in range(1, self.cams+1):
			self.cams_data[n] = None
		self.scwer_awake = False
		self.scwer_awake_time = 120/night
		self.battery = 100
		self.battery_down = (0.002)*(night/1.5)
		self.start = time.time()
		self.endtime = 360*2
		self.danger = 0
		self.scwer_come = 0
		self.run = True
	def time(self):
		e = int((time.time()-self.start)/2)
		hour = int(e/60)
		e -= hour*60
		if e < 10:
			return f"{hour}:0{e:.0f}"
		else:
			return f"{hour}:{e:.0f}"
	def process(self):
		global roompanel, scwer
		if time.time()-self.start <= self.endtime:
			if roompanel:
				self.battery -= self.battery_down
			if time.time()-self.start >= self.scwer_awake_time and not self.scwer_awake:
				print("scwer awake")
				self.scwer_awake = True
			for cam in range(1, self.cams+1):
				if cam != 2 and self.cams_data[cam] == None:
					if random.random() <= (1/2000)*(self.night/2.5):
						while True:
							fakec = random.randint(1, self.cams)
							if fakec != 2 and fakec != cam:
								break
						self.cams_data[cam] = (random.choice([
						("changed_color", random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])),
						("crash", None),
						("no_light", None),
						("fake_copy", fakec),
						("high_light", None),
						("blood", random.randint(1, 3)),
						("face", None),
						("broken", None)
						]), time.time())
						print(self.cams_data[cam], cam)
						self.danger += 1
					if self.cams_data[cam] != None:
						if time.time()-self.cams_data[cam][1] >= 120/(self.night/2.5):
							if scwer != None and self.scwer_awake:
								print("scwer spawn 0")
								scwer = random.choice(["left", "right"])
			if self.danger >= int(self.cams/1.5) and self.scwer_awake:
				if scwer == None:
					print("scwer spawn 1", self.danger, int(self.cams/1.5))
					scwer = random.choice(["left", "right"])
			if self.scwer_awake and random.random() < (1/4000)*(self.night/2.5):
				if scwer == None:
					print("scwer spawn 2", self.danger)
					scwer = random.choice(["left", "right"])
			self.danger = max(min(self.danger, int(self.cams)), 0)
		else:
			self.run = False
			return "end"
	def check(self, cam, type):
		if cam == 2:
			pass
		elif self.cams_data[cam] == None:
			self.danger += 1
			return False
		elif self.cams_data[cam][0][0] == type:
			self.danger -= 1
			self.cams_data[cam] = None
			return True
		else:
			self.danger += 1
			return False
	def report_scwer(self, pos):
		global scwer
		if scwer == pos:
			scwer = None
			self.danger -= 1
			return True
		else:
			self.danger += 1
			return False
	def cmd(self, command):
		if command.startswith("report "):
			command = command[7:]
			if command.startswith("room "):
				target = command[5:]
				out = self.report_scwer(target)
				if out:
					return "Successfuly."
				else:
					return "There is no such thing as 'Scwer' here."
			elif command.startswith("camera "):
				try:
					camera = command[7:]
					target = int(camera[:camera.find(" ")])
					type = camera[camera.find(" ")+1:]
					out = self.check(target, type)
					if out:
						return "Successfuly."
					else:
						return "There is no anomaly."
				except Exception as e:
					print(e)
					return "[ Error Invalid Camera Index ]"
			else:
				return "[ Error Invalid Report Type ]"
		else:
			return "[ Error Invalid Command ]"

engine = ZiplayiverCekirge2(title="Scwer")
music_engine = ZiplayiverCekirge2_MusicEngine()

width, height = engine.fullscreen_size()
engine.set_screen(width, height)
engine.fullscreen()
width, height = engine.get_screen()

for n in range(32):
	engine.fill((0, 0, 0))
	engine.image(width=engine.screen_width, height=engine.screen_height, file="Pictures/syshanbur.jpg", alpha=n*4)
	engine.update()
	if "x" in engine.check_keyboard_events(engine.get_events()):
		engine.horror_mode = True
		music_engine.horror_mode = True
for n in range(32):
	engine.fill((0, 0, 0))
	engine.image(width=engine.screen_width, height=engine.screen_height, file="Pictures/syshanbur.jpg", alpha=128-(n*4))
	engine.update()
	if "x" in engine.check_keyboard_events(engine.get_events()):
		engine.horror_mode = True
		music_engine.horror_mode = True
engine.image(width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
engine.clock(75)

scwer = None
last_scwer = None
pos_dr = 0
thick_sounds = music_engine.random_unused_channel()
background_sounds = music_engine.random_unused_channel()
scwer_sounds = music_engine.random_unused_channel()
ambient_musics = music_engine.random_unused_channel()
ambient2_musics = music_engine.random_unused_channel()
roompanel = False
try:
	with open("User Data/night.txt", "r") as f:
		night = int(f.read())
except:
	night = 1
	with open("User Data/night.txt", "w") as f:
		f.write("1")
cam = 1
n2 = 0
def click(n=None):
	if n == None:
		n = random.randint(1, 3)
	music_engine.play_music("Music/click"+str(n)+".mp3")
def menu():
	global scwer, last_scwer, pos_dr, thick_sounds, background_sounds, scwer_sounds, ambient_musics, ambient2_musics, roompanel, night, cam, n2, engine, music_engine, width, height
	roompanel = False
	cam = 1
	n2 = 0
	pos_dr = 0
	scwer = None
	last_scwer = None
	music_engine.stop_music(channel=ambient_musics)
	music_engine.stop_music(channel=ambient2_musics)
	music_engine.stop_music(channel=background_sounds)
	music_engine.stop_music(channel=scwer_sounds)
	music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
	music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
	music_engine.stop_music(thick_sounds)
	music_engine.stop_music(scwer_sounds)
	loadmax = (3*2*3*8)+(10*3)+(4)+(1)
	loaded = 0
	engine.fill((0, 0, 0))
	engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
	engine.text(text="Loading... %0", color=(255, 255, 255), size=40)
	engine.update()
	for bcr in [0.1, 0.5, 1, 0.6, 0.7, 0.8]:
		for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
			ts = []
			for cam in range(1, 9):
				t = threading.Thread(target=engine.image, kwargs={"x": width/6.5, "y": height/5.5, "width": width/1.4, "height": height/1.35, "file": "Pictures/cam"+str(cam)+".png", "brightness": bcr, "color_changer": False, "color": color, "color_force": 64})
				t.start()
				ts.append(t)
				events = engine.get_events()
				engine.tick()
			for t in ts:
				t.join()
				loaded += 1
				engine.fill((0, 0, 0))
				engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
				engine.text(text="Loading... %"+str(int((loaded/loadmax)*100)), color=(255, 255, 255), size=40)
				engine.update()
				engine.tick()
	for n in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
		for n2 in [0, 0.1, -0.1]:
			events = engine.get_events()
			engine.image(file="Pictures/menu.png", width=width, height=height, brightness=round(n+0.3, 1)+n2)
			loaded += 1
			engine.fill((0, 0, 0))
			engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
			engine.text(text="Loading... %"+str(int((loaded/loadmax)*100)), color=(255, 255, 255), size=40)
			engine.update()
			engine.tick()
	for n in range(1, 5):
		engine.image(file="Pictures/vhs"+str(n)+".png", width=width, height=height, alpha=32)
		loaded += 1
		engine.fill((0, 0, 0))
		engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
		engine.text(text="Loading... %"+str(int((loaded/loadmax)*100)), color=(255, 255, 255), size=40)
		engine.update()
	engine.image(x=width/6, y=height/5, width=width/1.5, height=height/1.45, file="Pictures/broken.png", brightness=1, alpha=128)
	loaded += 1
	engine.fill((0, 0, 0))
	engine.text(text="Loading... %"+str(int((loaded/loadmax)*100)), color=(255, 255, 255), size=40)
	engine.update()
	lastex = None
	run = True
	ic = 1
	xmode = 0
	while run:
		if engine.horror_mode:
			night = 6
		music_engine.stop_music(channel=ambient2_musics)
		music_engine.stop_music(channel=scwer_sounds)
		pos_dr = 0
		ic += 1
		engine.fill((0, 0, 0))
		events = engine.get_events()
		clicks = engine.check_mouse_events(events)
		mx, my = engine.mouse_pos()
		n1 = (abs(mx-width)/width)+0.3
		br = round(n1, 1)+random.choice([0, 0.1, -0.1])
		engine.image(file="Pictures/menu.png", width=width, height=height, brightness=br)
		engine.text(text=str(night), size=((height+width)/2)/18, x=width/3.82, y=height/2.73, alpha=br*100, color=(255, 0, 0))
		if mx >= width/19.6:
			if my >= height/4:
				if mx <= (width/19.44)+width/2.95:
					if my <= (height/4)+height/5.1:
						engine.rect(x=width/19.6, y=height/4, width=width/2.95, height=height/5.1, color=(255, 64, 20), alpha=random.randint(16, 52))
						xmode += 1
					else:
						xmode = 0
		if mx >= (width/19.6):
			if my >= (height/2.15):
				if mx <= (width/19.6)+width/2.95:
					if my <= (height/2.15)+height/7.5:
						engine.rect(x=width/19.6, y=height/2.15, width=width/2.95, height=height/7.5, color=(255, 64, 20), alpha=random.randint(16, 52))
		if mx >= (width/19.6):
			if my >= (height/1.625):
				if mx <= (width/19.6)+width/2.95:
					if my <= (height/1.625)+height/7.5:
						engine.rect(x=width/19.6, y=height/1.615, width=width/2.95, height=height/7.55, color=(255, 64, 20), alpha=random.randint(16, 52))
		if mx >= (width/6.9):
			if my >= (height/1.292):
				if mx <= (width/6.9)+width/6.75:
					if my <= (height/1.292)+height/10:
						if lastex == None:
							lastex = time.time()
						ex = max(min((time.time()-lastex), 1.7), 0)/1.7
						engine.rect(width=width, height=height, color=(16, 0, 0), alpha=random.randint(150, 230)*ex)
						engine.rect(x=width/6.9, y=height/1.292, width=width/6.75, height=height/10, color=(255, 32, 32), alpha=random.randint(16, 52)*ex)
					else:
						lastex = None
		for pos, typee in clicks["clicks"]:
			if typee == "left":
				x, y = pos
				if x >= width/19.6:
					if y >= height/4:
						if x <= (width/19.44)+width/2.95:
							if y <= (height/4)+height/5.1:
								music_engine.play_music_manual(hz=400, duration=0.015, volume=0.3)
								for n in range(128):
									engine.rect(width=width, height=height, color=(0, 0, 0), alpha=n)
									engine.update()
									time.sleep(0.02)
								ongame()
				if x >= (width/19.6):
					if y >= (height/2.15):
						if x <= (width/19.6)+width/2.95:
							if y <= (height/2.15)+height/7.5:
								music_engine.play_music_manual(hz=400, duration=0.015, volume=0.3)
								night = 1
								with open("User Data/night.txt", "w") as f:
									f.write("1")
								for n in range(128):
									engine.rect(width=width, height=height, color=(0, 0, 0), alpha=n)
									engine.update()
									time.sleep(0.02)
								ongame()
				if x >= (width/19.6):
					if y >= (height/1.625):
						if x <= (width/19.6)+width/2.95:
							if y <= (height/1.625)+height/7.5:
								music_engine.play_music_manual(hz=400, duration=0.015, volume=0.3)
								pass
				if x >= (width/6.9):
					if y >= (height/1.292):
						if x <= (width/6.9)+width/6.75:
							if y <= (height/1.292)+height/10:
								music_engine.play_music_manual(hz=400, duration=0.015, volume=0.3)
								run = False
		engine.image(file="Pictures/vhs"+str((ic%4)+1)+".png", width=width, height=height, alpha=32)
		engine.update()
		for event in events:
			if event.type == QUIT:
				sysm.exit()
		engine.tick()

def bg_processor(sys):
	global process_end
	while process_end != "end" and sys.run:
		process_end = sys.process()
		time.sleep(1/20)

process_end = None

def ongame():
	global scwer, last_scwer, pos_dr, thick_sounds, background_sounds, scwer_sounds, ambient_musics, ambient2_musics, roompanel, night, cam, n2, engine, music_engine, width, height, process_end
	music_engine.stop_music(channel=ambient_musics)
	music_engine.play_music(music_file="Music/ongame.mp3", channel=ambient_musics, loop=True)
	if night >= 3:
		music_engine.play_music(music_file="Music/ongame2.mp3", channel=ambient2_musics, loop=True, volume=0.2)
	for n in range(64):
		engine.get_events()
		engine.image(file="Pictures/room.jpg", width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=0.2)
		engine.rect(width=width, height=height, color=(0, 0, 0), alpha=255-(n*4))
		engine.update()
		engine.tick()
		time.sleep(1/40)
		engine.image(file="Pictures/room.jpg", width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0)
		engine.rect(width=width, height=height, color=(0, 0, 0), alpha=255-(n*4))
		engine.update()
		engine.tick()
		time.sleep(1/40)
	ic = 1
	for _ in range(8):
		engine.get_events()
		engine.image(file="Pictures/room.jpg", width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=0.2)
		engine.update()
		ic += 1
		time.sleep(ic*0.01)
		engine.image(file="Pictures/room.jpg", width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0)
		engine.update()
		ic += 1
		time.sleep(ic*0.01)
	engine.image(file="Pictures/room.jpg", width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0)
	sys = GameSystem(night)
	ic = 1
	camcom = ""
	camcomout = ""
	camerapanel = False
	load_last = False
	scwer = None
	last_scwer = None
	pod_dr = None
	roompanel = False
	cam = 1
	momentum = 0
	drs = 375
	fps_ends = None
	camreport = False
	lastcamreport = 0
	lastreportroom = 0
	jc_type = None
	adminterminaled = False
	process_end = None
	bgt = threading.Thread(target=bg_processor, args=(sys,))
	bgt.start()
	while True:
		fps_start = time.time()
		ic += 1
		if process_end == "end":
			night2 = night
			if night == 1:
				comt = "We noticed your presence."
			elif night == 2:
				comt = "It won't be that easy."
			elif night == 3:
				comt = "We don't want you to leave us like he did."
			elif night == 4:
				comt = "Take a look at the picture in your palm."
			elif night == 5:
				comt = "..."
			if night < 5 and not engine.horror_mode:
				with open("User Data/night.txt", "w") as f:
					f.write(str(night+1))
				night = night+1
			music_engine.stop_music(channel=ambient_musics)
			music_engine.stop_music(channel=ambient2_musics)
			music_engine.stop_music(channel=background_sounds)
			music_engine.stop_music(channel=scwer_sounds)
			engine.fill((0, 0, 0))
			music_engine.play_music(channel=ambient_musics, music_file="Music/finish.mp3", volume=2, loop=False)
			engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
			engine.text(size=64, x=width/2.35, y=height/2.25, text="Night Finished.")
			engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
			engine.text(text=comt, size=40, color=(255, 255, 255), alpha=16, y=height/1.1)
			engine.update()
			while len(engine.check_keyboard_events(engine.get_events())) == 0:
				engine.fill((0, 0, 0))
				engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.6)
				engine.text(size=64, x=width/2.35, y=height/2.25, text="Night Finished.")
				engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
				engine.text(text=comt, size=40, color=(255, 255, 255), alpha=16, y=height/1.05)
				time.sleep(0);engine.update()
			music_engine.play_music_manual(hz=200, duration=0.2, loop=True, volume=0.3, channel=background_sounds)
			while len(engine.check_keyboard_events(engine.get_events())) == 0:
				ic += 1
				engine.fill((0, 0, 0))
				engine.image(file="Pictures/story"+str(night2)+".png", width=width, height=height, brightness=0.7, saturation=0.5)
				engine.image(file="Pictures/vhs"+str(((ic+3)%4)+1)+".png", width=width, height=height, alpha=128)
				time.sleep(0);engine.update()
			if night == 5:
				drs = 700
				while len(engine.check_keyboard_events(engine.get_events())) == 0:
					ic += 1
					engine.fill((0, 0, 0))
					engine.image(file="Pictures/scwerzal.png", width=width/2, height=height, x=width/4)
					engine.text(text="Please... save me from Zreheal'Zal...", size=64)
					engine.image(file="Pictures/vhs"+str(((ic+3)%4)+1)+".png", width=width, height=height, alpha=256)
					time.sleep(0);engine.update()
				zal = None
				zalh = 64
				playerh = 6
				pos_dr = 0
				momentum = 0
				drs = 80
				reloading = None
				ammo = 6
				lastshot = 0
				lastcome = time.time()
				music_engine.play_music(music_file="Music/ongame.mp3", volume=0.1, channel=ambient_musics)
				music_engine.play_music_manual(hz=180, volume=0.3, channel=background_sounds, duration=5, loop=True)
				while True:
					if reloading != None:
						if time.time()-reloading >= 2:
							reloading = None
							ammo = 6
					if playerh <= 0:
						music_engine.play_music("Music/jc.mp3")
						engine.fill((0, 0, 0))
						engine.image(file="Pictures/zrehealzal.png", width=width, height=height)
						engine.update()
						for _ in range(16):
							music_engine.play_music("Music/jc.mp3")
						time.sleep(4)
						engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
						while len(engine.check_keyboard_events(engine.get_events())) == 0:
							time.sleep(0);engine.update()
						break
					if zalh <= 0:
						while len(engine.check_keyboard_events(engine.get_events())) == 0:
							ic += 1
							engine.fill((0, 0, 0))
							engine.image(file="Pictures/storyend.png", width=width, height=height, brightness=0.7, saturation=0.5)
							engine.image(file="Pictures/vhs"+str(((ic+3)%4)+1)+".png", width=width, height=height, alpha=128)
							time.sleep(0);engine.update()
						return
					engine.fill((0, 0, 0))
					pos_dr += random.randint(-1, 1)
					events = engine.get_events()
					pkeys = engine.check_keyboard_events(events)
					clicks = engine.check_mouse_events(events)
					bg = "Pictures/room.jpg"
					if zal == "left":
						bg = "Pictures/room_zrehealzal_left.png"
					elif zal == "right":
						bg = "Pictures/room_zrehealzal_right.png"
					if random.random() <= 1/230 and time.time()-lastcome >= 0.3:
						if zal != None:
							playerh -= 1
							music_engine.play_music("Music/jc.mp3", volume=0.05)
						zal = random.choice(["left", "right"])
						lastcome = time.time()
					engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0)
					engine.text(text="Zreheal'Zal", x=width/2.2, color=(255, 255, 255), size=40)
					engine.rect(x=width/4, y=40, color=(255, 255, 255), width=width/2, alpha=128)
					engine.rect(x=width/4, y=40, color=(255, 0, 0), width=int((zalh/64)*(width/2)), alpha=128)
					tts = random.uniform(-(6-playerh), (6-playerh))
					engine.text(text="You", x=(width/2.02)+tts, color=(255, 255, 255), size=40, y=height/1.1)
					engine.rect(x=int((width/2.5)+tts), y=height/1.05, color=(255, 255, 255), width=int(width/4.5), alpha=128)
					engine.rect(x=int((width/2.5)+tts), y=height/1.05, color=(0, 255, 0), width=abs((playerh/6)*(width/4.5)), alpha=128)
					mx, my = engine.mouse_pos()
					used1 = False
					if mx >= ((width/2)+width)/2:
						pos_dr -= width/drs
						momentum -= width/drs
						used1 = True
					elif mx <= width-((width/2)+width)/2:
						pos_dr += width/drs
						momentum += width/drs
						used1 = True
					if keyboard.is_pressed("left") and not used1:
						pos_dr += width/drs
						momentum += width/drs
					if keyboard.is_pressed("right") and not used1:
						pos_dr -= width/drs
						momentum -= width/drs
					pos_dr += momentum/5.5
					pos_dr = max(min(pos_dr, width/4), -(width/4))
					momentum = momentum/1.1
					if reloading == None:
						for pos, typee in clicks["clicks"]:
							if typee == "left":
								mx, my = pos
								music_engine.play_music("Music/gun_shot.mp3")
								if zal == "left" and mx <= width-((width/2)+width)/2:
									zal = None
									zalh -= 1
								elif zal == "right" and mx >= ((width/2)+width)/2:
									zal = None
									zalh -= 1
								ammo -= 1
								lastshot = time.time()
							if ammo <= 0:
								break
					if ammo <= 0 and not reloading:
						reloading = time.time()
						if random.random() >= 0.5:
							music_engine.play_music("Music/gun_load.mp3")
						else:
							music_engine.play_music("Music/gun_load2.mp3")
					engine.rect(width=int(width), height=int(height), color=(255, 255, 200), alpha=max(min(int((1-((time.time()-lastshot)/0.2))*255), 255), 0))
					engine.update()
					playerh += 1/2048
					playerh = max(min(playerh, 6), 0)
					engine.tick()
					
			music_engine.stop_music(channel=ambient_musics)
			music_engine.stop_music(channel=background_sounds)
			music_engine.stop_music(channel=scwer_sounds)
			music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
			music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
			music_engine.stop_music(thick_sounds)
			music_engine.stop_music(scwer_sounds)
			break
		engine.fill((0, 0, 0))
		if scwer != None and last_scwer == None and jc_type == None:
			last_scwer = time.time()
			jc_type = random.randint(1, 2)
		if random.random() < (1/20 if scwer != None else 1/40):
			n = 0.2
			music_engine.play_music_manual(hz=13000, duration=0.015, channel=thick_sounds, volume=0.15)
			music_engine.play_music_manual(hz=11000, duration=0.015, channel=thick_sounds, volume=0.15)
		else:
			n = 1
		if sys.battery <= 0:
			n = 0.2
			if roompanel:
				music_engine.play_music("Music/close.mp3")
				for n2 in ([int(height/n3) for n3 in range(1, 11)]):
							engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
							engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
							engine.update()
							engine.tick()
				roompanel = False
		music_engine.stop_music(channel=scwer_sounds)
		if scwer != None:
			music_engine.play_music_manual(hz=230, duration=5, channel=scwer_sounds, loop=True, volume=0.25)
		bg = "Pictures/room.jpg"
		if scwer == "left":
			particles = abs(pos_dr-(width/1.5))
			bg = "Pictures/room_left_scwer.jpg"
		elif scwer == "right":
			particles = abs(pos_dr-(-width/1.5))
			bg = "Pictures/room_right_scwer.jpg"
		else:
			last_scwer = None
			jc_type = None
			particles = 0
		pos_dr = max(min(pos_dr, width/4), -(width/4))
		engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
		engine.text(x=width-(40*2), text=sys.time(), color=(255, 255, 255), alpha=128, size=40)
		events = engine.get_events()
		pkeys = engine.check_keyboard_events(events)
		clicks = engine.check_mouse_events(events)
		taps = engine.check_keyboard_events(events)
		used1 = False
		mov = None
		if not roompanel:
			mx, my = engine.mouse_pos()
			mov = None
			if mx >= ((width/2)+width)/2:
				pos_dr -= width/drs
				momentum -= width/drs
				used1 = True
				mov = "right"
			elif mx <= width-((width/2)+width)/2:
				pos_dr += width/drs
				momentum += width/drs
				used1 = True
				mov = "left"
		if abs(pos_dr) <= width/5 and not roompanel:
			if last_scwer != None and time.time()-last_scwer >= 60/night:
				pass
			else:
				engine.rect(x=width/2.5, y=int(height/1.2)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=24)
				engine.text(x=width/2.5, y=int(height/1.2), text="[ Open Room Panel ]", size=width/34, color=(255, 255, 255), alpha=50)
				for pos, typee in clicks["clicks"]:
					if typee == "left":
						x, y = pos
						if x >= width/2.5:
							if x <= ((width/93)*19)+(width/2.5):
								if y >= (height/1.2)-4:
									if y <= (width/37)+((height/1.2)-4):
										music_engine.play_music("Music/open.mp3")
										for n2 in ([int(height/n3) for n3 in range(1, 11)])[::-1]:
											engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
											engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
											engine.update()
											engine.tick()
										roompanel = True
		else:
			if last_scwer == None or time.time()-last_scwer <= 60/night:
				if time.time()-lastreportroom >= 3:
					if pos_dr >= width/5:
						engine.rect(x=(width-(width/1.3))-((width/93)*17), y=22, width=(width/93)*17, height=width/39, color=(255, 255, 255), alpha=24)
						engine.text(x=(width-(width/1.3))-((width/93)*17), y=25, text="[ Report Anomaly ]", size=width/34, color=(255, 255, 255), alpha=50)
						for pos, typee in clicks["clicks"]:
							if typee == "left":
								mx, my = pos
								if mx >= (width-(width/1.3))-((width/93)*17):
									if my >= 22:
										if mx <= ((width-(width/1.3))):
											if my <= 22+(width/39):
												if sys.report_scwer("left"):
													engine.rect(x=(width-(width/1.3))-((width/93)*17), y=22, width=(width/93)*17, height=width/39, color=(0, 255, 0), alpha=32)
													music_engine.play_music_manual(hz=3000, duration=0.01, volume=0.3)
												else:
													engine.rect(x=(width-(width/1.3))-((width/93)*17), y=22, width=(width/93)*17, height=width/39, color=(255, 0, 0), alpha=32)
													music_engine.play_music_manual(hz=1500, duration=0.015, volume=0.3)
												lastreportroom = time.time()
					elif pos_dr <= -(width/5):
						engine.rect(x=width/1.3, y=22, width=(width/93)*17, height=width/37, color=(255, 255, 255), alpha=24)
						engine.text(x=width/1.3, y=25, text="[ Report Anomaly ]", size=width/34, color=(255, 255, 255), alpha=50)
						for pos, typee in clicks["clicks"]:
							if typee == "left":
								mx, my = pos
								if mx >= width/1.3:
									if my >= 22:
										if mx <= (width/1.3)+(width/93)*17:
											if my <= 22+(width/39):
												if sys.report_scwer("right"):
													engine.rect(x=width/1.3, y=22, width=(width/93)*17, height=width/37, color=(0, 255, 0), alpha=32)
													music_engine.play_music_manual(hz=3000, duration=0.01, volume=0.3)
												else:
													engine.rect(x=width/1.3, y=22, width=(width/93)*17, height=width/37, color=(255, 0, 0), alpha=32)
													music_engine.play_music_manual(hz=1500, duration=0.015, volume=0.3)
												lastreportroom = time.time()
				else:
					if pos_dr >= width/5:
						engine.rect(x=(width-(width/1.3))-((width/93)*20), y=22, width=(width/93)*20, height=width/39, color=(255, 255, 255), alpha=16)
						engine.text(x=(width-(width/1.3))-((width/93)*20), y=25, text="[ Reporting Anomaly ]", size=width/34, color=(255, 255, 255), alpha=32)
					elif pos_dr <= -(width/5):
						engine.rect(x=width/1.3, y=22, width=(width/93)*20, height=width/37, color=(255, 255, 255), alpha=16)
						engine.text(x=width/1.3, y=25, text="[ Reporting Anomaly ]", size=width/34, color=(255, 255, 255), alpha=32)
		for _ in range(int(particles/10)):
			engine.rect(x=random.randint(0, width), y=random.randint(0, height), color=tuple([random.randint(0, 255)]*3), width=random.randint(1, 7), height=random.randint(1, 7), alpha=random.randint(0, 75))
		if particles != 0:
			engine.rect(x=0, y=0, width=width, height=height, alpha=random.randint(int(particles/(width/64)), int(particles/(width/128))), color=(0, 0, 0))
		if scwer != None and last_scwer != None:
			if time.time()-last_scwer >= 30/night:
				music_engine.play_music_manual(hz=250, duration=5, channel=scwer_sounds, loop=True, volume=0.3)
				if scwer == "left":
					momentum += random.randint(-12, int(width/40))
				else:
					momentum += random.randint(-int(width/40), 12)
		music_engine.stop_music(channel=scwer_sounds)
		if scwer != None:
			music_engine.play_music_manual(hz=230, duration=5, channel=scwer_sounds, loop=True, volume=0.2)
		if roompanel:
			if camerapanel:
				bcr = round(random.uniform(0.6, 0.8), 1)
				color_changer = False
				color = (0, 0, 0)
				crash = False
				aa = 255
				if sys.cams_data[cam] != None:
					if sys.cams_data[cam][0][0] == "crash":
						crash = True
						aa = 0
					elif sys.cams_data[cam][0][0] == "no_light":
						bcr = 0.2
					elif sys.cams_data[cam][0][0] == "high_light":
						bcr = 5
					elif sys.cams_data[cam][0][0] == "changed_color":
						color_changer = True
						color = sys.cams_data[cam][0][1]
				if cam == 2 and sys.scwer_awake:
					engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/cam2a.png", brightness=round(random.uniform(0.5, 0.8), 1))
				else:
					if not crash:
						engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/cam"+str(cam)+".png", brightness=bcr, color_changer=color_changer, color=color, color_force=64)
					else:
						engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=round(random.uniform(0.5, 0.8), 1))
				if sys.cams_data[cam] != None:
					if sys.cams_data[cam][0][0] == "face":
						engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/scwer.jpg", brightness=1, alpha=128)
					elif sys.cams_data[cam][0][0] == "broken":
						engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/broken.png", brightness=1, alpha=180)
					elif sys.cams_data[cam][0][0] == "blood":
						engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/blood"+str(sys.cams_data[cam][0][1])+".png", brightness=1, alpha=180)
					elif sys.cams_data[cam][0][0] == "fake_copy":
						engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/cam"+str(sys.cams_data[cam][0][1])+".png", brightness=bcr, alpha=aa)
				engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/vhs"+str((ic%4)+1)+".png", alpha=128)
				engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet2.png", brightness=round(random.uniform(0.5, 0.8), 1))
				engine.rect(x=width/2.5, y=int(height/1.075)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=24)
				engine.text(x=width/2.5, y=int(height/1.075), text="[ Close Room Panel ]", size=width/34, color=(255, 255, 255), alpha=50)
				cam = max(min(cam, sys.cams), 1)
				engine.text(size=36, color=(255, 255, 255), alpha=128, text="Change camera with arrows.", x=width/6.3, y=height/5)
				engine.text(size=36, color=(255, 255, 255), alpha=128, text="Current Camera: "+str(cam), x=width/6.3, y=(height/5)+36)
				engine.text(size=24, color=(255, 255, 255), alpha=128, text="Press space for quit camera system", x=width/6.3, y=(height/5)+(36*2))
				if "left" in pkeys and cam > 1:
					music_engine.play_music_manual(hz=6000, duration=0.01)
					engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=round(random.uniform(0.5, 0.8), 1))
					cam -= 1
				elif "right" in pkeys and cam < sys.cams:
					music_engine.play_music_manual(hz=6500, duration=0.01)
					engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=round(random.uniform(0.5, 0.8), 1))
					cam += 1
				engine.rect(x=width/2.5, y=int(height/1.075)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=24)
				engine.text(x=width/2.5, y=int(height/1.075), text="[ Close Room Panel ]", size=width/34, color=(255, 255, 255), alpha=50)
				if "space" in pkeys:
					camerapanel = False
					engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=round(random.uniform(0.5, 0.8), 1))
					engine.rect(x=width/2.5, y=int(height/1.075)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=24)
					engine.text(x=width/2.5, y=int(height/1.075), text="[ Close Room Panel ]", size=width/34, color=(255, 255, 255), alpha=50)
				engine.text(size=36, color=(255, 255, 255), alpha=128, text="ENERGY: "+str(round(sys.battery, 1)), x=width/1.33, y=height/5)
				if time.time()-lastcamreport >= 3:
					if not camreport:
						engine.rect(x=width/1.5, y=int(height/1.2)-4, width=(width/93)*16, height=width/37, color=(255, 255, 255), alpha=24)
						engine.text(x=width/1.5, y=int(height/1.2), text="[ Report Camera ]", size=width/34, color=(255, 255, 255), alpha=50)
						for pos, typee in clicks["clicks"]:
							if typee == "left":
								mx, my = pos
								if mx >= width/1.5:
									if my >= int(height/1.2)-4:
										if mx <= (width/1.5)+((width/93)*16):
											if my <= (int(height/1.2)-4)+(width/37):
												camreport = True
					else:
						engine.rect(x=width/1.5, y=int(height/1.2)-4, width=(width/93)*16, height=width/37, color=(255, 255, 255), alpha=24)
						engine.text(x=width/1.5, y=int(height/1.2), text="[ Quit Reporting ]", size=width/34, color=(255, 255, 255), alpha=50)
						for pos, typee in clicks["clicks"]:
							if typee == "left":
								mx, my = pos
								if mx >= width/1.5:
									if my >= int(height/1.2)-4:
										if mx <= (width/1.5)+((width/93)*16):
											if my <= (int(height/1.2)-4)+(width/37):
												camreport = False
						typees = {
						"Changed Colors": "changed_color", "Crash No-Screen": "crash", "No Lights": "no_light",
						"High Lights": "high_light", "Fake Copy": "fake_copy", "Blood Screen": "blood",
						"Face": "face", "Broken Screen": "broken"
						}
						starty = int(height/4.8)
						for name, typee in typees.items():
							engine.rect(x=(width/2.5)-4, y=starty-8, width=((width/93)*19)+8, height=(width/37)+8, color=(0, 0, 0), alpha=80)
							engine.rect(x=width/2.5, y=starty-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=32)
							engine.text(x=(((width/2.5)+((width/93)*19)/2.7))-(len(name)*(width/300)), y=starty, text=name, size=width/34, color=(255, 255, 255), alpha=50)
							mx, my = engine.mouse_pos()
							if mx >= width/2.5:
								if my >= starty-4:
									if mx <= (width/2.5)+((width/93)*19):
										if my <= (starty-4)+(width/37):
											engine.rect(x=width/2.5, y=starty-4, width=(width/93)*19, height=width/37, color=(255, 255, 0), alpha=24)
							for pos, typeee in clicks["clicks"]:
								if typeee == "left":
									mx, my = pos
									if mx >= width/2.5:
										if my >= starty-4:
											if mx <= (width/2.5)+((width/93)*19):
												if my <= (starty-4)+(width/37):
													if sys.check(cam, typee):
														engine.rect(x=width/2.5, y=starty-4, width=(width/93)*19, height=width/37, color=(0, 255, 0), alpha=24)
														music_engine.play_music_manual(hz=3000, duration=0.01, volume=0.3)
													else:
														engine.rect(x=width/2.5, y=starty-4, width=(width/93)*19, height=width/37, color=(255, 0, 0), alpha=24)
														music_engine.play_music_manual(hz=1500, duration=0.015, volume=0.3)
													camreport = False
													lastcamreport = time.time()
							starty += (width/37)+42
				else:
					engine.rect(x=width/1.6, y=int(height/1.2)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=16)
					engine.text(x=width/1.6, y=int(height/1.2), text="[ Reporting Camera ]", size=width/34, color=(255, 255, 255), alpha=32)
						
			else:
				engine.rect(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, color=(0, 0, 0))
				engine.text(size=36, alpha=255, text="Room and Security Control Panel (Terminal)", x=width/6.3, y=height/5, color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="Terminal Commands:", x=width/6.3, y=(height/5)+36, color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="camsys = Open Camera Control System", x=width/6.3, y=(height/5)+(36*3), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="report camera <camera_index_number> <anomaly_type> = Report Camera Anomaly Activity", x=width/6.3, y=(height/5)+(36*4), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="report room <left/right> = Report Anomaly In Security Room", x=width/6.3, y=(height/5)+(36*5), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="Anomaly Types: changed_color,crash,no_light,high_light,fake_copy,blood,face,broken", x=width/6.3, y=(height/5)+(36*7), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="changed_color = When camera vision colors changed to Red, Green or Blue.", x=width/6.3, y=(height/5)+(36*9), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="crash = When the camera crashes or shuts down", x=width/6.3, y=(height/5)+(36*10), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="no_light = When light level in the camera image is too low or dark.", x=width/6.3, y=(height/5)+(36*11), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="high_light = When light level in the camera image is too high.", x=width/6.3, y=(height/5)+(36*12), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="fake_copy = When camera view shows another camera view.", x=width/6.3, y=(height/5)+(36*13), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="blood = When a bloodstain obscuring the camera view", x=width/6.3, y=(height/5)+(36*14), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="face = When a 'Face' obscuring the camera view", x=width/6.3, y=(height/5)+(36*15), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text="broken = When the camera lens breaks", x=width/6.3, y=(height/5)+(36*16), color=(0, 250, 0))
				engine.text(size=36, alpha=255, text=">>> "+camcom, x=width/6.3, y=(height/5)+(36*18), color=(0, 250, 0))
				for key in pkeys:
					if key == "-":
						key = "_"
					if key == "return":
						click(2)
						if camcom == "camsys":
							camerapanel = True
							camcom = ""
						elif camcom != "":
							camcomout = sys.cmd(camcom)
							camcom = ""
							engine.text(size=36, alpha=255, text="Loading...", x=width/6.3, y=(height/5)+(36*19), color=(0, 250, 0))
							time.sleep(0.05)
							load_last = True
					elif key == "backspace":
						click(3)
						camcom = camcom[:-1]
					elif key == "space":
						click(2)
						camcom += " "
					elif len(key) == 1:
						click(1)
						camcom += key
				if not load_last:
					engine.text(size=36, alpha=255, text=camcomout, x=width/6.3, y=(height/5)+(36*19), color=(0, 250, 0))
				load_last = False
				camcom = camcom[:32]
				engine.image(x=width/6.5, y=height/5.5, width=width/1.4, height=height/1.35, file="Pictures/vhs"+str((ic%4)+1)+".png", alpha=180)
				engine.image(x=width/10, y=height/10, width=width/1.25, height=height/1.1, file="Pictures/tablet2.png", brightness=round(random.uniform(0.5, 0.8), 1))
				engine.rect(x=width/2.5, y=int(height/1.075)-4, width=(width/93)*19, height=width/37, color=(255, 255, 255), alpha=24)
				engine.text(x=width/2.5, y=int(height/1.075), text="[ Close Room Panel ]", size=width/34, color=(255, 255, 255), alpha=50)
				engine.text(size=36, color=(255, 255, 255), alpha=128, text="ENERGY: "+str(round(sys.battery, 1)), x=width/1.33, y=height/5)
			for pos, typee in clicks["clicks"]:
				if typee == "left":
					x, y = pos
					if x >= width/2.5:
						if x <= ((width/93)*19)+(width/2.5):
							if y >= (height/1.075)-4:
								if y <= (width/37)+((height/1.075)-4):
									music_engine.play_music("Music/close.mp3")
									for n2 in [int(height/n3) for n3 in range(1, 10)]:
										engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
										engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
										engine.update()
										engine.tick()
									roompanel = False
		else:
			if keyboard.is_pressed("left") and not used1:
				pos_dr += width/drs
				momentum += width/drs
			if keyboard.is_pressed("right") and not used1:
				pos_dr -= width/drs
				momentum -= width/drs
			if "c" in pkeys:
				roompanel = True
				music_engine.play_music("Music/open.mp3")
				for n2 in [int(height/n3) for n3 in range(1, 10)][::-1]:
					engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
					engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
					engine.update()
					engine.tick()
				camerapanel = True
		pos_dr += momentum/5.5
		momentum = momentum/1.1
		if abs(pos_dr) <= width/5:
			if "up" in pkeys and not roompanel:
				music_engine.play_music("Music/open.mp3")
				for n2 in [int(height/n3) for n3 in range(1, 10)][::-1]:
					engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
					engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
					engine.update()
					engine.tick()
				roompanel = True
			if "down" in pkeys and roompanel:
				music_engine.play_music("Music/close.mp3")
				for n2 in [int(height/n3) for n3 in range(1, 10)]:
					engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
					engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
					engine.update()
					engine.tick()
				roompanel = False
		if scwer != None and last_scwer != None and jc_type != None:
			if lastroompanelonscwer == None:
				if roompanel:
					lastroompanelonscwer = True
				else:
					lastroompanelonscwer = False
			if jc_type == 1:
				if time.time()-last_scwer >= 60/night:
					if roompanel:
						music_engine.play_music("Music/close.mp3")
						for n2 in [int(height/n3) for n3 in range(1, 10)]:
											engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
											engine.image(x=width/10, y=((height/10)+((int(height))-n2)), width=width/1.25, height=height/1.1, file="Pictures/tablet.png", brightness=0.65)
											engine.update()
											engine.tick()
						roompanel = False
					music_engine.stop_music(channel=ambient_musics)
					music_engine.play_music_manual(hz=260, duration=5, channel=scwer_sounds, loop=True, volume=0.4)
					a = abs(((60/night)-abs(time.time()-last_scwer))*(night*16))
					if a >= 255:
						engine.rect(x=0, y=0, color=(0, 0, 0), width=width, height=height, alpha=255)
						engine.update()
						music_engine.play_music_manual_zpzkg2("q=400,w=420,e=430,r=460,d=0.4,duration=0.1,volume=0.4\nq/d/d,q/d/d,w/0.2/d,w/d/d,q/d/d,q/d/d,e/d/d,w/d/d,q/d/d,q/d/d,w/0.2/d,w/d/d,q/d/d,q,q/d/d,e/d/d,w/d/d,q/d/d", channel=background_sounds)
						engine.image(file=bg, width=int(width*1.5), height=height, x=int(pos_dr-(width/4)), y=0, brightness=n)
						engine.image(file="Pictures/scwer.jpg", width=width, height=height, x=0, contrast=2, brightness=0.7, alpha=160)
						engine.fill((0, 0, 0))
						if random.random() >= 0.5:
							time.sleep(random.randint(3, 5))
						for _ in range(3):
							music_engine.play_music(music_file="Music/jc.mp3")
						engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.3)
						for _ in range(2):
							music_engine.play_music(music_file="Music/jc.mp3")
						engine.image(file="Pictures/scwer.jpg", width=width, height=height, x=0, contrast=2, brightness=0.7, alpha=160)
						for _ in range(4):
							music_engine.play_music(music_file="Music/jc.mp3")
							time.sleep(1/40)
						engine.update()
						time.sleep(3)
						engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
						while len(engine.check_keyboard_events(engine.get_events())) == 0:
							time.sleep(0);engine.update()
						music_engine.stop_music(channel=ambient_musics)
						music_engine.stop_music(channel=background_sounds)
						music_engine.stop_music(channel=scwer_sounds)
						music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
						music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
						music_engine.stop_music(thick_sounds)
						music_engine.stop_music(scwer_sounds)
						break
					engine.rect(width=width, height=height, alpha=max(min(a, 255), 0), color=(0, 0, 0))
			else:
				if time.time()-last_scwer >= 40/night:
					for _ in range(3):
						music_engine.play_music(music_file="Music/jc.mp3")
					engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.3)
					for _ in range(2):
						music_engine.play_music(music_file="Music/jc.mp3")
					engine.image(file="Pictures/scwer.jpg", width=width, height=height, x=0, contrast=2, brightness=0.7, alpha=160)
					for _ in range(4):
						music_engine.play_music(music_file="Music/jc.mp3")
						time.sleep(1/40)
					engine.update()
					time.sleep(3)
					engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
					while len(engine.check_keyboard_events(engine.get_events())) == 0:
						time.sleep(0);engine.update()
					music_engine.stop_music(channel=ambient_musics)
					music_engine.stop_music(channel=background_sounds)
					music_engine.stop_music(channel=scwer_sounds)
					music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
					music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
					music_engine.stop_music(thick_sounds)
					music_engine.stop_music(scwer_sounds)
					break
				elif not roompanel and lastroompanelonscwer and time.time()-last_scwer >= 15/night:
					for _ in range(3):
						music_engine.play_music(music_file="Music/jc.mp3")
					engine.image(file="Pictures/room.jpg", width=width, height=height, brightness=0.3)
					for _ in range(2):
						music_engine.play_music(music_file="Music/jc.mp3")
					engine.image(file="Pictures/scwer.jpg", width=width, height=height, x=0, contrast=2, brightness=0.7, alpha=160)
					for _ in range(4):
						music_engine.play_music(music_file="Music/jc.mp3")
						time.sleep(1/40)
					engine.update()
					time.sleep(3)
					engine.text(text="Press a button for exit.", size=40, color=(255, 255, 255), alpha=170)
					while len(engine.check_keyboard_events(engine.get_events())) == 0:
						time.sleep(0);engine.update()
					music_engine.stop_music(channel=ambient_musics)
					music_engine.stop_music(channel=background_sounds)
					music_engine.stop_music(channel=scwer_sounds)
					music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
					music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
					music_engine.stop_music(thick_sounds)
					music_engine.stop_music(scwer_sounds)
					break
		else:
			lastroompanelonscwer = None
		fps_end = time.time()-fps_start
		if fps_ends == None:
			fps_ends = fps_end
		else:
			fps_ends = (fps_ends+fps_end)/2
		fps = int(1/(fps_ends))
		engine.text(text=f"FPS {fps}", alpha=4, size=30, color=(0, 255, 0))
		engine.text(text=f"NIGHT {night}", alpha=4, size=30, y=30, color=(0, 255, 0))
		engine.text(text=f"ATER {adminterminaled}", alpha=4, size=30, y=60, color=(0, 255, 0))
		engine.update()
		if "escape" in pkeys:
			music_engine.stop_music(channel=ambient_musics)
			music_engine.stop_music(channel=ambient2_musics)
			music_engine.stop_music(channel=background_sounds)
			music_engine.stop_music(channel=scwer_sounds)
			music_engine.play_music(music_file="Music/menu.mp3", channel=ambient_musics, loop=True)
			music_engine.play_music_manual(hz=180, duration=1, channel=background_sounds, loop=True, volume=0.3)
			music_engine.stop_music(thick_sounds)
			music_engine.stop_music(scwer_sounds)
			break
		for event in events:
			if event.type == QUIT:
				sysm.exit()
		engine.tick()

menu()