#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Python 3.11+: tomllib in der Standardbibliothek
try:
    import tomllib
except Exception as e:
    raise SystemExit("Python 3.11+ mit tomllib wird benötigt") from e

# Rich UI
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)
from rich.logging import RichHandler

console = Console()

# ---------- Konfiguration ----------
def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")
    with config_path.open("rb") as f:
        return tomllib.load(f)

def get_cfg(d: dict, key: str, default):
    return d.get(key, default) if isinstance(d, dict) else default

# ---------- .env ----------
load_dotenv()  # lädt .env im Projekt/übergeordneten Verzeichnissen

# ---------- HTTP ----------
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}
RETRY_STATUSES = {403, 429, 503}

# ---------- Prompt mit Timeout ----------
_PROMPT_LOCK = threading.Lock()

def prompt_with_timeout(prompt: str, timeout_sec: int = 15) -> Optional[str]:
    console.print(f"{prompt} (Timeout {timeout_sec}s) [j/N]: ", end="")
    start = time.time()
    try:
        while True:
            if sys.stdin in select_rfds():
                line = sys.stdin.readline()
                if not line:
                    return None
                return line.strip()
            if time.time() - start >= timeout_sec:
                console.print("")
                return None
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("")
        return "n"

def select_rfds():
    rfds: List[object] = []
    try:
        import msvcrt  # type: ignore
        if msvcrt.kbhit():
            rfds.append(sys.stdin)
    except ImportError:
        import select  # type: ignore
        r, _, _ = select.select([sys.stdin], [], [], 0)
        rfds = list(r)
    return rfds

# ---------- Fehlerbehandlung ----------
def explain_error(resp: Optional[requests.Response], exc: Optional[Exception]) -> str:
    if resp is not None:
        sc = resp.status_code
        if sc == 429:
            return "429 Too Many Requests – zu viele Anfragen in kurzer Zeit."
        if sc == 403:
            return "403 Forbidden – Zugriff verweigert/Anti‑Bot."
        if sc == 503:
            return "503 Service Unavailable – temporär nicht verfügbar."
        if 400 <= sc < 500:
            return f"{sc} Client Error – ungültige/unauthorisierte Anfrage."
        if 500 <= sc < 600:
            return f"{sc} Server Error – später erneut versuchen."
        return f"{sc} Unerwarteter Status."
    if exc is not None:
        return f"Netz-/Timeout-Fehler: {exc}"
    return "Unbekannter Fehler."

def handle_error_pause(resp: Optional[requests.Response], exc: Optional[Exception], context: str = "") -> bool:
    # Kompakte INFO: nur kurze Kerninfos
    msg = explain_error(resp, exc)
    body = ""
    if resp is not None:
        try:
            body = resp.text[:200]
        except Exception:
            body = ""
    with _PROMPT_LOCK:
        if context:
            logging.error("ERR @%s", context)
        logging.error("ERR %s", msg)
        if body:
            logging.error("BODY %s", body)
        logging.info("Pause 15s …")
        time.sleep(15)
        ans = prompt_with_timeout("Abbrechen?")
        if ans and ans.lower().startswith("j"):
            logging.info("Abbruch.")
            return False
        logging.info("Weiter.")
        return True

# ---------- Feed & Requests ----------
def build_members_url(base_url: str, page: int) -> str:
    parsed = urlparse(base_url.strip())
    path = parsed.path or "/"
    if not path.endswith("/"):
        path += "/"
    if "memberslistxml/" not in path:
        path += "memberslistxml/"
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["xml"] = "1"
    q["p"] = str(page)
    new_parsed = parsed._replace(path=path, query=urlencode(q, doseq=True))
    return urlunparse(new_parsed)

def safe_request(session: requests.Session, method: str, url: str,
                 headers: Optional[Dict[str, str]] = None, cookies: Optional[Dict[str, str]] = None,
                 data: Optional[Dict[str, str]] = None, timeout: int = 30, retries: int = 3,
                 context: str = "") -> Optional[requests.Response]:
    attempt = 1
    while attempt <= retries:
        logging.info("%s %d/%d → %s", method, attempt, retries, url)
        try:
            hdrs = dict(headers or {})
            if cookies:
                sid = cookies.get("sessionid", "")
                sls = cookies.get("steamLoginSecure", "")
                hdrs["Cookie"] = f"sessionid={sid};steamLoginSecure={sls}"
            resp = session.request(method=method, url=url, headers=hdrs, cookies=cookies, data=data, timeout=timeout)
            logging.info("Status %s", resp.status_code)
            if 200 <= resp.status_code < 300:
                return resp
            cont = handle_error_pause(resp, None, context=context)
            if not cont:
                return None
            attempt += 1
            continue
        except (requests.Timeout, requests.ConnectionError) as e:
            cont = handle_error_pause(None, e, context=context)
            if not cont:
                return None
            attempt += 1
            continue
        except Exception as e:
            cont = handle_error_pause(None, e, context=context)
            if not cont:
                return None
            attempt += 1
            continue
    logging.error("Aufgegeben nach %d Versuchen.", retries)
    return None

