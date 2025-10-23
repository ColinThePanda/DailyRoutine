import time
import os
import sys
import random
import atexit
from string import whitespace
from typing import TYPE_CHECKING
import platform

if platform.system() == "Windows" or (TYPE_CHECKING and sys.platform == "win32"):
    import msvcrt  # windows import
else:
    import termios, tty, sys  # unix imports


def min_to_time(mins: int) -> tuple[int, int, int, str]:
    mins = int(mins)
    hrs, mins = mins // 60, mins % 60
    days, hrs = hrs // 24, hrs % 24
    day_parts_map = {0: "am", 1: "pm"}
    daytime = day_parts_map[hrs % 24 // 12]
    hrs %= 12
    return mins, hrs, days, daytime


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def new_window():
    sys.stdout.write(f"\033[?1049h")
    sys.stdout.flush()


def previous_window():
    sys.stdout.write(f"\033[?1049l")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write(f"\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write(f"\033[?25h")
    sys.stdout.flush()


def read_char() -> str:
    if platform.system() == "Windows" or (TYPE_CHECKING and sys.platform == "win32"):
        # Clear input buffer
        while msvcrt.kbhit():
            msvcrt.getch()
        return msvcrt.getwch()
    else:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch


def read_key() -> str:
    if platform.system() == "Windows" or (TYPE_CHECKING and sys.platform == "win32"):
        ch = read_char()

        if ch == "\x03":
            raise KeyboardInterrupt

        if ch in "\x00\xe0":
            ch = "\x00" + read_char()

        if "\ud800" <= ch <= "\udfff":
            ch += read_char()
            ch = ch.encode("utf-16", errors="surrogatepass").decode("utf-16")

        return ch
    else:
        c1 = read_char()

        if c1 in Key.CTRL_Z:
            raise KeyboardInterrupt

        if c1 != "\x1b":
            return c1

        c2 = read_char()
        if c2 not in "\x4f\x5b":
            return c1 + c2

        c3 = read_char()
        if c3 not in "\x31\x32\x33\x35\x36":
            return c1 + c2 + c3

        c4 = read_char()
        if c4 not in "\x30\x31\x33\x34\x35\x37\x38\x39":
            return c1 + c2 + c3 + c4

        c5 = read_char()
        return c1 + c2 + c3 + c4 + c5


def input(prompt: object = ""):
    print(prompt, end="", flush=True)
    if platform.system() == "Windows" or (TYPE_CHECKING and sys.platform == "win32"):
        line = []
        while True:
            try:
                char = read_key()
            except KeyboardInterrupt:
                print("Interrupt")
                sys.exit()

            # Check for newline (Enter)
            if char in ("\r", "\n"):
                print()  # Print a newline for visual clarity
                break
            # Handle backspace
            elif char == "\x08":
                if line:
                    line.pop()
                    print(
                        "\b \b", end="", flush=True
                    )  # Move back, overwrite with space, move back again
            else:
                line.append(char)
                print(char, end="", flush=True)

        return "".join(line)

    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            line = []

            while True:
                ch = sys.stdin.read(1)

                # Check for Enter key (carriage return)
                if ch == "\r":
                    sys.stdout.write("\n")
                    break

                # Check for backspace or delete
                elif ch in ("\x08", "\x7f"):
                    if line:
                        line.pop()
                        # Erase the character from the screen
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()

                # Handle Ctrl+C, which normally raises KeyboardInterrupt
                elif ch == "\x03":
                    # Restore settings before exiting
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    raise KeyboardInterrupt

                # Handle regular characters
                else:
                    line.append(ch)
                    sys.stdout.write(ch)
                    sys.stdout.flush()

        finally:
            # Always restore the original terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return "".join(line)


def pause_enter(prompt: str = "Press enter to continue..."):
    print(prompt, end="", flush=True)
    key = ""
    while key != "\x0d" and key != "\x0d":
        key = read_key()
    clear()


def prompt_yn(prompt: str) -> bool | None:
    response = "".join(filter(lambda x: x not in whitespace, input(prompt))).lower()
    if response == "yes":
        return True
    elif response == "no":
        return False
    else:
        print("Input must be either yes or no")
        return None


def prompt_int(prompt: str) -> int | None:
    response = "".join(filter(lambda x: x not in whitespace, input(prompt))).lower()
    try:
        return int(response)
    except ValueError:
        return None


def prompt_weekday() -> int | None:
    days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    for i, day in enumerate(days):
        print(f"{i+1}. {day}")
    day = prompt_int("\nWhat day is it today? ")
    if day is None:
        print("Input must be a number")
        return
    if day < 1 or day > 7:
        print("Input must be 1-7")
        return
    return day


def snooze_loop():
    hour = 7
    day_parts_map = {0: "am", 1: "pm"}
    while True:
        show_cursor()
        hour %= 24
        daytime = day_parts_map[hour // 12]

        print(f"The time is {(hour - 1)%12 + 1}{daytime}")
        sleep = prompt_yn("Do you want to sleep more? ")
        if sleep is True:
            hour += 1
        elif sleep is False:
            break
        else:
            return

        hide_cursor()
        clear()
        for i in range(3):
            print(f"\rSleeping{str('.') * int(i+1)}", end="")
            time.sleep(1 / 3)
        clear()


def weekend_events():
    print("Today is a weekend")
    time.sleep(3)
    clear()
    print("You have the option to sleep in")
    time.sleep(3)
    clear()

    snooze_loop()

    clear()
    hide_cursor()
    print("Have a nice day!")
    time.sleep(1)


def shower_minigame():
    clear()
    print("Before you can take a shower, you must get it at the right temperature")
    time.sleep(1)
    pause_enter()
    clear()
    print("The correct temperature is between 1 and 100 degrees")
    time.sleep(1)
    pause_enter()
    clear()

    correct_temp = random.randint(1, 100)

    while True:
        clear()
        show_cursor()
        temp = prompt_int("Set the shower to a temperature (1 - 100): ")
        if temp is None:
            print("Must input a number")
            time.sleep(1)
            continue
        if not (temp >= 1 and temp <= 100):
            print("Temperature must be 1-100")
            time.sleep(1)
            continue

        hide_cursor()
        clear()

        if temp > correct_temp:
            print("\033[31mToo Hot!\033[0m")
        elif temp < correct_temp:
            print("\033[34mToo Cold!\033[0m")
        else:
            print("\033[32mPerfect!\033[0m")
            break

        time.sleep(1)


def clothing_minigame():
    clear()
    print("You have to get dressed, but it only works if it is in the right order")
    time.sleep(1)
    pause_enter()
    clear()
    print("Type in the clothing item to put it on")
    time.sleep(1)
    pause_enter()
    clear()

    wearing = {
        "shirt": False,
        "pants": False,
        "underwear": False,
        "socks": False,
        "shoes": False,
    }
    while True:
        clear()
        for key, value in wearing.items():
            if value is True:
                print(f"\033[32m{key}\033[0m", flush=True)
            else:
                print(f"\033[31m{key}\033[0m", flush=True)
        show_cursor()
        response = input("\n> ")
        choice = "".join(filter(lambda x: x not in whitespace, response)).lower()
        hide_cursor()
        clear()

        if choice in wearing.keys():
            if choice == "pants" and wearing["underwear"] is False:
                print("You can't put pants on before underwear")
                time.sleep(3)
                continue
            if choice == "shoes" and wearing["socks"] is False:
                print("You can't put shoes on before socks")
                time.sleep(3)
                continue
            if choice == "shoes" and wearing["pants"] is False:
                print("You can't put shoes on before pants")
                time.sleep(3)
                continue

            if wearing[choice] is True:
                print("You are already wearing that")
                time.sleep(3)
                continue
            else:
                wearing[choice] = True

                if all(wearing.values()):
                    break


def schoolday_events(elapsed_time):
    print("Today is a school day")
    time.sleep(3)
    clear()
    print("You have to go take a shower")
    time.sleep(3)

    shower_start = time.time()
    # shower_minigame()
    shower_end = time.time()

    elapsed_time += shower_end - shower_start

    time.sleep(1)
    clear()
    print("You take a nice shower and wash yourself")
    time.sleep(3)

    clothing_start = time.time()
    # clothing_minigame()
    clothing_end = time.time()

    elapsed_time += clothing_end - clothing_start

    print("You are fully dressed")
    time.sleep(3)

    clear()
    mins, hrs, days, _ = min_to_time(elapsed_time)
    if days > 0:
        if hrs > 0:
            print(
                f"It took you {days} days, {hrs} hours, and {mins} minutes to get ready for school"
            )
        else:
            print(f"It took you {days} days and {mins} minutes to get ready for school")
    else:
        if hrs > 0:
            print(f"It took you {hrs} hours and {mins} minutes to get ready for school")
        else:
            print(f"It took you {mins} minutes to get ready for school")
    time.sleep(3)
    clear()

    elapsed_time = 1600
    elapsed_time += 15 + 7 * 60

    mins, hrs, days, daytime = min_to_time(elapsed_time)

    if elapsed_time <= 80:
        print(f"You drive to school and arrive at {hrs}:{mins:02d}{daytime}")
        time.sleep(3)
        pause_enter()
        print("You made it to school on time and you are ready to start your day!")
        time.sleep(3)
        pause_enter()
        print(f"\033[32mGood Ending\033[0m")
    elif elapsed_time <= 480:
        print(f"You drive to school and arrive at {hrs}:{mins:02d}{daytime}")
        time.sleep(3)
        pause_enter()
        print("You are late for school")
        show_cursor()
        check_in = prompt_yn("Do you want to check in with Ms.Minchin? ")
        clear()
        if check_in is True:
            print(
                "You did the right thing after being late, but you still missed things"
            )
            time.sleep(3)
            pause_enter()
            print(f"\033[33mLate Ending\033[0m")
        else:
            print("You choose not to check in with Ms.Minchin after arrving late")
            time.sleep(3)
            pause_enter()
            print("Because you did not check in, you are suspended")
            time.sleep(3)
            pause_enter()
            print(f"\033[31mSuspended Ending\033[0m")
    else:
        rev_daytime_map = {"am": 0, "pm": 1}
        total_time = (rev_daytime_map.get(daytime, 0) + 1) * (hrs * 60) + mins
        if days > 0 and total_time / 60 >= 8.33 and total_time / 60 <= 15:
            print("You arrive at school, and everyone is already in class")
            time.sleep(3)
            pause_enter()
            print(
                f"You check the time on your phone, and you see that it is {hrs}:{mins:02d}{daytime}"
            )
            time.sleep(3)
            pause_enter()
            if days == 1:
                print("School is currently in session, but it is the next day")
            else:
                print("School is currently in session, but you missed a few days")
        else:
            print("You arrive at school, but all the lights are off...")
            time.sleep(3)
            pause_enter()
            print(
                f"You check the time on your phone, and you see that it is {hrs}:{mins:02d}{daytime}"
            )
            time.sleep(3)
            pause_enter()
            print("School is already over")
        time.sleep(3)
        pause_enter()
        print(f"\033[31mAbsent Ending\033[0m")
    time.sleep(3)
    pause_enter("Press enter to exit...")


def clean_up():
    previous_window()
    show_cursor()


def main():
    new_window()
    hide_cursor()
    clear()
    for _ in range(3):
        print("Ring!")
        time.sleep(0.5)
        clear()
        time.sleep(0.5)
    clear()

    print("You just woke up and it is 7 AM")
    time.sleep(3)

    start_time = time.time()

    clear()
    show_cursor()
    while True:
        day = prompt_weekday()
        if day:
            break
        time.sleep(1)
        clear()

    hide_cursor()
    clear()
    if day == 1 or day == 7:
        weekend_events()
    elif day > 1 and day < 7:
        schoolday_events(time.time() - start_time)


if __name__ == "__main__":
    atexit.register(clean_up)
    main()
