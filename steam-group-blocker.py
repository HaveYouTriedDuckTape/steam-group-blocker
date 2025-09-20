#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Python 3.11+: tomllib
try:
    import tomllib
except Exception as e:
    raise SystemExit("Python 3.11+ mit tomllib wird benötigt") from e

# Retries/Adapters
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Process-Isolation (Watchdog pro Gruppe)
import multiprocessing as mp

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
load_dotenv()

# ---------- HTTP Defaults ----------
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# ---------- urllib3-Logs dämpfen ----------
def quiet_urllib3_logging(http_cfg: dict):
    suppress = bool(get_cfg(http_cfg, "suppress_pool_warnings", True))
    if suppress:
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

# ---------- Session mit Retries/Timeouts/Pool ----------
def make_session(http_cfg: dict) -> requests.Session:
    retries_total = int(get_cfg(http_cfg, "retries_total", 3))
    retries_backoff = float(get_cfg(http_cfg, "retries_backoff", 0.5))
    pool_conns = int(get_cfg(http_cfg, "pool_connections", 20))
    pool_size = int(get_cfg(http_cfg, "pool_maxsize", 50))
    pool_block = bool(get_cfg(http_cfg, "pool_block", False))
    retry = Retry(
        total=retries_total,
        backoff_factor=retries_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_conns,
        pool_maxsize=pool_size,
        pool_block=pool_block,
    )
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

# ---------- Prompt/Fehler ----------
_PROMPT_LOCK = threading.Lock()

def prompt_with_timeout(prompt: str, timeout_sec: int) -> Optional[str]:
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

def explain_error(resp: Optional[requests.Response], exc: Optional[Exception]) -> str:
    if resp is not None:
        sc = resp.status_code
        if sc == 429: return "429 Too Many Requests"
        if sc == 403: return "403 Forbidden"
        if sc == 503: return "503 Service Unavailable"
        if 400 <= sc < 500: return f"{sc} Client Error"
        if 500 <= sc < 600: return f"{sc} Server Error"
        return f"{sc} Unexpected"
    if exc is not None:
        return f"Netz-/Timeout: {exc}"
    return "Unbekannt"

def handle_error(config: dict, resp: Optional[requests.Response], exc: Optional[Exception], context: str = "") -> bool:
    general = get_cfg(config, "general", {})
    interactive = bool(get_cfg(general, "interactive_errors", False))
    pause_s = int(get_cfg(general, "error_pause_seconds", 15))
    prompt_s = int(get_cfg(general, "prompt_timeout_seconds", 15))

    msg = explain_error(resp, exc)
    body = ""
    if resp is not None:
        try:
            body = resp.text[:200]
        except Exception:
            body = ""
    if context:
        logging.error("ERR @%s", context)
    logging.error("ERR %s", msg)
    if body:
        logging.error("BODY %s", body)

    if not interactive:
        if pause_s > 0:
            logging.info("Weiter ohne Prompt (non-interactive).")
        return True

    with _PROMPT_LOCK:
        if pause_s > 0:
            logging.info("Pause %ds …", pause_s)
            time.sleep(pause_s)
        ans = prompt_with_timeout("Abbrechen?", timeout_sec=prompt_s)
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

def safe_request(config: dict, session: requests.Session, method: str, url: str,
                 headers: Optional[Dict[str, str]] = None, cookies: Optional[Dict[str, str]] = None,
                 data: Optional[Dict[str, str]] = None, context: str = "") -> Optional[requests.Response]:
    http_cfg = get_cfg(config, "http", {})
    ct = float(get_cfg(http_cfg, "connect_timeout", 5.0))
    rt = float(get_cfg(http_cfg, "read_timeout", 20.0))
    timeout = (ct, rt)

    attempt = 1
    max_attempts = int(get_cfg(http_cfg, "retries_total", 3)) + 1

    while attempt <= max_attempts:
        logging.info("%s %d/%d → %s", method, attempt, max_attempts, url)
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
            cont = handle_error(config, resp, None, context=context)
            if not cont:
                return None
            attempt += 1
            continue
        except (requests.Timeout, requests.ConnectionError) as e:
            cont = handle_error(config, None, e, context=context)
            if not cont:
                return None
            attempt += 1
            continue
        except Exception as e:
            cont = handle_error(config, None, e, context=context)
            if not cont:
                return None
            attempt += 1
            continue
    logging.error("Aufgegeben nach %d Versuchen.", max_attempts)
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

def get_page_members(config: dict, session: requests.Session, base_url: str, page: int) -> Optional[Tuple[List[str], Dict[str, int]]]:
    full_url = build_members_url(base_url, page)
    resp = safe_request(config, session, "GET", full_url, headers=DEFAULT_HEADERS, context=f"GET p={page}")
    if resp is None:
        return None
    xml_text = resp.text or ""
    return parse_member_page(xml_text, fallback_page=page)