def parse_member_page(xml_text: str, fallback_page: int) -> Tuple[List[str], Dict[str, int]]:
    root = ET.fromstring(xml_text)
    total_pages_text = root.findtext("totalPages")
    current_page_text = root.findtext("currentPage")
    try:
        total_pages = int(total_pages_text) if total_pages_text is not None else 1
    except ValueError:
        total_pages = 1
    try:
        current_page = int(current_page_text) if current_page_text is not None else fallback_page
    except ValueError:
        current_page = fallback_page
    members_elem = root.find("members")
    members: List[str] = []
    if members_elem is not None:
        for sid in members_elem.findall("steamID64"):
            if sid.text:
                members.append(sid.text.strip())
    logging.info("Seite %d/%d → %d IDs", current_page, total_pages, len(members))
    return members, {"totalPages": total_pages, "currentPage": current_page}

def get_page_members(session: requests.Session, base_url: str, page: int) -> Optional[Tuple[List[str], Dict[str, int]]]:
    full_url = build_members_url(base_url, page)
    resp = safe_request(session, "GET", full_url, headers=DEFAULT_HEADERS, context=f"GET p={page}")
    if resp is None:
        return None
    xml_text = resp.text or ""
    return parse_member_page(xml_text, fallback_page=page)

# ---------- Kombinierter Progress (Fetch + Block) ----------
def run_group_with_single_progress(group: str, max_needed: Optional[int], cookies: Optional[dict],
                                   dry_run: bool, mode: str, concurrency: int, referer_mode: str) -> Tuple[int,int,int]:
    # Erste Seite: total_pages ermitteln
    members_all: list[str] = []
    fetched_pages = 0
    total_pages = 1
    with requests.Session() as session:
        first = get_page_members(session, group, 1)
        if first is None:
            return (0, 0, 0)
        m1, meta = first
        total_pages = int(meta.get("totalPages", 1))
        members_all.extend(m1)
        fetched_pages = 1

    # Vorläufige Auswahl
    if max_needed and len(members_all) >= max_needed:
        selected = members_all[:max_needed]
    else:
        selected = list(dict.fromkeys(members_all))

    # Kompakter Gesamtbalken
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.fields[mode]} • {task.fields[group_short]} • p:{task.fields[pages]}/{task.fields[total_pages]} • ids:{task.fields[ids]} • ok:{task.fields[ok]} • err:{task.fields[err]}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:

        group_short = (group if len(group) <= 42 else group[:39] + "…")
        task = progress.add_task(
            "Gesamt",
            total=total_pages,  # später +len(selected)
            mode=("BLK" if mode == "block" else "UNBLK"),
            group_short=group_short,
            pages=1,
            total_pages=total_pages,
            ids=len(selected),
            ok=0,
            err=0,
        )

        # Restseiten holen
        if fetched_pages < total_pages and (not max_needed or len(selected) < max_needed):
            with requests.Session() as session:
                for p in range(2, total_pages + 1):
                    res = get_page_members(session, group, p)
                    if res is None:
                        break
                    mp, _ = res
                    selected.extend(mp)
                    fetched_pages += 1
                    progress.update(task, advance=1, pages=fetched_pages, ids=min(len(selected), max_needed or len(selected)))
                    if len(mp) < 1000 or (max_needed and len(selected) >= max_needed):
                        break

        # Deduplizieren + limitieren
        selected = list(dict.fromkeys(selected))
        if max_needed:
            selected = selected[:max_needed]

        # Ziel um Block-Phase erweitern
        progress.update(task, total=total_pages + len(selected))

        # Block-Phase
        ok = 0
        err = 0
        if dry_run:
            for _sid in selected:
                progress.update(task, advance=1)
        else:
            with requests.Session() as sess:
                def block_user_web(steamid: str, session: requests.Session, cookies: Dict[str, str],
                                   mode: str, referer_mode: str, group_url: Optional[str], timeout: int = 30) -> bool:
                    url = "https://steamcommunity.com/actions/BlockUserAjax"
                    referer = group_url if (referer_mode == "group" and group_url) else f"https://steamcommunity.com/profiles/{steamid}"
                    headers = {
                        "User-Agent": DEFAULT_HEADERS["User-Agent"],
                        "Referer": referer,
                        "Origin": "https://steamcommunity.com",
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    }
                    form = {
                        "sessionID": cookies.get("sessionid", ""),
                        "steamid": str(steamid),
                        "block": "1" if mode == "block" else "0",
                        "ajax": "1",
                        "json": "1",
                    }
                    resp = safe_request(session, "POST", url, headers=headers, cookies=cookies, data=form, timeout=timeout,
                                        context=f"POST sid={steamid} {mode}")
                    if resp is None:
                        return False
                    ok_local = resp.ok
                    try:
                        if resp.headers.get("Content-Type", "").startswith("application/json"):
                            js = resp.json()
                            ok_local = ok_local and bool(js.get("success", True))
                    except Exception:
                        pass
                    return ok_local

                def worker(sid: str) -> Tuple[str, bool]:
                    return sid, block_user_web(
                        steamid=sid,
                        session=sess,
                        cookies=cookies or {},
                        mode=mode,
                        referer_mode=referer_mode,
                        group_url=group
                    )

                if concurrency <= 1:
                    for sid in selected:
                        _, success = worker(sid)
                        if success: ok += 1
                        else: err += 1
                        progress.update(task, advance=1, ok=ok, err=err)
                else:
                    with ThreadPoolExecutor(max_workers=concurrency) as ex:
                        futures = {ex.submit(worker, sid): sid for sid in selected}
                        for fut in as_completed(futures):
                            sid = futures[fut]
                            success = False
                            try:
                                _sid, success = fut.result()
                            except Exception as e:
                                cont = handle_error_pause(None, e, context=f"worker sid={sid}")
                                if not cont:
                                    ex.shutdown(cancel_futures=True)
                                    break
                                success = False
                            if success: ok += 1
                            else: err += 1
                            progress.update(task, advance=1, ok=ok, err=err)

        return (len(selected), ok, err)

