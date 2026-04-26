import random
import time
import threading
import pygame
import sys

# ================= SPEED & SPACING =================
speeds = {'car': 2.2, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}
movingGap = 27

# ================= POSITIONS =================
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicleTypes  = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
stopLines   = {'right': 590, 'down': 330, 'left': 800, 'up': 535}


# ================= VEHICLE CLASS =================
class Vehicle(pygame.sprite.Sprite):
    """
    Represents a single vehicle in the simulation.

    Car-following logic (canMove / enforceStopLine) is intentionally preserved
    from the original implementation so that safety gaps and stop-line enforcement
    remain identical regardless of whether we are in interactive or evaluation mode.
    """

    def __init__(self, lane, vtype, dir_num, direction,
                 vehicles_dict, simulation_group, images_cache, spawn_time_ref):
        pygame.sprite.Sprite.__init__(self)

        self.lane      = lane
        self.vtype     = vtype
        self.speed     = speeds[vtype]
        self.dir_num   = dir_num
        self.direction = direction
        self.x         = x[direction][lane]
        self.y         = y[direction][lane]
        self.crossed   = False
        self.spawn_time = spawn_time_ref()   # callable so eval mode can pass sim-clock

        # ── shared state references (injected so the class is self-contained) ──
        self._vehicles   = vehicles_dict
        self._simulation = simulation_group

        self._vehicles[direction][lane].append(self)
        self.index = len(self._vehicles[direction][lane]) - 1

        self.image = images_cache[direction][vtype]
        self._simulation.add(self)

    # ------------------------------------------------------------------ #
    #  🔥 FIX 1 – stronger safety gap (unchanged from original)           #
    # ------------------------------------------------------------------ #
    def canMove(self):
        if self.index == 0:
            return True

        front    = self._vehicles[self.direction][self.lane][self.index - 1]
        safeGap  = movingGap + 15   # extra buffer on top of movingGap

        if self.direction == 'right':
            return (self.x + self.image.get_width() + safeGap) < front.x
        elif self.direction == 'left':
            return (self.x - safeGap) > (front.x + front.image.get_width())
        elif self.direction == 'down':
            return (self.y + self.image.get_height() + safeGap) < front.y
        elif self.direction == 'up':
            return (self.y - safeGap) > (front.y + front.image.get_height())
        return True

    def enforceStopLine(self):
        if self.direction == 'right':
            stop = stopLines['right']
            if self.x + self.image.get_width() > stop:
                self.x = stop - self.image.get_width()

        elif self.direction == 'left':
            stop = stopLines['left']
            if self.x < stop:
                self.x = stop

        elif self.direction == 'down':
            stop = stopLines['down']
            if self.y + self.image.get_height() > stop:
                self.y = stop - self.image.get_height()

        elif self.direction == 'up':
            stop = stopLines['up']
            if self.y < stop:
                self.y = stop

    # ------------------------------------------------------------------ #
    #  🔥 FIX 2 – block movement entirely when vehicle ahead is too close #
    # ------------------------------------------------------------------ #
    def move(self, currentGreen, currentYellow, metrics):
        if not self.canMove():
            return      # hard stop – never overlap, even on green

        signal_allows = True
        if not self.crossed:
            at_stop_line = False
            buffer = 5

            if   self.direction == 'right' and self.x + self.image.get_width() >= stopLines['right'] - buffer:
                at_stop_line = True
            elif self.direction == 'left'  and self.x <= stopLines['left'] + buffer:
                at_stop_line = True
            elif self.direction == 'down'  and self.y + self.image.get_height() >= stopLines['down'] - buffer:
                at_stop_line = True
            elif self.direction == 'up'    and self.y <= stopLines['up'] + buffer:
                at_stop_line = True

            if at_stop_line:
                if not (currentGreen == self.dir_num and currentYellow == 0):
                    signal_allows = False

        if signal_allows:
            if   self.direction == 'right': self.x += self.speed
            elif self.direction == 'left':  self.x -= self.speed
            elif self.direction == 'down':  self.y += self.speed
            elif self.direction == 'up':    self.y -= self.speed
        else:
            self.enforceStopLine()

        if not self.crossed:
            if ((self.direction == 'right' and self.x > stopLines['right'])  or
                (self.direction == 'left'  and self.x < stopLines['left'])   or
                (self.direction == 'down'  and self.y > stopLines['down'])   or
                (self.direction == 'up'    and self.y < stopLines['up'])):
                self.crossed = True
                metrics['total_vehicles_passed'] += 1
                metrics['total_waiting_time']    += (time.time() - self.spawn_time)


