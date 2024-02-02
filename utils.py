import subprocess
import pkg_resources


def print_red(text):
    """Funkce pro výpis textu červenou barvou."""
    print(f"\033[91m{text}\033[0m")


def ascii():
    print("\n\n______________________________________________")
    print("||||||| Trading template by moodix labs ||||||")
    print(" ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄  ▄▄▄ ▄▄   ▄▄ ")
    print(" █  █▄█  █       █       █      ██   █  █▄█  █ ")
    print(" █       █   ▄   █   ▄   █  ▄    █   █       █ ")
    print(" █       █  █ █  █  █ █  █ █ █   █   █       █ ")
    print(" █       █  █▄█  █  █▄█  █ █▄█   █   ██     █  ")
    print(" █ ██▄██ █       █       █       █   █   ▄   █ ")
    print(" █▄█   █▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄██▄▄▄█▄▄█ █▄▄█ ")
    print("..................................... ver. O.74")
    print("> Not intended for live trading!")
    print("> Created for study purposes of moodix \nAPI connection options!")
    print("______________________________________________\n\n")


def install_requirements(file_path='requirements.txt'):
    with open(file_path, 'r') as file:
        packages = [line.strip() for line in file if line.strip() and not line.startswith('#')]

    print("\nKontrola nainstalovaných balíčků: ")
    for package in packages:
        try:
            # Kontrola, zda je balíček již nainstalován
            pkg_resources.require(package)
            print(f"\033[92m{package}: Nainstalován\033[0m")  # Zelená barva
        except pkg_resources.DistributionNotFound:
            # Instalace balíčku, pokud není nalezen
            print(f"\033[91m{package}: Schází, instaluji...\033[0m")  # Červená barva
            subprocess.check_call(["pip", "install", package])
        except pkg_resources.VersionConflict:
            # Zde můžete přidat logiku pro řešení konfliktů verzí
            pass


def is_paper_account(ib_instance):
    managed_accounts = ib_instance.managedAccounts()
    for account in managed_accounts:
        if account.startswith('DU'):
            print(">> Account type: Paper account")
            return True  # DU znamená paper trading účet
        elif account.startswith('U'):
            print(">> Real account, not allowed!")
    return False
