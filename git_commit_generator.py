#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Commit Generator - visszaadatáló commit készítő
Ellenőrzi a Git telepítést, és CMD-ből is futtatható.
"""

import subprocess
import sys
import os
import shutil
import platform
from datetime import datetime, timedelta
import random

#  Színek és segédfüggvények

class Color:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def p(color, msg):
    print(f"{color}{msg}{Color.RESET}")

#  1. GIT telepítés ellenőrzése

def check_git():
    p(Color.CYAN, "\nGit telepítés ellenőrzése...")

    git_path = shutil.which("git")

    if git_path is None:
        p(Color.RED, "A Git NEM található a gépen vagy nincs a PATH-ban!\n")
        p(Color.YELLOW, "Telepítési lehetőségek:")
        print("   -> Windows:  https://git-scm.com/download/win")
        print("   -> Mac:      brew install git")
        print("   -> Linux:    sudo apt install git  /  sudo dnf install git / sudo pacman -S git\n")
        p(Color.YELLOW, "Telepítés után indítsd újra a CMD ablakot, majd futtasd újra a scriptet.")
        sys.exit(1)

    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        p(Color.GREEN, f"Git megtalálva: {version}")
        p(Color.GREEN, f"   Elérési ut: {git_path}\n")
    except Exception as e:
        p(Color.RED, f"Git futtatása sikertelen: {e}")
        sys.exit(1)

#  2. GIT konfiguráció ellenőrzése

def check_git_config():
    p(Color.CYAN, "Git felhasználó ellenőrzése...")

    name  = subprocess.run(["git", "config", "--global", "user.name"],
                           capture_output=True, text=True).stdout.strip()
    email = subprocess.run(["git", "config", "--global", "user.email"],
                           capture_output=True, text=True).stdout.strip()

    if not name or not email:
        p(Color.YELLOW, "Nincs beállítva globális Git felhasználó!")
        name  = input("   Add meg a nevedet (pl. Kovács János): ").strip()
        email = input("   Add meg az email címedet: ").strip()
        subprocess.run(["git", "config", "--global", "user.name",  name])
        subprocess.run(["git", "config", "--global", "user.email", email])
        p(Color.GREEN, "Git felhasználó beállítva.\n")
    else:
        p(Color.GREEN, f"Git user: {name} <{email}>\n")

#  3. REPO inicializálása / ellenőrzése

def init_repo(repo_path, remote_url=None):
    p(Color.CYAN, f"Repo mappa: {repo_path}")

    os.makedirs(repo_path, exist_ok=True)
    os.chdir(repo_path)

    if os.path.exists(".git"):
        p(Color.YELLOW, "A mappa már inicializált Git repo.\n")
    else:
        subprocess.run(["git", "init"], check=True)
        p(Color.GREEN, "Git repo inicializálva.\n")

    if remote_url:
        existing = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout.strip()
        if "origin" in existing:
            p(Color.YELLOW, "Remote 'origin' már létezik, frissítés...")
            subprocess.run(["git", "remote", "set-url", "origin", remote_url])
        else:
            subprocess.run(["git", "remote", "add", "origin", remote_url])
        p(Color.GREEN, f"Remote URL beállítva: {remote_url}\n")

#  4. EGYETLEN visszaadatáló COMMIT

def make_commit(date_str: str, message: str, file_name: str = None):
    if file_name is None:
        ts = date_str.replace(" ", "_").replace(":", "-")
        file_name = f"change_{ts}.txt"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"Commit dátuma: {date_str}\n")
        f.write(f"Uzenet: {message}\n")

    subprocess.run(["git", "add", file_name], check=True)

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"]    = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    result = subprocess.run(
        ["git", "commit", "-m", message],
        env=env, capture_output=True, text=True
    )

    if result.returncode == 0:
        p(Color.GREEN, f"[{date_str}]  {message}")
    else:
        p(Color.RED, f"Hiba: {result.stderr.strip()}")

#  5. Több COMMIT generálása

def generate_commits(start_date: str, end_date: str, count: int, messages: list):
    p(Color.CYAN, f"\n{count} commit generálása: {start_date} -> {end_date}\n")

    fmt   = "%Y-%m-%d"
    start = datetime.strptime(start_date, fmt)
    end   = datetime.strptime(end_date,   fmt)
    delta = (end - start).days

    if delta < 1:
        p(Color.RED, "A végdátumnak később kell lennie a kezdőnél.")
        return

    days_chosen = sorted(random.sample(range(delta + 1), min(count, delta + 1)))

    for i, day_offset in enumerate(days_chosen):
        hour   = random.randint(8, 20)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dt = start + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        msg = messages[i % len(messages)]
        make_commit(date_str, msg)

    p(Color.GREEN, f"\n{len(days_chosen)} commit sikeresen létrehozva!\n")

#  6. REPO LÉTREHOZÁSI DÁTUMÁNAK BEÁLLÍTÁSA

def set_repo_creation_date(date_str: str, commit_message: str = "Initial commit"):
    """
    Beállítja a repo látszólagos 'létrehozási dátumát':
    - Üres repo esetén: létrehoz egy backdatált initial commitot
    - Meglévő commitok esetén: átírja az ELSŐ commit dátumát (history rewrite)
    """
    result = subprocess.run(
        ["git", "log", "--oneline"],
        capture_output=True, text=True
    )
    has_commits = result.returncode == 0 and result.stdout.strip() != ""

    if not has_commits:
        # -- UJ REPO: initial commit backdatálva --------------------------------
        p(Color.CYAN, f"\nInitial commit létrehozása visszadatálva: {date_str}")

        if not os.path.exists("README.md"):
            with open("README.md", "w", encoding="utf-8") as f:
                f.write("# Project\n\nInitial setup.\n")
        subprocess.run(["git", "add", "README.md"], check=True)

        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"]    = date_str
        env["GIT_COMMITTER_DATE"] = date_str

        res = subprocess.run(
            ["git", "commit", "-m", commit_message],
            env=env, capture_output=True, text=True
        )

        if res.returncode == 0:
            p(Color.GREEN, f"Repo letrehozási dátuma beállítva: {date_str}")
        else:
            p(Color.RED, f"Hiba az initial commitnál: {res.stderr.strip()}")

    else:
        # -- MEGLEVO REPO: első commit dátumának átírása -------------------------
        p(Color.CYAN, "\nMeglevo repo - az ELSO commit dátumának átírása...")
        p(Color.YELLOW, f"   Cél dátum: {date_str}")

        root_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True, text=True
        )
        root_hash = root_result.stdout.strip()

        if not root_hash:
            p(Color.RED, "Nem sikerült megtalálni az első commitot.")
            return

        p(Color.CYAN, f"   Elso commit azonosítója: {root_hash[:10]}")

        old_date = subprocess.run(
            ["git", "log", "-1", "--format=%ai", root_hash],
            capture_output=True, text=True
        ).stdout.strip()
        p(Color.YELLOW, f"   Jelenlegi dátum: {old_date}")
        p(Color.YELLOW,  "   FIGYELEM: Ez átírja a git history-t! Utána force push szükséges.\n")

        confirm = input("   Biztosan folytatod? (i/n): ").strip().lower()
        if confirm != "i":
            p(Color.YELLOW, "Megszakítva.")
            return

        # Unstaged változások elmentése (filter-branch nem fut, ha van ilyen)
        stash_result = subprocess.run(
            ["git", "stash", "--include-untracked"],
            capture_output=True, text=True
        )
        stashed = "No local changes" not in stash_result.stdout
        if stashed:
            p(Color.YELLOW, "   Unstaged változások ideiglenesen elmentve (git stash)...")

        env_filter = (
            f'if [ "$GIT_COMMIT" = "{root_hash}" ]; then '
            f'export GIT_AUTHOR_DATE="{date_str}"; '
            f'export GIT_COMMITTER_DATE="{date_str}"; '
            f'fi'
        )

        res = subprocess.run(
            ["git", "filter-branch", "-f", "--env-filter", env_filter, "--", "--all"],
            capture_output=True, text=True
        )

        if stashed:
            pop_result = subprocess.run(
                ["git", "stash", "pop"],
                capture_output=True, text=True
            )
            if pop_result.returncode == 0:
                p(Color.GREEN, "   Elmentett változások visszaállítva (git stash pop).")
            else:
                p(Color.YELLOW, f"   Stash pop sikertelen, manuálisan futtasd: git stash pop\n{pop_result.stderr.strip()}")

        if res.returncode == 0:
            p(Color.GREEN, f"Elso commit dátuma sikeresen átírva: {date_str}")
            p(Color.YELLOW, "   Fontos: a remote-ra force push-szal kell felküldeni!")
            p(Color.YELLOW, "   -> git push origin main --force")
        else:
            p(Color.RED, f"Hiba a filter-branch során:\n{res.stderr.strip()}")
            p(Color.YELLOW, "   Tipp: Gyozodj meg róla, hogy Git Bash-ben futtatod (Windows esetén).")

#  7. PUSH

def push_to_github(force=False):
    p(Color.CYAN, "\nPush GitHub-ra...")
    subprocess.run(["git", "branch", "-M", "main"])
    cmd = ["git", "push", "-u", "origin", "main"]
    if force:
        cmd.append("--force")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        p(Color.GREEN, "Push sikeres!")
    else:
        p(Color.RED, f"Push hiba:\n{result.stderr.strip()}")
        p(Color.YELLOW, "   Tipp: Ha már volt push, próbáld force push-szal (válaszd az F opciót).")

#  8. Interaktív menü

def menu():
    if platform.system() == "Windows":
        os.system("color")  # ANSI színek engedélyezése CMD-ben

    p(Color.BOLD + Color.CYAN, "=" * 60)
    p(Color.BOLD + Color.CYAN, "   Git Visszadatált Commit Generátor by: MartinkaV2 alias Martin Medvecz")
    p(Color.BOLD + Color.CYAN, "=" * 60)

    check_git()
    check_git_config()

    repo_path = input("Repo mappa neve/elérési útja (Enter = jelenlegi mappa): ").strip()
    if not repo_path:
        repo_path = os.getcwd()

    remote_url = input("GitHub remote URL (Enter = kihagyás): ").strip() or None
    init_repo(repo_path, remote_url)

    while True:
        p(Color.CYAN, "\nMit szeretnél csinálni?")
        print("  [1] Egyetlen commit adott dátumra")
        print("  [2] Több commit automatikus generálása (dátumtartomány)")
        print("  [3] Csak push (már meglévő commitokhoz)")
        print("  [4] Repo letrehozási dátumának beállítása (első commit visszadatálása)")
        print("  [Q] Kilépés")

        choice = input("\nVálasztás: ").strip().upper()

        if choice == "1":
            date_str = input("Dátum (YYYY-MM-DD HH:MM:SS, pl. 2024-10-15 10:00:00): ").strip()
            message  = input("Commit üzenet: ").strip()
            make_commit(date_str, message)

        elif choice == "2":
            start = input("Kezdo dátum (YYYY-MM-DD, pl. 2024-10-01): ").strip()
            end   = input("Záró dátum  (YYYY-MM-DD, pl. 2024-10-31): ").strip()
            count = int(input("Hány commitot generáljon? (pl. 20): ").strip())
            p(Color.YELLOW, "\nIrd be a commit üzeneteket (minden sor egy üzenet, üres sor = kész):")
            messages = []
            while True:
                line = input("  > ").strip()
                if not line:
                    break
                messages.append(line)
            if not messages:
                messages = [
                    "Update", "Fix bug", "Refactor", "Add feature", "Cleanup",
                    "Improve performance", "Documentation update", "Minor changes",
                    "Code review fixes", "Dependency update"
                ]
            generate_commits(start, end, count, messages)

        elif choice == "3":
            pass  # csak push következik

        elif choice == "4":
            p(Color.CYAN, "\nRepo letrehozási dátumának beállítása")
            p(Color.YELLOW, "   Ez az első commit dátumát állítja be, ami a GitHub grafikonon")
            p(Color.YELLOW, "   a projekt kezdetét mutatja.")
            date_str  = input("\n   Dátum (YYYY-MM-DD HH:MM:SS, pl. 2023-01-15 09:00:00): ").strip()
            msg_input = input("   Initial commit üzenet (Enter = 'Initial commit'): ").strip()
            commit_msg = msg_input if msg_input else "Initial commit"
            set_repo_creation_date(date_str, commit_msg)

        elif choice == "Q":
            p(Color.YELLOW, "\nKilépés.")
            sys.exit(0)

        else:
            p(Color.RED, "Érvénytelen választás, próbáld újra.")
            continue

        if choice in ("1", "2", "3", "4"):
            do_push = input("\nSzeretnéd pusholni GitHub-ra? (i/n): ").strip().lower()
            if do_push == "i":
                force = input(" Force push? (n = normál, f = --force): ").strip().lower() == "f"
                push_to_github(force)

        p(Color.GREEN + Color.BOLD, "\nMuvelet kész! Visszatérés a főmenübe...\n")

#  Belépési pont

if __name__ == "__main__":
    menu()