"""Optional pywin32 SCM host. Configure only on the authorized demo terminal machine."""

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any

CONFIG = Path(r"C:\ProgramData\AITradingReadOnlyBridge\bridge.json")


def service_class() -> Any:
    if sys.platform != "win32":
        raise RuntimeError("Windows service support requires Windows and pywin32")
    utilities = importlib.import_module("win32serviceutil")
    api = importlib.import_module("win32service")
    events = importlib.import_module("win32event")
    jobs = importlib.import_module("win32job")
    handles = importlib.import_module("win32api")
    constants = importlib.import_module("win32con")

    base: Any = utilities.ServiceFramework

    class DemoReadBridgeService(base):  # type: ignore[misc]  # Windows-only dynamic pywin32 base
        _svc_name_ = "AITradingDemoReadOnlyBridge"
        _svc_display_name_ = "AI Trading Demo Read-Only Bridge"

        def __init__(self, args: Any) -> None:
            super().__init__(args)
            self.stopped = events.CreateEvent(None, 0, 0, None)
            self.child: subprocess.Popen[bytes] | None = None

        def SvcStop(self) -> None:
            self.ReportServiceStatus(api.SERVICE_STOP_PENDING)
            events.SetEvent(self.stopped)

        def SvcDoRun(self) -> None:
            # Fixed module and local path; no password/token is placed on a command line.
            root = Path(__file__).resolve().parents[2]
            interpreter = root / ".venv" / "Scripts" / "python.exe"
            if not interpreter.is_file():
                raise RuntimeError("Install the dedicated Windows bridge virtual environment")
            job = jobs.CreateJobObject(None, None)
            limits = jobs.QueryInformationJobObject(job, jobs.JobObjectExtendedLimitInformation)
            limits["BasicLimitInformation"]["LimitFlags"] = (
                jobs.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | jobs.JOB_OBJECT_LIMIT_PROCESS_MEMORY
            )
            limits["ProcessMemoryLimit"] = 768 * 1024 * 1024
            jobs.SetInformationJobObject(job, jobs.JobObjectExtendedLimitInformation, limits)
            self.child = subprocess.Popen(  # noqa: S603 - fixed service module/config, no shell
                [str(interpreter), "-m", "services.broker_bridge.app", "--config", str(CONFIG)],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                process_handle = handles.OpenProcess(
                    constants.PROCESS_SET_QUOTA | constants.PROCESS_TERMINATE, False, self.child.pid
                )
                try:
                    jobs.AssignProcessToJobObject(job, process_handle)
                finally:
                    process_handle.Close()
                while events.WaitForSingleObject(self.stopped, 1000) == events.WAIT_TIMEOUT:
                    if self.child.poll() is not None:
                        raise RuntimeError(
                            "Read-only bridge process stopped; SCM recovery required"
                        )
            finally:
                self.child.terminate()
                try:
                    self.child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.child.kill()
                    self.child.wait(timeout=5)
                job.Close()

    DemoReadBridgeService.__module__ = "services.windows.service"
    DemoReadBridgeService.__qualname__ = "DemoReadBridgeService"
    return DemoReadBridgeService


if sys.platform == "win32":
    DemoReadBridgeService = service_class()


def main() -> None:
    service = globals().get("DemoReadBridgeService") or service_class()
    importlib.import_module("win32serviceutil").HandleCommandLine(service)


if __name__ == "__main__":
    main()
