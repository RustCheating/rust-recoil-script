import win32api, ctypes, pyttsx3, random, multiprocessing, Overlay
from datetime import datetime, timedelta

# Loop settings
active = True
paused = False
########### Recoil Tables
Recoil_Tables = [
    # Recoil_AK
    [
        [-36.3583, 52.3906],
        [5, 46],
        [-55, 42],
        [-42, 37],
        [0, 33],
        [16, 28],
        [29, 24],
        [38, 19],
        [42, 14],
        [42, 9],
        [38, 9],
        [30, 18],
        [17, 25],
        [0, 29],
        [-15, 32],
        [-27, 33],
        [-37, 32],
        [-43, 29],
        [-46, 24],
        [-45, 17],
        [-42, 8],
        [-35, 5],
        [-24, 14],
        [-11, 21],
        [12, 25],
        [36, 28],
        [49, 28],
        [49, 26],
        [38, 21],
    ],
    # Recoil_MP5
    [
        [0, 21],
        [0, 29],
        [0, 33],
        [12, 33],
        [29, 29],
        [33, 22],
        [23, 13],
        [0, 10],
        [-18, 9],
        [-25, 8],
        [-19, 7],
        [-3, 6],
        [7, 5],
        [14, 4],
        [16, 4],
        [16, 3],
        [12, 2],
        [6, 2],
        [-1, 1],
        [-5, 1],
        [-8, 0],
        [-10, 0],
        [-12, 0],
        [-13, 0],
        [-13, 0],
        [-12, 0],
        [-11, 0],
        [-8, 0],
        [-5, 0],
    ],
]
Recoil_Delays = [0.1333333333, 0.1]  # ak  # mp5
Scope_Values = [
    # None
    1,
    # Holo
    1.2,
    # 8x
    3.84,
]
# Multipliers
all_scopes = [
    "None",
    "Holo",
    "8x"
]
all_weapons = ["AK", "MP5"]
scopes_overlay = [
    " ",
    " HOL",
    " 8X"
]
weapon_overlay = [" AK", "MP5"]
active_weapon, active_scope, start_time = 0, 0, 0


def get_sense():  # Get sensitivity on script run
    global sense
    file = open(
        "C:\Program Files (x86)\Steam\steamapps\common\Rust\cfg\client.cfg"
    )  # Path to rust
    for line in file:
        if "input.sensitivity" in line:
            line = line.replace('"', "")
            sense = float(line.replace("input.sensitivity", ""))
    file.close()


def mouse_move_curved(x, y, delay):  # Recoil control for curved weapons
    global start_time
    divider = random.randint(20, 43)  # Smoothing factor
    moveindex, dxindex, dyindex = 0, 0, 0
    dx = int(x / divider)
    absx = abs(x - dx * divider)
    dy = int(y / divider)
    ry = y % divider
    bullet_delay = (delay / (divider)) * 0.61  # 60% of the delay between shots
    while moveindex < divider:
        bullet_start_time = datetime.now()
        ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 5)  # Move recoil / divider
        moveindex += 1
        if absx * moveindex > (dxindex + 1) * divider:
            dxindex += 1
            ctypes.windll.user32.mouse_event(0x0001, int(x / abs(x)), 0, 0, 5)
        if ry * moveindex > (dyindex + 1) * divider:
            dyindex += 1
            ctypes.windll.user32.mouse_event(0x0001, 0, int(y / abs(y)), 0, 5)
        sleepTime = timedelta(seconds=bullet_delay)
        while (
            bullet_start_time + sleepTime > datetime.now()
        ):  # Sleeping in between each smoothing move
            pass
    if x != 0 and y != 0:  # Accounting for loss
        if round(x) != dxindex * int(x / abs(x)) + dx * moveindex:
            ctypes.windll.user32.mouse_event(0x0001, int(x / abs(x)), 0, 0, 5)
            dxindex += 1
        if round(y) != dyindex * int(y / abs(y)) + dy * moveindex:
            ctypes.windll.user32.mouse_event(0x0001, int(y / abs(y)), 0, 0, 5)
            dyindex += 1
    sleepTime = timedelta(seconds=delay)
    while (
        start_time + sleepTime > datetime.now()
    ):  # This is more accurate then time.sleep()
        pass  # This also wont brick if -slept time


