#!/usr/bin/env python3
"""Tourmaline Ring — neon rotating-paddle interceptor for ElbowOS."""
import argparse, math, os, random, subprocess, sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "TOURMALINE RING"
HANDLE = "x.com/ElbowOS"
CX, CY = W // 2, H // 2 + 40
CORE_R, RING_R, PAD_W, PAD_ARC = 54, 280, 28, 0.38
PAL = {
    "bg0": (8, 4, 18),
    "bg1": (28, 8, 42),
    "ink": (16, 6, 32),
    "ring": (255, 92, 168),
    "pad": (80, 255, 196),
    "core": (255, 210, 70),
    "ice": (240, 230, 255),
    "rose": (255, 70, 140),
    "teal": (40, 230, 220),
    "vio": (170, 90, 255),
    "gold": (255, 196, 64),
    "dim": (140, 110, 170),
}
GEM = [PAL["rose"], PAL["teal"], PAL["vio"], PAL["gold"], PAL["pad"], PAL["ring"]]


class Game:
    def __init__(self, auto=False):
        self.auto = auto
        self.t = self.score = self.hits = self.miss = 0
        self.ang = 0.0
        self.spin = 0.0
        self.hp = 5
        self.flash = 0
        self.shards = []
        self.sparks = []
        self.motes = [
            (random.randrange(W), random.randrange(H), random.randint(1, 3), random.choice(GEM))
            for _ in range(70)
        ]
        for _ in range(6):
            self._spawn()

    def _spawn(self):
        a = random.random() * 6.283
        dist = random.uniform(620, 860)
        spd = random.uniform(5.2, 8.8)
        self.shards.append({
            "a": a, "d": dist, "spd": spd,
            "col": random.choice(GEM), "r": random.randint(14, 22),
            "wob": random.random() * 6.28,
        })

    def _burst(self, x, y, col, n=16):
        for _ in range(n):
            th = random.random() * 6.283
            s = random.uniform(2.0, 10.0)
            self.sparks.append([x, y, math.cos(th) * s, math.sin(th) * s, 18, col])

    def autoplay(self):
        if not self.shards:
            return
        nearest = min(self.shards, key=lambda s: s["d"])
        target = nearest["a"]
        pads = 4
        best, best_d = 0, 99
        for i in range(pads):
            pa = self.ang + i * (math.pi * 2 / pads)
            d = (target - pa + math.pi) % (math.pi * 2) - math.pi
            if abs(d) < abs(best_d):
                best, best_d = i, d
        self.spin += max(-0.16, min(0.16, best_d * 0.28))

    def step(self, keys=None):
        self.t += 1
        if self.flash:
            self.flash -= 1
        if self.auto:
            self.autoplay()
        elif keys:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.spin -= 0.018
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.spin += 0.018
        self.spin *= 0.92
        self.ang = (self.ang + self.spin) % (math.pi * 2)
        if self.t % 18 == 0 and len(self.shards) < 10:
            self._spawn()
        keep = []
        pads = 4
        for sh in self.shards:
            sh["d"] -= sh["spd"]
            sh["wob"] += 0.18
            sh["a"] += 0.004 * math.sin(sh["wob"])
            x = CX + math.cos(sh["a"]) * sh["d"]
            y = CY + math.sin(sh["a"]) * sh["d"]
            hit = False
            if abs(sh["d"] - RING_R) < 26:
                for i in range(pads):
                    pa = self.ang + i * (math.pi * 2 / pads)
                    da = (sh["a"] - pa + math.pi) % (math.pi * 2) - math.pi
                    if abs(da) < PAD_ARC * 0.55:
                        hit = True
                        self.score += 40 + int(sh["spd"] * 8)
                        self.hits += 1
                        self._burst(x, y, sh["col"], 22)
                        self.flash = 5
                        break
            if hit:
                continue
            if sh["d"] <= CORE_R + sh["r"]:
                self.miss += 1
                self.hp = max(0, self.hp - 1)
                self._burst(CX, CY, PAL["rose"], 26)
                self.flash = 8
                if self.hp <= 0:
                    self.hp = 5
                    self.flash = 12
                continue
            if -80 < x < W + 80 and -80 < y < H + 80:
                keep.append(sh)
        self.shards = keep
        nxt = []
        for sp in self.sparks:
            sp[0] += sp[2]
            sp[1] += sp[3]
            sp[4] -= 1
            if sp[4] > 0:
                nxt.append(sp)
        self.sparks = nxt

    def draw(self, surf, font, small, mid):
        for y in range(0, H, 8):
            k = y / H
            pygame.draw.rect(surf, (int(8 + 22 * k), int(3 + 6 * k), int(16 + 30 * k)), (0, y, W, 8))
        for i, (x, y, r, col) in enumerate(self.motes):
            yy = (y + int(self.t * 0.55 + i * 3)) % H
            pygame.draw.circle(surf, col, (x, yy), r)
        for rad, col, w in ((RING_R + 70, PAL["ink"], 10), (RING_R, (60, 20, 80), 6), (CORE_R + 90, PAL["ink"], 4)):
            pygame.draw.circle(surf, col, (CX, CY), rad, w)
        pulse = 0.55 + 0.45 * math.sin(self.t * 0.12)
        pygame.draw.circle(surf, PAL["core"], (CX, CY), CORE_R + int(6 * pulse))
        pygame.draw.circle(surf, PAL["ice"], (CX - 10, CY - 12), 14)
        pygame.draw.circle(surf, PAL["ink"], (CX, CY), CORE_R - 18)
        pygame.draw.circle(surf, PAL["ring"], (CX, CY), RING_R, 5)
        pads = 4
        for i in range(pads):
            pa = self.ang + i * (math.pi * 2 / pads)
            pts = []
            for k in range(-6, 7):
                aa = pa + (k / 6.0) * PAD_ARC * 0.5
                rr = RING_R + (PAD_W if abs(k) < 5 else 6)
                pts.append((CX + math.cos(aa) * rr, CY + math.sin(aa) * rr))
            for k in range(6, -7, -1):
                aa = pa + (k / 6.0) * PAD_ARC * 0.5
                rr = RING_R - 10
                pts.append((CX + math.cos(aa) * rr, CY + math.sin(aa) * rr))
            pygame.draw.polygon(surf, PAL["pad"], pts)
            pygame.draw.polygon(surf, PAL["ice"], pts, 2)
            hx = CX + math.cos(pa) * RING_R
            hy = CY + math.sin(pa) * RING_R
            pygame.draw.circle(surf, PAL["gold"], (int(hx), int(hy)), 9)
        for sh in self.shards:
            x = int(CX + math.cos(sh["a"]) * sh["d"])
            y = int(CY + math.sin(sh["a"]) * sh["d"])
            pygame.draw.circle(surf, sh["col"], (x, y), sh["r"] + 5)
            pygame.draw.circle(surf, PAL["ice"], (x - 3, y - 4), max(3, sh["r"] // 3))
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 4))
        if self.flash:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 90, 170, 10 * self.flash))
            surf.blit(veil, (0, 0))
        banner = pygame.Surface((W, 150), pygame.SRCALPHA)
        banner.fill((10, 4, 22, 230))
        surf.blit(banner, (0, 0))
        surf.blit(font.render(TITLE, True, PAL["ring"]), (36, 16))
        surf.blit(small.render(HANDLE, True, PAL["gold"]), (36, 88))
        sc = font.render(f"{self.score:05d}", True, PAL["core"])
        surf.blit(sc, (W - 44 - sc.get_width(), 16))
        meta = small.render(f"HIT {self.hits}   MISS {self.miss}   HP {'●' * self.hp}", True, PAL["pad"])
        surf.blit(meta, (W - 44 - meta.get_width(), 90))
        hint = "A / D  spin the ring" if not self.auto else "AUTO RELAY"
        foot = small.render(hint, True, PAL["dim"])
        surf.blit(foot, foot.get_rect(center=(W * 0.5, H - 48)))


def record(path):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    font = pygame.font.SysFont("DejaVu Sans", 56, bold=True)
    mid = pygame.font.SysFont("DejaVu Sans", 46, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 32, bold=True)
    g = Game(auto=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frames = FPS * 15
    try:
        for _ in range(frames):
            g.step()
            g.draw(surf, font, small, mid)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read()
        rc = proc.wait(timeout=60)
    except Exception:
        proc.kill()
        raise
    if rc != 0:
        raise RuntimeError(err.decode("utf-8", "ignore")[-800:])
    print("wrote", path)


def play():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("DejaVu Sans", 56, bold=True)
    mid = pygame.font.SysFont("DejaVu Sans", 46, bold=True)
    small = pygame.font.SysFont("DejaVu Sans", 32, bold=True)
    g = Game(auto=False)
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                run = False
        g.step(pygame.key.get_pressed())
        g.draw(screen, font, small, mid)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--record", action="store_true")
    p.add_argument("--play", action="store_true")
    p.add_argument("--out", default="/home/workdir/artifacts/TOURMALINE_RING_ElbowOS.mp4")
    a = p.parse_args()
    if a.record or not a.play:
        record(a.out)
        if a.play:
            play()
    else:
        play()


if __name__ == "__main__":
    main()