# ---------- I/O ----------
def read_groups_file(path: Path) -> List[str]:
    groups: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        groups.append(s)
    logging.info("Datei %s → %d Gruppen", path.name, len(groups))
    return groups

def process_groups(
    groups: Iterable[str],
    max_per_group: int,
    sessionid: Optional[str],
    steam_login_secure: Optional[str],
    dry_run: bool,
    mode: str,
    concurrency: int,
    referer_mode: str,
) -> None:
    total_selected = total_ok = total_err = 0
    cookies = {"sessionid": sessionid, "steamLoginSecure": steam_login_secure} if (sessionid and steam_login_secure) else None
    if cookies is None:
        dry_run = True
        logging.warning("Keine Cookies → DRY RUN")

    for group in groups:
        console.rule(f"[bold]{('BLK' if mode=='block' else 'UNBLK')}[/] {group}")
        selected, ok, err = run_group_with_single_progress(
            group=group,
            max_needed=(max_per_group if max_per_group > 0 else None),
            cookies=cookies,
            dry_run=dry_run,
            mode=mode,
            concurrency=concurrency,
            referer_mode=referer_mode,
        )
        total_selected += selected
        total_ok += ok
        total_err += err

    logging.info("Fertig: sel=%d ok=%d err=%d", total_selected, total_ok, total_err)
    if total_err > 0:
        ts = int(time.time())
        out = Path(f"failed-{ts}.txt")
        out.write_text("", encoding="utf-8")  # optional: Fehlerliste hier schreiben, falls gesammelt
        logging.info("Fehlerliste: %s", out.resolve())

# ---------- Main ----------
def main():
    config_path = Path(os.getenv("CONFIG_PATH", "config.toml")).resolve()
    cfg = load_config(config_path)

    general = get_cfg(cfg, "general", {})
    log_level = str(get_cfg(general, "log_level", "INFO")).upper()

    # Kompaktes Logging via Rich
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
    )

    groups: List[str] = []
    groups_file = get_cfg(general, "groups_file", None)
    group_url = get_cfg(general, "group_url", None)
    if groups_file:
        p = Path(groups_file).expanduser().resolve()
        if not p.exists():
            logging.error("groups file not found: %s", p)
            sys.exit(2)
        groups.extend(read_groups_file(p))
    if group_url:
        groups.append(group_url)
    if not groups:
        logging.error("Konfiguration ohne Gruppen; setze general.groups_file oder general.group_url")
        sys.exit(2)

    max_per_group = int(get_cfg(general, "max_per_group", 0))
    dry_run = bool(get_cfg(general, "dry_run", False))

    cookies_cfg = get_cfg(cfg, "cookies", {})
    use_env = bool(get_cfg(cookies_cfg, "use_env", True))
    sessionid = os.getenv("SESSIONID") if use_env else get_cfg(cookies_cfg, "sessionid", None)
    steam_login_secure = os.getenv("STEAMLOGINSECURE") if use_env else get_cfg(cookies_cfg, "steamLoginSecure", None)
    if not sessionid or not steam_login_secure:
        logging.warning("Cookies fehlen → DRY RUN")
        dry_run = True

    block_cfg = get_cfg(cfg, "block", {})
    mode = str(get_cfg(block_cfg, "mode", "block")).lower()
    if mode not in ("block", "unblock"):
        logging.error("Ungültiger block.mode: %s", mode)
        sys.exit(2)
    concurrency = int(get_cfg(block_cfg, "concurrency", 1))
    referer_mode = str(get_cfg(block_cfg, "referer", "profile")).lower()
    if referer_mode not in ("profile", "group"):
        referer_mode = "profile"

    process_groups(
        groups=groups,
        max_per_group=max(0, max_per_group),
        sessionid=sessionid,
        steam_login_secure=steam_login_secure,
        dry_run=dry_run,
        mode=mode,
        concurrency=concurrency,
        referer_mode=referer_mode,
    )

if __name__ == "__main__":
    main()