def call_move(recoil_pattern, delay):
    global start_time
    current_bullet = 0
    if active_weapon < 6:  # Curved weapons that need smoothing
        while current_bullet < len(recoil_pattern) and win32api.GetKeyState(0x01) < 0:
            if current_bullet != 0:
                start_time = datetime.now()
            recoil_x = ((recoil_pattern[current_bullet][0] / 2) / sense) * Scope_Values[
                active_scope
            ]
            recoil_y = ((recoil_pattern[current_bullet][1] / 2) / sense) * Scope_Values[
                active_scope
            ]
            if active_weapon == 5 and win32api.GetKeyState(0x11) < 0:
                recoil_x = recoil_x / 2
                recoil_y = recoil_y / 2
            mouse_move_curved(recoil_x, recoil_y, delay)
            current_bullet += 1
    else:
        if (
            current_bullet != 0
        ):  # Recoil control for linear weapons that need to be clicked each shot
            start_time = datetime.now()
        recoil_x = ((recoil_pattern[0] / 2) / sense) * Scope_Values[active_scope]
        recoil_y = ((recoil_pattern[1] / 2) / sense) * Scope_Values[active_scope]
        if (
            win32api.GetKeyState(0x11) < 0
        ):  # If player crouched, recoil is .5 for these weapons
            recoil_x = recoil_x / 2
            recoil_y = recoil_y / 2
        ctypes.windll.user32.mouse_event(0x0001, int(recoil_y), int(recoil_x), 0, 5)
        sleepTime = timedelta(seconds=delay)
        while start_time + sleepTime > datetime.now() or win32api.GetKeyState(0x01) < 0:
            pass


def scope_change():  # Changes the current scope value
    global active_scope
    if active_scope == len(all_scopes):  # Max number of scopes
        active_scope = 0
    else:
        active_scope += 1


def weapon_change(int):  # Changes the current weapon value
    if int == -1 and active_weapon == 0:
        return 1
    elif int == 1 and active_weapon == len(all_weapons):  # Max number of weapons
        return 0
    else:
        return active_weapon + int


def run():
    global active, paused, active_weapon, start_time, Recoil_Tables, Recoil_Delays, weapon_overlay
    # Startup Functions
    get_sense()
    # Start Overlay
    p = multiprocessing.Process(
        target=Overlay.draw,
        args=[weapon_overlay[active_weapon], scopes_overlay[active_scope]],
    )
    p.start()
    # TTS Settings
    engine = pyttsx3.init()
    engine.setProperty("volume", 0.1)
    engine.setProperty("rate", 500)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)
    engine.say("Started")
    engine.runAndWait()  # Run engine.say and wait till done
    while active:  # Main loop
        # While not paused
        if not paused:
            if (
                win32api.GetKeyState(0x01) < 0 and win32api.GetKeyState(0x02) < 0
            ):  # Left n Right MB
                start_time = datetime.now()
                call_move(Recoil_Tables[active_weapon], Recoil_Delays[active_weapon])
            if win32api.GetKeyState(0x22) < 0:  # PageDown
                # win32api.SetCursorPos([300, 300]) #For drawing in paint (debugging)
                active_weapon = weapon_change(1)
                p.terminate()
                p = multiprocessing.Process(
                    target=Overlay.draw,
                    args=[weapon_overlay[active_weapon], scopes_overlay[active_scope]],
                )
                p.start()
                engine.say(all_weapons[active_weapon])
                engine.runAndWait()
            if win32api.GetKeyState(0x21) < 0:  # PageUp
                active_weapon = weapon_change(-1)
                p.terminate()
                p = multiprocessing.Process(
                    target=Overlay.draw,
                    args=[weapon_overlay[active_weapon], scopes_overlay[active_scope]],
                )
                p.start()
                engine.say(all_weapons[active_weapon])
                engine.runAndWait()
            if win32api.GetKeyState(0x24) < 0:  # Home
                scope_change()
                p.terminate()
                p = multiprocessing.Process(
                    target=Overlay.draw,
                    args=[weapon_overlay[active_weapon], scopes_overlay[active_scope]],
                )
                p.start()
                engine.say(all_scopes[active_scope])
                engine.runAndWait()
        # Doesnt Matter if Paused
        if win32api.GetKeyState(0x91) < 0:  # ScrLk
            get_sense()
            engine.say("Updated")
            engine.runAndWait()
        if win32api.GetKeyState(0x13) < 0:  # Pause
            paused = not paused
            if paused:
                engine.say("Paused")
                engine.runAndWait()
            elif not paused:
                engine.say("Unpaused")
                engine.runAndWait()
        if win32api.GetKeyState(0x23) < 0:  # End
            engine.say("Exiting")
            p.terminate()
            engine.runAndWait()
            active = False


if __name__ == "__main__":
    run()