# ================= HELPERS =================
def _build_vehicles_dict():
    return {'right': {0: [], 1: [], 2: []},
            'down':  {0: [], 1: [], 2: []},
            'left':  {0: [], 1: [], 2: []},
            'up':    {0: [], 1: [], 2: []}}

def _load_images():
    """Load all vehicle + signal images once and return a nested dict."""
    cache = {}
    for d in directionNumbers.values():
        cache[d] = {}
        for vt in vehicleTypes.values():
            cache[d][vt] = pygame.image.load(f"images/{d}/{vt}.png")
    signals = {
        'red':    pygame.image.load("images/signals/red.png"),
        'yellow': pygame.image.load("images/signals/yellow.png"),
        'green':  pygame.image.load("images/signals/green.png"),
    }
    return cache, signals

def _get_queue(simulation):
    return sum(1 for v in simulation if not v.crossed)

def _fitness(metrics, simulation):
    avg_wait = (metrics['total_waiting_time'] / metrics['total_vehicles_passed']
                if metrics['total_vehicles_passed'] else 0)
    return avg_wait + _get_queue(simulation)

def _cleanup_out_of_bounds(simulation, vehicles_dict):
    """Remove sprites that have left the screen and re-index their lanes."""
    for v in list(simulation):
        if v.x < -200 or v.x > 1600 or v.y < -200 or v.y > 1000:
            lane_list = vehicles_dict[v.direction][v.lane]
            if v in lane_list:
                lane_list.remove(v)
                for i, veh in enumerate(lane_list):
                    veh.index = i
            v.kill()


