from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tomllib
from pathlib import Path


APP_NAME = "GDS3D"
PACKAGE_NAME = "gds3d"
ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
INSTALLER_DIR = DIST_DIR / "installers"
SOURCE_ICON = ROOT / "packaging" / "icons" / "icon.png"
WINDOWS_ICON = ROOT / "build" / "icons" / f"{APP_NAME}.ico"

PlatformName = str
ArchName = str


def main() -> int:
    args = _parse_args()
    version = _package_version(args.version)
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)

    if args.platform == "windows":
        _package_windows(args.arch, version)
    elif args.platform == "macos":
        _package_macos(args.arch, version)
    elif args.platform == "linux":
        _package_linux(args.arch, version)
    else:
        raise ValueError(f"unsupported platform: {args.platform}")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--platform",
        required=True,
        choices=("windows", "macos", "linux"),
    )
    parser.add_argument("--arch", required=True, choices=("x64", "arm64"))
    parser.add_argument("--version")
    return parser.parse_args()


def _package_version(version: str | None) -> str:
    if version is None:
        version = _project_version()
    if version.startswith(("v", "V")) and len(version) > 1 and version[1].isdigit():
        version = version[1:]
    if not version:
        raise ValueError("version must not be empty")
    return version


def _project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("project.version is missing from pyproject.toml")
    return version


def _package_windows(arch: ArchName, version: str) -> None:
    app_dir = DIST_DIR / APP_NAME
    exe_path = app_dir / f"{APP_NAME}.exe"
    if not exe_path.exists():
        raise FileNotFoundError(exe_path)

    outfile = INSTALLER_DIR / f"{APP_NAME}-{version}-windows-{arch}-setup.exe"
    script_path = DIST_DIR / f"{PACKAGE_NAME}-{arch}.nsi"
    script_path.write_text(
        _nsis_script(app_dir=app_dir, outfile=outfile),
        encoding="utf-8",
    )
    makensis = _makensis_path()
    subprocess.run([str(makensis), str(script_path)], cwd=ROOT, check=True)


def _makensis_path() -> Path:
    makensis = shutil.which("makensis")
    if makensis is not None:
        return Path(makensis)

    for base_name in ("ProgramFiles(x86)", "ProgramFiles"):
        base_path = os.environ.get(base_name)
        if not base_path:
            continue
        candidate = Path(base_path) / "NSIS" / "makensis.exe"
        if candidate.exists():
            return candidate

    raise FileNotFoundError("makensis was not found; install NSIS before packaging")


def _nsis_script(app_dir: Path, outfile: Path) -> str:
    app_files = _nsis_path(app_dir / "*")
    installer = _nsis_path(outfile)
    icon = _nsis_path(WINDOWS_ICON)
    return f"""
Unicode True
!include MUI2.nsh

Name "{APP_NAME}"
OutFile "{installer}"
InstallDir "$LOCALAPPDATA\\Programs\\{APP_NAME}"
RequestExecutionLevel user
Icon "{icon}"
UninstallIcon "{icon}"

!define MUI_ABORTWARNING
!define MUI_ICON "{icon}"
!define MUI_UNICON "{icon}"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "{app_files}"
  CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
  CreateShortCut "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe"
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\\{APP_NAME}"
  RMDir /r "$INSTDIR"
SectionEnd
""".lstrip()


def _nsis_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\")


def _package_macos(arch: ArchName, version: str) -> None:
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        raise FileNotFoundError(app_path)

    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
        cwd=ROOT,
        check=True,
    )
    outfile = INSTALLER_DIR / f"{APP_NAME}-{version}-macos-{arch}.dmg"
    subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            APP_NAME,
            "-srcfolder",
            str(app_path),
            "-ov",
            "-format",
            "UDZO",
            str(outfile),
        ],
        cwd=ROOT,
        check=True,
    )


def _package_linux(arch: ArchName, version: str) -> None:
    app_dir = DIST_DIR / APP_NAME
    executable = app_dir / APP_NAME
    if not executable.exists():
        raise FileNotFoundError(executable)

    deb_arch = _deb_arch(arch)
    package_root = DIST_DIR / f"{PACKAGE_NAME}-{deb_arch}"
    if package_root.exists():
        shutil.rmtree(package_root)

    opt_dir = package_root / "opt" / PACKAGE_NAME
    bin_dir = package_root / "usr" / "bin"
    app_dir_dest = package_root / "usr" / "share" / "applications"
    icon_dir = package_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    control_dir = package_root / "DEBIAN"

    shutil.copytree(app_dir, opt_dir)
    bin_dir.mkdir(parents=True)
    app_dir_dest.mkdir(parents=True)
    icon_dir.mkdir(parents=True)
    control_dir.mkdir(parents=True)
    shutil.copy2(SOURCE_ICON, icon_dir / f"{PACKAGE_NAME}.png")

    launcher = bin_dir / PACKAGE_NAME
    launcher.write_text(
        f"#!/bin/sh\nexec /opt/{PACKAGE_NAME}/{APP_NAME} \"$@\"\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    (app_dir_dest / f"{PACKAGE_NAME}.desktop").write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={APP_NAME}",
                f"Exec=/usr/bin/{PACKAGE_NAME}",
                f"Icon={PACKAGE_NAME}",
                "Categories=Graphics;Science;Engineering;",
                "Terminal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (control_dir / "control").write_text(
        "\n".join(
            [
                f"Package: {PACKAGE_NAME}",
                f"Version: {version}",
                "Section: graphics",
                "Priority: optional",
                f"Architecture: {deb_arch}",
                "Maintainer: GDS3D contributors",
                "Description: 3D visualization editor for GDS layouts.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    outfile = INSTALLER_DIR / f"{APP_NAME}-{version}-linux-{arch}.deb"
    subprocess.run(
        ["dpkg-deb", "--build", "--root-owner-group", str(package_root), str(outfile)],
        cwd=ROOT,
        check=True,
    )


def _deb_arch(arch: ArchName) -> str:
    if arch == "x64":
        return "amd64"
    if arch == "arm64":
        return "arm64"
    raise ValueError(f"unsupported architecture: {arch}")


if __name__ == "__main__":
    raise SystemExit(main())
