"""Bepul tarjima xizmatlari zanjiri: biri ishlamasa, keyingisiga o'tadi."""
import logging
from urllib.parse import quote

import httpx

log = logging.getLogger("translator")

MAX_CHUNK = 450  # MyMemory limiti ~500 belgi


def _chunks(text: str, size: int = MAX_CHUNK) -> list[str]:
    """Matnni qatorlar/jumlalar bo'yicha bo'laklarga ajratadi."""
    parts, cur = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > size:
            cut = line.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:cut])
            line = line[cut:]
        if len(cur) + len(line) > size:
            parts.append(cur)
            cur = ""
        cur += line
    if cur:
        parts.append(cur)
    return parts


async def _google(client: httpx.AsyncClient, text: str, target: str) -> str:
    r = await client.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text},
    )
    r.raise_for_status()
    return "".join(seg[0] for seg in r.json()[0] if seg[0])


async def _lingva(client: httpx.AsyncClient, text: str, target: str) -> str:
    tl = target.split("-")[0] if target != "zh-CN" else "zh"
    r = await client.get(
        f"https://lingva.ml/api/v1/auto/{tl}/{quote(text, safe='')}"
    )
    r.raise_for_status()
    return r.json()["translation"]


async def _mymemory(client: httpx.AsyncClient, text: str, target: str) -> str:
    # MyMemory "auto" qo'llamaydi, shuning uchun manba tilini Google bilan aniqlaymiz
    src = await _detect(client, text)
    if src == target:
        return text
    r = await client.get(
        "https://api.mymemory.translated.net/get",
        params={"q": text, "langpair": f"{src}|{target}"},
    )
    r.raise_for_status()
    data = r.json()
    if data.get("responseStatus") != 200:
        raise RuntimeError(data.get("responseDetails"))
    return data["responseData"]["translatedText"]


async def _detect(client: httpx.AsyncClient, text: str) -> str:
    try:
        r = await client.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text[:200]},
        )
        r.raise_for_status()
        return r.json()[2]
    except Exception:
        return "en"


PROVIDERS = [("google", _google), ("lingva", _lingva), ("mymemory", _mymemory)]


async def translate_text(text: str, target: str) -> str:
    async with httpx.AsyncClient(
        timeout=15, headers={"User-Agent": "Mozilla/5.0"}
    ) as client:
        out = []
        for chunk in _chunks(text):
            if not chunk.strip():
                out.append(chunk)
                continue
            for name, fn in PROVIDERS:
                try:
                    out.append(await fn(client, chunk, target))
                    break
                except Exception as e:
                    log.warning("%s ishlamadi: %r", name, e)
            else:
                raise RuntimeError("Barcha tarjima xizmatlari ishlamadi")
        return "".join(out)