# =========================================================
# TASK 1 – Evaluation Function
# =========================================================
def evaluate(green_times, sim_duration=60, headless=False):
    """
    Run the traffic simulation for *sim_duration* wall-clock seconds and
    return a single Fitness Score = Avg Waiting Time + Queue Length.

    Parameters
    ----------
    green_times   : list[int]  – [G1, G2, G3, G4] green durations per direction
    sim_duration  : int        – how many seconds to run (default 60)
    headless      : bool       – if True, skip all pygame rendering (faster)

    Returns
    -------
    float  – fitness score (lower is better)
    """
    # ── mutable simulation state (no globals) ─────────────────────────
    state = {
        'currentGreen':  0,
        'currentYellow': 0,
        'greenTimes':    list(green_times),
        'yellowTime':    4,
        'running':       True,
    }
    metrics = {
        'total_waiting_time':    0,
        'total_vehicles_passed': 0,
    }

    vehicles_dict = _build_vehicles_dict()
    simulation    = pygame.sprite.Group()

    # ── pygame setup ──────────────────────────────────────────────────
    if not pygame.get_init():
        pygame.init()

    if headless:
        screen = None
        font   = None
        bg = red_img = yellow_img = green_img = None
        vehicle_images, _ = _load_images()
        signal_images      = {}
    else:
        screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Traffic Simulation – Evaluating …")
        vehicle_images, signal_images = _load_images()
        bg        = pygame.image.load("images/intersection.png")
        red_img   = signal_images['red']
        yellow_img = signal_images['yellow']
        green_img  = signal_images['green']
        font      = pygame.font.Font(None, 30)

    clock = pygame.time.Clock()

    # ── spawn-time helper (wall clock) ────────────────────────────────
    def spawn_time_fn():
        return time.time()

    # ── signal thread (stops when state['running'] is False) ──────────
    def signal_loop():
        while state['running']:
            sleep_left = state['greenTimes'][state['currentGreen']]
            deadline   = time.time() + sleep_left
            while time.time() < deadline and state['running']:
                time.sleep(0.05)
            if not state['running']:
                break
            state['currentYellow'] = 1
            yellow_deadline = time.time() + state['yellowTime']
            while time.time() < yellow_deadline and state['running']:
                time.sleep(0.05)
            state['currentYellow'] = 0
            state['currentGreen']  = (state['currentGreen'] + 1) % 4

    # ── vehicle-generation thread (stops when state['running'] is False)
    def generate_vehicles():
        random.seed(42)  # deterministic vehicle generation for fair evaluation
        while state['running']:
            vtype = random.randint(0, 3)
            lane  = random.randint(0, 2)
            r     = random.randint(0, 99)
            if   r < 40: d = 0
            elif r < 70: d = 1
            elif r < 85: d = 2
            else:        d = 3

            Vehicle(
                lane, vehicleTypes[vtype], d, directionNumbers[d],
                vehicles_dict, simulation, vehicle_images, spawn_time_fn
            )
            # interruptible sleep
            deadline = time.time() + 1.2
            while time.time() < deadline and state['running']:
                time.sleep(0.05)

    # ── launch threads ────────────────────────────────────────────────
    t_signal   = threading.Thread(target=signal_loop,      daemon=True)
    t_vehicles = threading.Thread(target=generate_vehicles, daemon=True)
    t_signal.start()
    t_vehicles.start()

    # ── main loop ─────────────────────────────────────────────────────
    start_time = time.time()

    while (time.time() - start_time) < sim_duration:
        # handle quit even during evaluation
        if not headless:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    state['running'] = False
                    pygame.quit()
                    sys.exit()

        cg = state['currentGreen']
        cy = state['currentYellow']

        for v in list(simulation):
            v.move(cg, cy, metrics)

        _cleanup_out_of_bounds(simulation, vehicles_dict)

        if not headless:
            screen.blit(bg, (0, 0))

            for i in range(4):
                if i == cg:
                    screen.blit(yellow_img if cy else green_img, signalCoods[i])
                else:
                    screen.blit(red_img, signalCoods[i])

            for v in simulation:
                screen.blit(v.image, (v.x, v.y))

            avg  = (metrics['total_waiting_time'] / metrics['total_vehicles_passed']
                    if metrics['total_vehicles_passed'] else 0)
            q    = _get_queue(simulation)
            fit  = _fitness(metrics, simulation)
            elapsed = time.time() - start_time

            screen.blit(font.render(f"Avg Wait:  {avg:.2f}s",         True, (255, 255, 255)), (20, 20))
            screen.blit(font.render(f"Queue:     {q}",                True, (255, 255, 255)), (20, 50))
            screen.blit(font.render(f"Fitness:   {fit:.2f}",          True, (255, 255, 255)), (20, 80))
            screen.blit(font.render(f"Elapsed:   {elapsed:.1f}s/{sim_duration}s",
                                     True, (200, 200, 100)), (20, 110))
            screen.blit(font.render(f"Green:     Dir {cg} ({'YELLOW' if cy else 'GREEN'})",
                                     True, (200, 200, 100)), (20, 140))

            pygame.display.update()
            # Task 4 – no FPS cap during evaluation = fast-forward
            # (clock.tick(60) intentionally omitted here)
        else:
            # headless: yield CPU occasionally
            time.sleep(0)

    # ── stop threads ─────────────────────────────────────────────────
    state['running'] = False
    t_signal.join(timeout=2)
    t_vehicles.join(timeout=2)

    score = _fitness(metrics, simulation)
    return score


