"""Управление системой Windows через PowerShell"""
import subprocess
from typing import Tuple


def run_powershell(command: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Универсальная обёртка для выполнения PowerShell-команд.
    Возвращает (успех, stdout|stderr).
    """
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", command,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Превышено время ожидания команды"
    except Exception as e:
        return False, f"Ошибка выполнения: {e}"


# === Готовые команды-помощники ===

def open_application(app: str) -> Tuple[bool, str]:
    """Запустить приложение (notepad, calc, chrome, msedge, ms-settings: и т.д.)"""
    return run_powershell(f"Start-Process '{app}'")


def create_folder(path: str) -> Tuple[bool, str]:
    """Создать папку (включая вложенные)"""
    return run_powershell(f"New-Item -ItemType Directory -Path '{path}' -Force")


def lock_workstation() -> Tuple[bool, str]:
    """Заблокировать ПК (как Win+L)"""
    return run_powershell("rundll32.exe user32.dll,LockWorkStation")


def shutdown(delay_seconds: int = 60) -> Tuple[bool, str]:
    """Запланировать выключение через delay_seconds секунд"""
    return run_powershell(f"shutdown /s /t {delay_seconds}")


def cancel_shutdown() -> Tuple[bool, str]:
    """Отменить запланированное выключение"""
    return run_powershell("shutdown /a")


def sleep_after(minutes: int) -> Tuple[bool, str]:
    """Перевести компьютер в спящий режим через N минут (блокирующая)"""
    seconds = minutes * 60
    return run_powershell(
        f"Start-Sleep -Seconds {seconds}; "
        f"Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)",
        timeout=seconds + 30,
    )


def get_battery_percent() -> Tuple[bool, str]:
    """Уровень заряда батареи в процентах"""
    return run_powershell("(Get-CimInstance Win32_Battery).EstimatedChargeRemaining")


def get_cpu_load() -> Tuple[bool, str]:
    """Текущая загрузка CPU в процентах"""
    return run_powershell(
        "(Get-CimInstance Win32_Processor | "
        "Measure-Object -Property LoadPercentage -Average).Average"
    )