# ---------- Helfer ----------
def chunks(lst: List[str], size: int) -> Iterable[List[str]]:
    if size <= 0:
        yield lst
    else:
        for i in range(0, len(lst), size):
            yield lst[i:i+size]

# ---------- Kombinierter Progress ----------
def run_group_with_single_progress(config: dict, group: str, max_needed: Optional[int],
                                   cookies: Optional[dict], dry_run: bool, mode: str,
                                   concurrency: int, referer_mode: str) -> Tuple[int,int,int]:
    http_cfg = get_cfg(config, "http", {})
    s = make_session(http_cfg)

    members_all: list[str] = []
    fetched_pages = 0
    total_pages = 1

    first = get_page_members(config, s, group, 1)
    if first is None:
        s.close()
        return (0, 0, 0)
    m1, meta = first
    total_pages = int(meta.get("totalPages", 1))
    members_all.extend(m1)
    fetched_pages = 1

    if max_needed and len(members_all) >= max_needed:
        selected = members_all[:max_needed]
    else:
        selected = list(dict.fromkeys(members_all))

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
            total=total_pages,
            mode=("BLK" if mode == "block" else "UNBLK"),
            group_short=group_short,
            pages=1,
            total_pages=total_pages,
            ids=len(selected),
            ok=0,
            err=0,
        )

        if fetched_pages < total_pages and (not max_needed or len(selected) < max_needed):
            for p in range(2, total_pages + 1):
                res = get_page_members(config, s, group, p)
                if res is None:
                    break
                mp_ids, _ = res
                selected.extend(mp_ids)
                fetched_pages += 1
                progress.update(task, advance=1, pages=fetched_pages, ids=min(len(selected), max_needed or len(selected)))
                if len(mp_ids) < 1000 or (max_needed and len(selected) >= max_needed):
                    break

    s.close()

    selected = list(dict.fromkeys(selected))
    if max_needed:
        selected = selected[:max_needed]

    ok = 0
    err = 0

    block_cfg = get_cfg(config, "block", {})
    batch_size = int(get_cfg(block_cfg, "batch_size", 50))
    fail_max = int(get_cfg(block_cfg, "breaker_fail_max", 10))
    err_rate_max = float(get_cfg(block_cfg, "breaker_error_rate", 0.3))
    per_task_to = float(get_cfg(block_cfg, "per_task_timeout_seconds", 30.0))
    wait_to = float(get_cfg(block_cfg, "executor_wait_timeout_seconds", 30.0))
    fallback_seq = bool(get_cfg(block_cfg, "fallback_to_sequential", True))

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
        task = progress.add_task(
            "Gesamt",
            total=total_pages + len(selected),
            mode=("BLK" if mode == "block" else "UNBLK"),
            group_short=(group if len(group) <= 42 else group[:39] + "…"),
            pages=total_pages,
            total_pages=total_pages,
            ids=len(selected),
            ok=0,
            err=0,
        )

        if dry_run:
            for _sid in selected:
                progress.update(task, advance=1)
            return (len(selected), 0, 0)

        # Pool-/Concurrency-Kopplung: Concurrency nicht größer als pool_maxsize
        pool_size = int(get_cfg(http_cfg, "pool_maxsize", 50))
        current_conc = max(1, min(concurrency, pool_size))

        sblk = make_session(http_cfg)
        fail_streak = 0

        def block_user_web(steamid: str) -> bool:
            url = "https://steamcommunity.com/actions/BlockUserAjax"
            referer = group if (referer_mode == "group" and group) else f"https://steamcommunity.com/profiles/{steamid}"
            headers = {
                "User-Agent": DEFAULT_HEADERS["User-Agent"],
                "Referer": referer,
                "Origin": "https://steamcommunity.com",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
            form = {
                "sessionID": (cookies or {}).get("sessionid", ""),
                "steamid": str(steamid),
                "block": "1" if mode == "block" else "0",
                "ajax": "1",
                "json": "1",
            }
            resp = safe_request(config, sblk, "POST", url, headers=headers, cookies=cookies, data=form,
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

        for batch in chunks(selected, batch_size):
            if current_conc <= 1:
                for sid in batch:
                    success = block_user_web(sid)
                    if success:
                        ok += 1
                        fail_streak = 0
                    else:
                        err += 1
                        fail_streak += 1
                    progress.update(task, advance=1, ok=ok, err=err)
                    if fail_streak >= fail_max:
                        logging.warning("Breaker open: fail_streak=%d >= %d → Gruppe abgebrochen", fail_streak, fail_max)
                        sblk.close()
                        return (len(selected), ok, err)
            else:
                with ThreadPoolExecutor(max_workers=current_conc) as ex:
                    futures = [ex.submit(block_user_web, sid) for sid in batch]
                    done, not_done = wait(futures, timeout=wait_to, return_when=FIRST_COMPLETED)
                    if not_done:
                        done2, not_done2 = wait(not_done, timeout=wait_to)
                        done = set(list(done) + list(done2))
                        not_done = not_done2

                    for fut in done:
                        success = False
                        try:
                            success = fut.result(timeout=per_task_to)
                        except Exception as e:
                            _ = handle_error(config, None, e, context="worker result")
                            success = False
                        if success:
                            ok += 1
                            fail_streak = 0
                        else:
                            err += 1
                            fail_streak += 1
                        progress.update(task, advance=1, ok=ok, err=err)
                        if fail_streak >= fail_max:
                            logging.warning("Breaker open: fail_streak=%d >= %d → Gruppe abgebrochen", fail_streak, fail_max)
                            sblk.close()
                            return (len(selected), ok, err)

                    for fut in not_done:
                        fut.cancel()
                        err += 1
                        fail_streak += 1
                        progress.update(task, advance=1, ok=ok, err=err)
                        if fail_streak >= fail_max:
                            logging.warning("Breaker open: fail_streak=%d >= %d → Gruppe abgebrochen", fail_streak, fail_max)
                            sblk.close()
                            return (len(selected), ok, err)

            total_so_far = ok + err
            err_rate = (err / total_so_far) if total_so_far else 0.0
            if err_rate > err_rate_max:
                logging.warning("Hohe Fehlerquote %.0f%% > %.0f%%", err_rate*100, err_rate_max*100)
                if fallback_seq and current_conc > 1:
                    logging.info("Downgrade: Parallelität %d → 1 (sequentiell)", current_conc)
                    current_conc = 1
                else:
                    logging.info("Gruppe wird beendet (Stabilität).")
                    sblk.close()
                    return (len(selected), ok, err)

        sblk.close()
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

# ---------- Top-level Worker für Spawn (Windows) ----------
def group_worker_entry(q: mp.Queue, cfg: dict, grp: str, need, cks: Optional[dict],
                       dr: bool, md: str, conc: int, ref: str):
    try:
        res = run_group_with_single_progress(cfg, grp, need, cks, dr, md, conc, ref)
    except Exception as e:
        logging.error("Group worker exception: %s", e)
        res = (0, 0, 0)
    try:
        q.put(res)
    except Exception:
        pass

# ---------- Gruppenlauf mit Watchdog ----------
def run_group_with_watchdog(config: dict, group: str, max_needed: Optional[int], cookies: Optional[dict],
                            dry_run: bool, mode: str, concurrency: int, referer_mode: str) -> Tuple[int,int,int]:
    general = get_cfg(config, "general", {})
    group_to = int(get_cfg(general, "group_timeout_seconds", 600))
    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue()
    p = ctx.Process(
        target=group_worker_entry,
        args=(q, config, group, max_needed, cookies, dry_run, mode, concurrency, referer_mode),
    )
    p.start()
    p.join(group_to)
    if p.is_alive():
        logging.error("Watchdog: group timeout (%ds) → Terminate %s", group_to, group)
        p.terminate()
        p.join(5)
        return (0, 0, 0)
    try:
        return q.get_nowait()
    except Exception:
        return (0, 0, 0)

# ---------- Hauptablauf ----------
def process_groups(config: dict, groups: Iterable[str], max_per_group: int,
                   sessionid: Optional[str], steam_login_secure: Optional[str],
                   dry_run: bool, mode: str, concurrency: int, referer_mode: str) -> None:
    total_selected = total_ok = total_err = 0
    cookies = {"sessionid": sessionid, "steamLoginSecure": steam_login_secure} if (sessionid and steam_login_secure) else None
    if cookies is None:
        dry_run = True
        logging.warning("Keine Cookies → DRY RUN")

    for group in groups:
        console.rule(f"[bold]{('BLK' if mode=='block' else 'UNBLK')}[/] {group}")
        selected, ok, err = run_group_with_watchdog(
            config=config,
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

# ---------- Main ----------
def main():
    config_path = Path(os.getenv("CONFIG_PATH", "config.toml")).resolve()
    cfg = load_config(config_path)

    general = get_cfg(cfg, "general", {})
    log_level = str(get_cfg(general, "log_level", "INFO")).upper()

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
    )

    # urllib3-Logs dämpfen (Pool-Warnungen unterdrücken)
    http_cfg = get_cfg(cfg, "http", {})
    quiet_urllib3_logging(http_cfg)

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
        config=cfg,
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
    mp.freeze_support()
    main()