# =========================================================
# Interactive / Original Main (unchanged UI)
# =========================================================
def main():
    """
    Run the simulation interactively, indefinitely, exactly as the original
    script did – with the same visual appearance and vehicle logic.
    """
    # ── mutable state ─────────────────────────────────────────────────
    state = {
        'currentGreen':  0,
        'currentYellow': 0,
        'greenTimes':    [10, 10, 10, 10],
        'yellowTime':    4,
        'running':       True,
    }
    metrics = {
        'total_waiting_time':    0,
        'total_vehicles_passed': 0,
    }

    vehicles_dict = _build_vehicles_dict()

    pygame.init()
    simulation = pygame.sprite.Group()

    vehicle_images, signal_images = _load_images()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Traffic Simulation")

    bg         = pygame.image.load("images/intersection.png")
    red_img    = signal_images['red']
    yellow_img = signal_images['yellow']
    green_img  = signal_images['green']
    font       = pygame.font.Font(None, 30)
    clock      = pygame.time.Clock()

    def spawn_time_fn():
        return time.time()

    def signal_loop():
        while state['running']:
            deadline = time.time() + state['greenTimes'][state['currentGreen']]
            while time.time() < deadline and state['running']:
                time.sleep(0.05)
            if not state['running']:
                break
            state['currentYellow'] = 1
            yd = time.time() + state['yellowTime']
            while time.time() < yd and state['running']:
                time.sleep(0.05)
            state['currentYellow'] = 0
            state['currentGreen']  = (state['currentGreen'] + 1) % 4

    def generate_vehicles():
        while state['running']:
            vtype = random.randint(0, 3)
            lane  = random.randint(0, 2)
            r     = random.randint(0, 99)
            if   r < 40: d = 0
            elif r < 70: d = 1
            elif r < 85: d = 2
            else:        d = 3
            Vehicle(lane, vehicleTypes[vtype], d, directionNumbers[d],
                    vehicles_dict, simulation, vehicle_images, spawn_time_fn)
            deadline = time.time() + 1.2
            while time.time() < deadline and state['running']:
                time.sleep(0.05)

    threading.Thread(target=signal_loop,      daemon=True).start()
    threading.Thread(target=generate_vehicles, daemon=True).start()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                state['running'] = False
                pygame.quit()
                sys.exit()

        cg = state['currentGreen']
        cy = state['currentYellow']

        screen.blit(bg, (0, 0))

        for i in range(4):
            if i == cg:
                screen.blit(yellow_img if cy else green_img, signalCoods[i])
            else:
                screen.blit(red_img, signalCoods[i])

        for v in list(simulation):
            v.move(cg, cy, metrics)
            screen.blit(v.image, (v.x, v.y))

        _cleanup_out_of_bounds(simulation, vehicles_dict)

        avg = (metrics['total_waiting_time'] / metrics['total_vehicles_passed']
               if metrics['total_vehicles_passed'] else 0)
        screen.blit(font.render(f"Avg Wait: {avg:.2f}s",          True, (255, 255, 255)), (20, 20))
        screen.blit(font.render(f"Queue:    {_get_queue(simulation)}", True, (255, 255, 255)), (20, 50))
        screen.blit(font.render(f"Fitness:  {_fitness(metrics, simulation):.2f}", True, (255, 255, 255)), (20, 80))

        pygame.display.update()
        clock.tick(60)   # 60 FPS cap for interactive mode only


# =========================================================
# TASK 3 – Baseline Tester
# =========================================================
if __name__ == "__main__":
    # ── Baseline experiments ────────────────────────────────────────
    #    Set headless=True to skip rendering (much faster).
    #    Set headless=False to watch each run play out visually.
    HEADLESS      = False   # flip to True for pure-console benchmark
    SIM_DURATION  = 60      # seconds per trial

    baseline_cases = [
        [10, 10, 10, 10],   # Case 1 – uniform equal timing
        [20, 10, 15, 25],   # Case 2 – skewed timing
        [5,  5,  5,  5]  # Case 3 – very short phases
    ]

    print("=" * 50)
    print("  Traffic Simulation – Baseline Evaluation")
    print(f"  Duration per run : {SIM_DURATION}s")
    print(f"  Rendering        : {'OFF (headless)' if HEADLESS else 'ON'}")
    print("=" * 50)

    pygame.init()   # init once before all evaluate() calls

    results = []
    for i, gt in enumerate(baseline_cases, start=1):
        print(f"\n[Case {i}] green_times = {gt}")
        print("  Running … ", end="", flush=True)

        score = evaluate(gt, sim_duration=SIM_DURATION, headless=HEADLESS)
        results.append((gt, score))
        print(f"Fitness Score = {score:.4f}")

    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)
    for i, (gt, score) in enumerate(results, start=1):
        print(f"  Case {i}  {str(gt):<20}  →  Fitness = {score:.4f}")
    best = min(results, key=lambda r: r[1])
    print(f"\n  ✓ Best case: {best[0]}  (score = {best[1]:.4f})")
    print("=" * 50)

    pygame.quit()
