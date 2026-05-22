import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


MEDIA_TAG_FIELDS = ["screen_size", "frame_rate", "video_codec", "audio_codec", "audio_channels"]

DEFAULT_MEDIA_TAG_ORDER = ["screen_size", "frame_rate", "video_codec", "audio_codec", "audio_channels"]

DEFAULT_MEDIA_EXTENSIONS = "mkv;mp4;avi;ts;mov;wmv;iso;m2ts;rmvb;flv;m4v;webm"
DEFAULT_METADATA_EXTENSIONS = "nfo;ass;ssa;srt;sub;idx;sup;vtt;jpg;jpeg;png;webp;bmp"

MAX_FILENAME_BYTES = 235

GENERIC_MEDIA_DIR_NAMES = {
    "电影", "影片", "movie", "movies",
    "电视剧", "剧集", "连续剧", "tv", "tv shows", "shows", "series",
    "动漫", "动画", "anime", "media", "video", "videos", "视频",
}

KNOWN_RELEASE_GROUPS = {
    "CHD", "CHDBits", "CHDTV", "CHDWEB", "CHDPAD", "CHDHKTV",
    "WiKi", "MTeam", "MTeamTV", "ADE", "ADWeb",
    "HDS", "HDSky", "HDH", "HDC", "HDArea", "HDChina", "HDCTV",
    "NTb", "NTG", "NTROPiC", "FraMeSToR",
    "TLF", "TLFCD", "TLFGROUP",
    "OurBits", "OurTV", "OurPanda", "iHD", "OPS",
    "PuTao", "Pter", "PTHome",
    "DDR", "TJUPT", "JOY", "BMDru",
    "FRDS", "GREENOTEA", "DBD", "DKB", "PandaMoon",
    "NF", "AMZN", "ATV", "DSNP", "HMAX", "MAX", "iT",
    "Sicario", "Telly", "TEPES", "BTN", "TRD", "Pandamonium",
    "BiliBili", "ByRA", "ByMQ", "NowYS", "QHstudIo", "RARBG",
    "YTS", "YIFY", "EVO", "GalaxyRG", "MeGusta",
    "FFans", "MNHD", "MTeamWEB",
}

KNOWN_RELEASE_GROUPS_CI = {g.lower() for g in KNOWN_RELEASE_GROUPS}

CHINESE_SUB_TAG_RE = re.compile(
    r"[\[【][^\]】]*?(?:字幕组|压制组|压制|字幕社|动漫国|fansub|sub|raws?|喵萌|霜庭云花|爱恋|猎户|动音漫影|花园字幕组|风之圣殿|澄空学园|轻之国度|肉肉|纪伊宫|银光字幕组|Lilith[-\s]?Raws|ANi|VCB[- ]?Studio|DBD|DKB|喵萌奶茶屋|动漫之家)[^\]】]*?[\]】]",
    re.IGNORECASE,
)

ANIME_BRACKET_PATTERNS = (
    re.compile(r'\[[^\]]+\]'),
    re.compile(r'【[^】]+】'),
)

ANIME_EPISODE_RE = re.compile(
    r'\s+-\s*(\d{1,4})\s*(?:[\(（]|\[|【|$|[\s.])'
)

PART_LABEL_RE = re.compile(
    r'(?:^|[\s._\-\[])(CD|DVD|DISC|DISK|PART|PT)\s*[._-]?\s*(\d{1,2}|[IVX]+|[ABab])(?=[\s._\-\]]|$)',
    re.IGNORECASE,
)

VOL_LABEL_RE = re.compile(
    r'(?:^|[\s._\-\[])vol\.?\s*(\d{1,3})(?=[\s._\-\]]|$)',
    re.IGNORECASE,
)

CN_PART_LABEL_RE = re.compile(
    r'(?:^|[\s._\-\[（(【])(上集|下集|前篇|后篇|上篇|下篇|完结篇|大结局)(?=[\s._\-\])）】]|$)'
)

SPECIAL_EPISODE_RE = re.compile(
    r'(?:^|[\s._\-\[【])(OVA|OAD|SP|NCOP|NCED|PV|CM|MENU|MV|特别篇|番外篇|番外|剧场版|映画|预告片?|花絮|彩蛋)(?:\s*(\d{1,3}))?(?=[\s._\-\]】]|$)',
    re.IGNORECASE,
)


@dataclass
class RuleResult:
    matched: bool
    score: float = 0.0
    reasons: List[str] = field(default_factory=list)


def setting_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "开启"}
    return default


def as_first_int(value) -> Optional[int]:
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def chinese_number_to_int(value: str) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    digit_map = {
        "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    }
    if text in digit_map:
        return digit_map[text]
    if "百" in text:
        left, _, right = text.partition("百")
        hundreds = digit_map.get(left, 1 if left == "" else None)
        if hundreds is None:
            return None
        tail = chinese_number_to_int(right) if right else 0
        return hundreds * 100 + (tail or 0)
    if "十" in text:
        left, _, right = text.partition("十")
        tens = digit_map.get(left, 1 if left == "" else None)
        ones = digit_map.get(right, 0 if right == "" else None)
        if tens is None or ones is None:
            return None
        return tens * 10 + ones
    return None


def parse_episode_number(value) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    return chinese_number_to_int(raw)


def sanitize_filename(name: str) -> str:
    return (
        (name or "")
        .replace("/", "")
        .replace("\\", "")
        .replace(":", "：")
        .replace("*", "")
        .replace("?", "")
        .replace("\"", "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
        .strip()
    )


def is_same_generated_name(current_name: str, generated_name: str) -> bool:
    return (current_name or "").strip() == (generated_name or "").strip()


def is_season_dir_name(name: str) -> bool:
    value = (name or "").strip().lower()
    return bool(
        re.search(r'^(season|series)\s*\d{1,3}$', value)
        or re.search(r'^s\d{1,3}$', value)
        or re.search(r'^第\s*\d{1,3}\s*季$', value)
        or re.search(r'^第[一二三四五六七八九十百]+季$', value)
    )


def is_generic_media_dir(name: str) -> bool:
    return (name or "").strip().lower() in GENERIC_MEDIA_DIR_NAMES


def preprocess_dotted_filename(name: str) -> str:
    if (name or "").count(".") < 2:
        return name or ""
    m = re.search(r'[.\s](\d{4})[.\s]', name)
    if "." in name:
        base, ext = name.rsplit(".", 1)
    else:
        base, ext = name, ""
    if not m:
        if len(ext) <= 4:
            return base.replace(".", " ") + "." + ext
        return name.replace(".", " ")
    year_pos = m.start(1)
    prefix = name[:year_pos].replace(".", " ")
    suffix = name[year_pos:]
    return prefix + suffix


def parse_filename_with_guessit(name: str) -> dict:
    try:
        from guessit import guessit
    except Exception:
        return {}
    try:
        result = guessit(name or "")
        return {
            "title": result.get("title"),
            "year": result.get("year"),
            "season": result.get("season"),
            "episode": result.get("episode"),
            "screen_size": result.get("screen_size"),
            "frame_rate": result.get("frame_rate"),
            "source": result.get("source"),
            "video_codec": result.get("video_codec"),
            "audio_codec": result.get("audio_codec"),
            "audio_channels": result.get("audio_channels"),
            "release_group": result.get("release_group"),
            "edition": result.get("edition"),
            "type": result.get("type"),
        }
    except Exception:
        return {}


def apply_episode_fallbacks(name: str, result: dict) -> dict:
    parsed = dict(result or {})
    stem = str(name or "").rsplit(".", 1)[0]
    normalized = preprocess_dotted_filename(stem)
    compact = re.sub(r"[\s._\-]+", " ", normalized).strip()
    number_pattern = r"(\d{1,4}|[零〇一二两三四五六七八九十百]{1,6})"
    season_episode_patterns = [
        rf"(?:第\s*{number_pattern}\s*[季部])\s*第\s*{number_pattern}\s*[集话話回]",
        rf"(?:第\s*{number_pattern}\s*[季部])\s*[Ee][Pp]?\s*{number_pattern}",
        rf"(?:Season|Series)\s*{number_pattern}\s*(?:Episode|Ep|E)\s*{number_pattern}",
        rf"[Ss]\s*{number_pattern}\s*[Ee]\s*{number_pattern}",
        rf"{number_pattern}\s*[xX]\s*{number_pattern}",
    ]
    season = None
    episode = None
    matched_span = None
    for pattern in season_episode_patterns:
        m = re.search(pattern, compact, flags=re.IGNORECASE)
        if not m:
            continue
        season = parse_episode_number(m.group(1))
        episode = parse_episode_number(m.group(2))
        matched_span = m.span()
        break

    if episode is None:
        episode_patterns = [
            rf"(?:第\s*{number_pattern}\s*[集话話回期])",
            rf"(?:^|[\s._\-\[])(?:EP|Ep|ep|Episode|episode|E)\s*{number_pattern}(?:$|[\s._\-\]])",
            rf"(?:^|[\s._\-\[]){number_pattern}\s*(?:集|话|話|回|期)(?:$|[\s._\-\]:：])",
        ]
        for pattern in episode_patterns:
            m = re.search(pattern, compact, flags=re.IGNORECASE)
            if not m:
                continue
            episode = parse_episode_number(m.group(1))
            matched_span = m.span()
            break

    if season is not None and parsed.get("season") is None:
        parsed["season"] = season
    if episode is not None and parsed.get("episode") is None:
        parsed["episode"] = episode
    if parsed.get("episode") is not None and parsed.get("season") is None:
        parsed["season"] = 1

    if parsed.get("episode") is not None:
        parsed["type"] = "episode"
        title = str(parsed.get("title") or "").strip()
        if matched_span:
            title_prefix = compact[:matched_span[0]].strip(" ._-")
            title_prefix = re.sub(rf"(?:第\s*{number_pattern}\s*[季部])\s*$", "", title_prefix).strip(" ._-")
            if title_prefix:
                parsed["title"] = title_prefix
            elif title and re.fullmatch(
                rf"(?:第\s*{number_pattern}\s*[季部]\s*)?(?:第\s*{number_pattern}\s*[集话話回期]|EP\s*{number_pattern}|E\s*{number_pattern})",
                title,
                flags=re.IGNORECASE,
            ):
                parsed["title"] = None
    return parsed


_ABS_LEADING_EP_RE = re.compile(r"^(\d{3,4})(?:[.\s_\-]|$)")


def extract_leading_absolute_episode(name: str) -> Optional[int]:
    """文件名以 1156 / 1160-4K 这类绝对集数开头时提取（长篇动画常见）。"""
    stem = (name or "").rsplit(".", 1)[0].strip()
    m = _ABS_LEADING_EP_RE.match(stem)
    if not m:
        return None
    num = int(m.group(1))
    return num if num >= 100 else None


def fix_guessit_absolute_episode_split(name: str, parsed: dict) -> dict:
    """guessit 常把 1156 误判为 S11E56；此时优先采用开头的绝对集数。"""
    abs_ep = extract_leading_absolute_episode(name)
    if abs_ep is None:
        return parsed
    out = dict(parsed or {})
    g_season = as_first_int(out.get("season"))
    g_episode = as_first_int(out.get("episode"))
    if g_season is not None and g_episode is not None and g_season * 100 + g_episode == abs_ep:
        out["episode"] = abs_ep
        out.pop("season", None)
    else:
        out["episode"] = abs_ep
        if g_season is not None and g_episode is not None:
            out.pop("season", None)
    out["type"] = "episode"
    return out


def normalize_parsed_media(parsed: dict) -> dict:
    result = dict(parsed or {})
    result["season"] = as_first_int(result.get("season"))
    result["episode"] = as_first_int(result.get("episode"))
    title = str(result.get("title") or "").strip()
    year = result.get("year")
    if title and year:
        title = re.sub(rf"\s*[\(（]\s*{re.escape(str(year))}\s*[\)）]\s*$", "", title).strip()
        title = re.sub(rf"[\s._-]+{re.escape(str(year))}\s*$", "", title).strip()
        result["title"] = title
    if result.get("type") == "episode" and result.get("year") in (720, 1080, 2160, 4320):
        result["year"] = None
    return result


def parse_filename_strict(name: str) -> dict:
    # 先剥掉已整理过的 {tmdb-XXX} / [imdb-ttXXX] 等标签，避免 guessit 把 (YYYY) {tmdb-NNN} 当成 SYYYY EpNNN
    sanitized = strip_known_id_tags(name or "")

    if is_anime(sanitized):
        anime = parse_anime_filename(sanitized)
        if anime.get("title"):
            # 补充 media tags（anime 解析器不抽 screen_size/codec/audio 等，需要 guessit 补）
            clean = preprocess_dotted_filename(sanitized)
            guessit_result = parse_filename_with_guessit(clean)
            for tag_key in ("screen_size", "frame_rate", "video_codec",
                            "audio_codec", "audio_channels", "source"):
                if not anime.get(tag_key) and guessit_result.get(tag_key):
                    anime[tag_key] = guessit_result[tag_key]
            return anime

    clean = preprocess_dotted_filename(sanitized)
    result = fix_guessit_absolute_episode_split(
        sanitized,
        apply_episode_fallbacks(sanitized, parse_filename_with_guessit(clean)),
    )
    bracket_year = re.search(r'^\s*(.+?)\s*[\(（]\s*(\d{4})\s*[\)）]', clean)
    if bracket_year:
        bracket_title = bracket_year.group(1).strip(" ._-")
        if bracket_title:
            result["title"] = bracket_title
        if not result.get("year"):
            result["year"] = int(bracket_year.group(2))
    dotted = (name or "").count(".") >= 2
    if dotted and result.get("season") is None and result.get("episode") is None:
        m = re.search(r'^(.+?)[.\s](\d{4})', clean)
        if m:
            regex_title = m.group(1).strip()
            result_title = (result.get("title") or "").strip()
            if regex_title and len(regex_title) > len(result_title):
                result["title"] = regex_title
                if not result.get("year"):
                    result["year"] = int(m.group(2))
    if result.get("title"):
        result["title"] = strip_chinese_quality_tags(result["title"])
        result["title"] = strip_release_group_from_title(result["title"])
    return result


_CN_SEASON_SUFFIX_RE = re.compile(
    r'^(?P<title>.+?)[\s._\-]*第\s*(?P<num>[0-9]+|[零〇一二两三四五六七八九十百]+)\s*[季部]\s*$'
)
_EN_SEASON_SUFFIX_RE = re.compile(
    r'^(?P<title>.+?)[\s._\-]+(?:Season|Series)\s*0*(?P<num>\d{1,3})\s*$',
    re.IGNORECASE,
)
_TRAILING_NUMBER_RE = re.compile(r'(?P<title>.+?)[\s._\-]*(?P<num>\d{1,2})\s*$')


def strip_season_suffix(name: str) -> Tuple[str, Optional[int]]:
    raw = (name or "").strip()
    if not raw:
        return raw, None
    m = _CN_SEASON_SUFFIX_RE.match(raw)
    if m:
        season = chinese_number_to_int(m.group("num"))
        if season is not None:
            return m.group("title").strip(" ._-"), season
    m = _EN_SEASON_SUFFIX_RE.match(raw)
    if m:
        try:
            return m.group("title").strip(" ._-"), int(m.group("num"))
        except ValueError:
            return raw, None
    return raw, None


def strip_trailing_number(name: str) -> Tuple[str, Optional[int]]:
    raw = (name or "").strip()
    if not raw:
        return raw, None
    m = _TRAILING_NUMBER_RE.match(raw)
    if not m:
        return raw, None
    try:
        num = int(m.group("num"))
    except ValueError:
        return raw, None
    title_part = m.group("title").strip(" ._-")
    if not title_part:
        return raw, None
    return title_part, num


def parse_dir_name(name: str) -> dict:
    raw = (name or "").strip()
    # 修复用户场景：有时目录名末尾误带媒体扩展名（如 "xxx.mkv" 作为文件夹名）
    # 把这种伪扩展名剥掉再解析，避免 guessit 把扩展名也当 title 一部分
    for ext in ("mkv", "mp4", "avi", "ts", "mov", "wmv", "iso", "m2ts", "rmvb", "flv", "m4v", "webm"):
        if raw.lower().endswith("." + ext):
            raw = raw[: -(len(ext) + 1)]
            break
    # 剥掉已有的 {tmdb-XXX} / [imdb-ttXXX] 等元数据标签，防止 guessit 误把 (YYYY) {tmdb-NNN} 当 SYYYY EpNNN
    raw = strip_known_id_tags(raw).strip()

    def _clean(out: dict) -> dict:
        if out.get("title"):
            out["title"] = strip_chinese_quality_tags(out["title"])
            out["title"] = strip_release_group_from_title(out["title"])
        return out

    # 番剧目录名（含字幕组特征）：用 anime 解析器
    if is_anime(raw):
        anime = parse_anime_filename(raw)
        if anime.get("title"):
            return _clean(anime)

    m = re.search(r'^\s*(.+?)\s*[\(（]\s*(\d{4})\s*[\)）]\s*$', raw)
    if m:
        head, season = strip_season_suffix(m.group(1).strip())
        out = {"title": head, "year": int(m.group(2)), "type": "movie"}
        if season is not None:
            out["season"] = season
            out["type"] = "episode"
        return _clean(out)

    head, season = strip_season_suffix(raw)
    if season is not None and head:
        return _clean({"title": head, "season": season, "type": "episode"})

    result = parse_filename_with_guessit(raw)
    if result.get("title"):
        return _clean(result)

    m = re.search(r'(.+?)\s*\((\d{4})\)', raw)
    if m:
        head2, season2 = strip_season_suffix(m.group(1).strip())
        out = {"title": head2, "year": int(m.group(2)), "type": "movie"}
        if season2 is not None:
            out["season"] = season2
            out["type"] = "episode"
        return _clean(out)
    # 兜底：guessit 没识别出来，直接用原名（可能整个就是 title）
    if raw.strip():
        return _clean({"title": raw.strip(), "type": "movie"})
    return {}


def looks_like_work_dir_name(name: str) -> bool:
    if is_generic_media_dir(name) or is_season_dir_name(name):
        return False
    parsed = normalize_parsed_media(parse_dir_name(name))
    return bool(parsed.get("title"))


def looks_like_tv_file(parsed: dict, ancestors: list) -> RuleResult:
    reasons = []
    score = 0.0
    if parsed.get("season") is not None and parsed.get("episode") is not None:
        reasons.append("文件名匹配 S/E 模式")
        score += 0.7
    season_anc = next((name for _, name in ancestors if is_season_dir_name(name)), None)
    if season_anc:
        reasons.append(f"祖先目录是季目录: {season_anc!r}")
        score += 0.5
    if score >= 0.5:
        return RuleResult(True, min(score, 1.0), reasons)
    return RuleResult(False, score, reasons)


def pick_tv_show_info(ancestors: list, file_parsed: dict) -> Tuple[Optional[str], Optional[str], dict]:
    deepest_dir_id = ancestors[-1][0] if ancestors else None
    skip_deepest_as_season_container = False
    if deepest_dir_id and file_parsed.get("season") is not None and file_parsed.get("episode") is not None:
        for _, upper_name in ancestors[:-1]:
            if is_generic_media_dir(upper_name) or is_season_dir_name(upper_name):
                continue
            if normalize_parsed_media(parse_dir_name(upper_name)).get("title"):
                skip_deepest_as_season_container = True
                break
    for dir_id, dir_name in reversed(ancestors):
        if skip_deepest_as_season_container and str(dir_id) == str(deepest_dir_id):
            continue
        if is_season_dir_name(dir_name) or is_generic_media_dir(dir_name):
            continue
        parsed = normalize_parsed_media(parse_dir_name(dir_name))
        if parsed.get("title"):
            return dir_id, dir_name, parsed
    title = (file_parsed.get("title") or "").strip()
    return None, None, {
        "title": title,
        "year": file_parsed.get("year"),
        "season": file_parsed.get("season"),
        "episode": file_parsed.get("episode"),
        "type": "episode",
    }


def parse_season_dir_number(name: str) -> Optional[int]:
    """从 Season 00 / S01 / 第1季 等季目录名解析季号；0 表示特别篇。"""
    value = (name or "").strip().lower()
    m = re.search(r'^(?:season|series)\s*(\d{1,3})$', value)
    if m:
        return int(m.group(1))
    m = re.search(r'^s(\d{1,3})$', value)
    if m:
        return int(m.group(1))
    m = re.search(r'^第\s*(\d{1,3})\s*季$', value)
    if m:
        return int(m.group(1))
    m = re.search(r'^第([零〇一二两三四五六七八九十百]+)季$', value)
    if m:
        return chinese_number_to_int(m.group(1))
    return None


def build_season_folder_name(season: Optional[int], template: str = "") -> str:
    # season=0 是特别篇（Season 00），不能用 `season or 1` 否则会被当成第一季
    season_num = 1 if season is None else season
    tpl = template or "Season {season:02d}"
    try:
        return sanitize_filename(tpl.format(season=season_num))
    except Exception:
        return f"Season {season_num:02d}"


_TMDB_TAG_PATTERNS = (
    re.compile(r'\[tmdbid[=\-](\d+)\]'),
    re.compile(r'\[tmdb[=\-](\d+)\]'),
    re.compile(r'\{tmdbid[=\-](\d+)\}'),
    re.compile(r'\{tmdb[=\-](\d+)\}'),
    re.compile(r'\{\[\s*tmdbid\s*=\s*(\d+)\s*'),
)


# 已整理过的文件名常带 {tmdb-XXX} / [imdb-ttXXX] 等元数据标签。
# guessit 在「(YYYY) {tmdb-NNN} [...]」这种结构下会把 YYYY 当成 season、NNN 当成 episode，
# 把电影误判为剧集进而拉错 TMDB 条目，所以解析前要先把这些已知 ID 标签剥掉。
_KNOWN_ID_TAG_RE = re.compile(
    r'[\{\[]\s*(?:tmdb|tmdbid|imdb|imdbid|tvdb|tvdbid|douban|doubanid|bangumi|anidb)\s*[=\-:]\s*[^\}\]]+[\}\]]',
    re.IGNORECASE,
)


def strip_known_id_tags(name: str) -> str:
    """剥掉 {tmdb-XXX} / [imdb-ttXXX] 等已有的元数据标签，给 guessit 一个干净的串。"""
    if not name:
        return name or ""
    return _KNOWN_ID_TAG_RE.sub(" ", name)


def find_tmdb_id_in_name(name: str) -> str:
    raw = name or ""
    if not raw:
        return ""
    for pattern in _TMDB_TAG_PATTERNS:
        m = pattern.search(raw)
        if m:
            return m.group(1)
    return ""


def is_already_organized(filename: str, marker: str) -> bool:
    if not marker or not marker.strip():
        return False
    m = marker.strip()
    if m in ("tmdb", "tmdbid"):
        return bool(find_tmdb_id_in_name(filename))
    return f"[{m}]" in (filename or "")


def normalize_audio_codec(codec: str) -> str:
    codec = re.sub(r'\d+\.\d+$', '', (codec or "").lower().strip()).strip()
    mapping = {
        "dolby digital plus": "DDP",
        "dolby digital": "DD",
        "dolby truehd": "TrueHD",
        "dts-hd master audio": "DTS-HD MA",
        "dts-hd high resolution": "DTS-HD HRA",
        "dts": "DTS",
        "aac": "AAC",
        "mp3": "MP3",
        "flac": "FLAC",
        "pcm": "PCM",
        "opus": "Opus",
        "vorbis": "Vorbis",
        "wma": "WMA",
        "eac3": "DDP",
        "ac3": "DD",
        "truehd": "TrueHD",
        "ddp": "DDP",
        "dd": "DD",
        "dolby atmos": "",
        "atmos": "",
    }
    return mapping.get(codec, codec.upper())


def normalize_video_codec(codec: str) -> str:
    mapping = {
        "h.265": "H.265",
        "h.264": "H.264",
        "x265": "H.265",
        "x264": "H.264",
        "hevc": "H.265",
        "avc": "H.264",
        "av1": "AV1",
        "vp9": "VP9",
    }
    raw = (codec or "").lower().strip()
    return mapping.get(raw, codec.upper() if (codec or "").isalpha() else (codec or ""))


def normalize_frame_rate(value) -> Optional[str]:
    if value is None or value == "":
        return None
    raw = str(value).strip()
    bracket_match = re.search(r'\[([0-9]+(?:\.[0-9]+)?)\s*fps\]', raw, re.IGNORECASE)
    if bracket_match:
        raw = bracket_match.group(1)
    rational_match = re.match(r'^(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)$', raw)
    if rational_match:
        numerator = float(rational_match.group(1))
        denominator = float(rational_match.group(2))
        if denominator <= 0:
            return None
        fps = numerator / denominator
    else:
        plain_match = re.search(r'(\d+(?:\.\d+)?)', raw)
        if not plain_match:
            return None
        fps = float(plain_match.group(1))
    if fps <= 0:
        return None
    rounded = round(fps)
    if abs(fps - rounded) < 0.05:
        return f"{int(rounded)}fps"
    return f"{fps:.2f}".rstrip("0").rstrip(".") + "fps"


def normalize_media_tag_value(key: str, value):
    if value is None or value == "":
        return None
    if key == "frame_rate":
        return normalize_frame_rate(value)
    if key == "video_codec":
        return normalize_video_codec(str(value))
    if key == "audio_codec":
        values = value if isinstance(value, (list, tuple)) else [value]
        normalized = []
        for item in values:
            text = normalize_audio_codec(str(item))
            if text and text not in normalized:
                normalized.append(text)
        return normalized[0] if len(normalized) == 1 else normalized
    if key == "audio_channels":
        return str(value)
    return str(value)


def merge_aligned_media_tags(parsed: dict, defaults: dict) -> dict:
    result = dict(parsed or {})
    for key, value in (defaults or {}).items():
        if key not in MEDIA_TAG_FIELDS:
            continue
        current = normalize_media_tag_value(key, result.get(key))
        if current:
            continue
        if value:
            result[key] = value
    return result


def build_media_info_tags(parsed: dict, tag_order: Optional[list] = None) -> str:
    if tag_order is None:
        tag_order = DEFAULT_MEDIA_TAG_ORDER
    parts: List[str] = []
    for key in tag_order:
        if key == "screen_size":
            v = normalize_media_tag_value(key, parsed.get("screen_size"))
            if v:
                parts.append(v)
        elif key == "frame_rate":
            v = normalize_media_tag_value(key, parsed.get("frame_rate"))
            if v and v not in parts:
                parts.append(v)
        elif key == "video_codec":
            v = normalize_media_tag_value(key, parsed.get("video_codec"))
            if v:
                parts.append(v)
        elif key == "audio_codec":
            v = normalize_media_tag_value(key, parsed.get("audio_codec"))
            if v:
                items = v if isinstance(v, list) else [v]
                for item in items:
                    s = str(item)
                    if s and s not in parts:
                        parts.append(s)
        elif key == "audio_channels":
            v = normalize_media_tag_value(key, parsed.get("audio_channels"))
            if v:
                parts.append(v)
    return "[" + " ".join(parts) + "]" if parts else ""


def screen_size_from_dimensions(width, height) -> Optional[str]:
    try:
        width = int(width or 0)
        height = int(height or 0)
    except Exception:
        return None
    pixels = max(width, height)
    if pixels >= 7600:
        return "4320p"
    if pixels >= 3800:
        return "2160p"
    if pixels >= 1900:
        return "1080p"
    if pixels >= 1200:
        return "720p"
    if pixels >= 700:
        return "480p"
    return None


def audio_channels_label(channels) -> Optional[str]:
    try:
        channels = int(channels or 0)
    except Exception:
        return None
    return {
        1: "1.0",
        2: "2.0",
        3: "2.1",
        4: "4.0",
        5: "5.0",
        6: "5.1",
        7: "6.1",
        8: "7.1",
    }.get(channels, str(channels) if channels > 0 else None)


def extract_tmdb_display_fields(result: dict, media_type: str = "movie") -> tuple:
    if not result:
        return "", "", "", None
    release_date = result.get("release_date") or result.get("first_air_date") or ""
    result_year = int(release_date[:4]) if release_date and release_date[:4].isdigit() else None
    tmdb_id = str(result.get("id", "") or "")
    title = (result.get("title") or result.get("name") or "").strip()
    original = (result.get("original_title") or result.get("original_name") or "").strip()
    return tmdb_id, title, original, result_year


def pick_tmdb_match_for_year(results: list, expected_year: Optional[int], media_type: str) -> Optional[dict]:
    if not results:
        return None
    if not expected_year:
        return results[0]
    for item in results:
        _, _, _, result_year = extract_tmdb_display_fields(item, media_type)
        if result_year and abs(result_year - expected_year) <= 1:
            return item
    return None


def build_folder_name(parsed: dict, tmdb_id: str = "") -> str:
    title = (parsed.get("title") or "").strip()
    year = parsed.get("year")
    if not title:
        return ""
    tag = f"{{tmdb-{tmdb_id}}}" if tmdb_id else ""
    parts = [title]
    if year:
        parts.append(f"({year})")
    if tag:
        parts.append(tag)
    return " ".join(parts).strip()


def build_target_filename(parsed: dict, marker: str = "", tmdb_id: str = "") -> str:
    title = (parsed.get("title") or "").strip()
    year = parsed.get("year")
    season = as_first_int(parsed.get("season"))
    episode = as_first_int(parsed.get("episode"))

    if not title:
        return ""

    parts = [title]
    if year:
        parts.append(f"({year})")

    tag = ""
    if marker in ("tmdb", "tmdbid"):
        tag = f"{{tmdb-{tmdb_id}}}" if tmdb_id else ""
    elif marker and marker.strip() and marker not in ("tmdb", "tmdbid"):
        tag = f"[{marker.strip()}]"

    if tag:
        parts.append(tag)

    if season is not None and episode is not None:
        parts.append(f"S{season:02d}E{episode:02d}")

    return " ".join(parts)


def fit_filename_bytes(filename: str, tmdb_lang: str = "zh-CN") -> str:
    if len((filename or "").encode("utf-8")) <= MAX_FILENAME_BYTES:
        return filename or ""

    m = re.match(r'^(.+?) - (.+?) \((\d{4})\)(.*)$', filename)
    if m:
        title1, title2, year, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        if (tmdb_lang or "zh-CN").startswith("zh"):
            short = f"{title1} ({year}){rest}"
        else:
            short = f"{title2} ({year}){rest}"
        if len(short.encode("utf-8")) <= MAX_FILENAME_BYTES:
            return short
        filename = short

    matches = list(re.finditer(r'\[([^\]]+)\]', filename))
    if not matches:
        return filename
    m = matches[-1]
    tags = m.group(1).split()
    for i in range(len(tags), 0, -1):
        new_tag = "[" + " ".join(tags[:i]) + "]"
        short = filename[:m.start()] + new_tag + filename[m.end():]
        if len(short.encode("utf-8")) <= MAX_FILENAME_BYTES:
            return short
    short = filename[:m.start()] + filename[m.end():]
    return short


def split_basename(name: str) -> Tuple[str, str]:
    if not name or "." not in name:
        return name or "", ""
    base, ext = name.rsplit(".", 1)
    return base, ext


_META_EPISODE_TOKEN_RE = re.compile(
    r"(?:^|[\s._\-])S(\d{1,2})E(\d{1,4})(?:[\s._\-]|$)",
    re.IGNORECASE,
)

# 文件名末尾常见、不应被当成 release group 剥掉的短 token
_META_TAIL_BLOCKLIST = {
    "1", "2", "5", "7", "atmos", "ddp", "dts", "hevc", "sdr", "hdr", "dv", "nf", "web",
}


def strip_release_group_from_stem(stem: str, parsed: Optional[dict] = None) -> str:
    """从媒体主文件名（无扩展名）末尾剥掉 release group，便于和字幕/nfo 配对。"""
    raw = (stem or "").strip()
    if not raw:
        return raw

    parsed = parsed or {}
    release_group = str(parsed.get("release_group") or "").strip()
    if release_group:
        for sep in ("-", ".", "_"):
            suffix = f"{sep}{release_group}"
            if raw.endswith(suffix) and len(raw) > len(suffix):
                return raw[: -len(suffix)].rstrip("._- ")

    m = re.search(r"^(.*?)[\s._\-]+([A-Za-z0-9]{2,12})\s*$", raw)
    if m and m.group(2).lower() in KNOWN_RELEASE_GROUPS_CI:
        return m.group(1).rstrip("._- ") or raw

    m = re.search(r"^(.*?)\s*-\s*([A-Za-z0-9]{2,12})\s*$", raw)
    if m and m.group(2).lower() in KNOWN_RELEASE_GROUPS_CI:
        return m.group(1).rstrip("._- ") or raw

    # 兜底：末尾 -Group / .Group（含中文组名，如 -老K）
    m = re.search(
        r"^(.*?)[\-_.]([\w\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]{1,12})\s*$",
        raw,
    )
    if m:
        tail = m.group(2)
        if (
            not re.fullmatch(r"S\d+E\d+", tail, re.IGNORECASE)
            and tail.lower() not in _META_TAIL_BLOCKLIST
        ):
            head = m.group(1).rstrip("._- ")
            if head and len(head) >= max(8, len(raw) // 3):
                return head
    return raw


def build_meta_match_bases(stem: str, parsed: Optional[dict] = None) -> List[str]:
    """生成元数据配对用的 basename 候选，优先保留原始值，再尝试去掉 release group。"""
    raw = (stem or "").strip()
    if not raw:
        return []
    bases: List[str] = [raw]
    stripped = strip_release_group_from_stem(raw, parsed)
    if stripped and stripped != raw:
        bases.append(stripped)
    deduped: List[str] = []
    seen = set()
    for base in bases:
        if base not in seen:
            seen.add(base)
            deduped.append(base)
    return deduped


def extract_episode_token(name: str, parsed: Optional[dict] = None) -> Optional[str]:
    parsed = parsed or {}
    season = parsed.get("season")
    episode = parsed.get("episode")
    if season is not None and episode is not None:
        try:
            return f"S{int(season):02d}E{int(episode):02d}"
        except (TypeError, ValueError):
            pass
    m = _META_EPISODE_TOKEN_RE.search(name or "")
    if m:
        return f"S{int(m.group(1)):02d}E{int(m.group(2)):02d}"
    return None


def _meta_file_extension(name: str, meta_exts: set[str]) -> Optional[str]:
    if not name or "." not in name:
        return None
    suffix = name.rsplit(".", 1)[-1].lower()
    if suffix in meta_exts:
        return suffix
    stem, tail = name.rsplit(".", 1)
    if "." in stem:
        inner_ext = stem.rsplit(".", 1)[-1].lower()
        if f"{inner_ext}.{suffix}" in {f"{e}" for e in meta_exts}:
            return f"{inner_ext}.{suffix}"
        if tail.lower() in meta_exts:
            return tail.lower()
    return None


def match_meta_file_prefix(
    name: str,
    match_bases: List[str],
    meta_exts: set[str],
    *,
    episode_token: Optional[str] = None,
) -> Optional[str]:
    """判断元数据文件名是否跟随某媒体文件，返回匹配到的前缀。"""
    if not name:
        return None
    ext_key = _meta_file_extension(name, meta_exts)
    if not ext_key:
        return None

    ordered_bases = sorted({b for b in (match_bases or []) if b}, key=len, reverse=True)
    for base in ordered_bases:
        if name.startswith(base + ".") or name.startswith(base + "-"):
            return base

    if episode_token:
        token = episode_token.upper()
        upper_name = name.upper()
        if token in upper_name and f".{ext_key}" in name.lower():
            meta_stem = name[: -(len(ext_key) + 1)]
            if extract_episode_token(meta_stem) == token:
                return meta_stem
    return None


def file_extension(name: str) -> str:
    if not name or "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def build_display_title(tmdb_title: str, tmdb_original: str, fallback_title: str) -> str:
    """命名展示标题。

    双标题（"中文 - English"）的使用场景仅限：
    - TMDB 中文 title 与 original 不同
    - **且 original 是拉丁字符（英文/西文）**——非拉丁原标题（日/韩/泰/阿拉伯等）
      用户大概率不认识，附加只会污染文件名
    """
    if not tmdb_title:
        return fallback_title or ""
    if not tmdb_original or tmdb_original.lower() == tmdb_title.lower():
        return tmdb_title
    if _is_latin_script(tmdb_original):
        return f"{tmdb_title} - {tmdb_original}"
    return tmdb_title


def _is_latin_script(text: str) -> bool:
    """判断是否为拉丁字符（包含基本拉丁、扩展拉丁、常见符号）。"""
    if not text:
        return False
    has_letter = False
    for ch in text:
        if ch.isspace() or ch in ".,:;'\"-_!?()&+/":
            continue
        code = ord(ch)
        # 基本拉丁 + 拉丁扩展 + 数字
        if (
            (0x0030 <= code <= 0x0039)  # 0-9
            or (0x0041 <= code <= 0x005A)  # A-Z
            or (0x0061 <= code <= 0x007A)  # a-z
            or (0x00C0 <= code <= 0x024F)  # 拉丁扩展（带变音符）
            or (0x1E00 <= code <= 0x1EFF)  # 拉丁扩展增补
        ):
            has_letter = True
            continue
        # 一个非拉丁字符就否决
        return False
    return has_letter


def parse_extension_set(text: str) -> set:
    return {e.strip().lower() for e in (text or "").split(";") if e.strip()}


def strip_chinese_quality_tags(title: str) -> str:
    """从 title 中剥离常见的中/英文质量/字幕/编码/声道标签。

    典型场景：
    - "白日梦想家 蓝光原盘REMUX 内封简英字幕" → "白日梦想家"
    - "千钧一发 4K原盘REMUX 杜比视界 国英双音 内封特效字幕" → "千钧一发"
    - "Some Movie 2024 1080p H.265 DDP 5.1" → "Some Movie 2024"
    - "千与千寻 简繁中日内封" → "千与千寻"
    """
    raw = (title or "").strip()
    if not raw:
        return raw
    cleaned = _CN_QUALITY_TAG_RE.sub(" ", raw)
    # 短歧义标签：保留前置分隔符（防止 lookbehind 长度限制）
    cleaned = _CN_SHORT_TAG_RE.sub(r"\1", cleaned)
    cleaned = _EN_QUALITY_TAG_RE.sub(" ", cleaned)
    # 多余的空格 / 点号 / 破折号 / 加号 / 方括号 / 全角括号 收敛为单空格
    cleaned = re.sub(r"[\s._\-+\[\]【】（）()]+", " ", cleaned).strip(" ._-+")
    return cleaned or raw


def strip_release_group_from_title(title: str) -> str:
    raw = (title or "").strip()
    if not raw:
        return raw
    m = re.search(r"^(.*?)[\s._\-]+([A-Za-z0-9]{2,12})\s*$", raw)
    if m:
        candidate = m.group(2)
        if candidate.lower() in KNOWN_RELEASE_GROUPS_CI:
            return m.group(1).strip(" ._-") or raw
    m = re.search(r"^(.*?)\s*-\s*([A-Za-z0-9]{2,12})\s*$", raw)
    if m and m.group(2).lower() in KNOWN_RELEASE_GROUPS_CI:
        return m.group(1).strip(" ._-") or raw
    return raw


def is_anime(name: str) -> bool:
    raw = (name or "")
    if not raw:
        return False
    if re.search(r"[\s._\-\[]S\d{1,2}E\d{1,4}(?![\dA-Za-z])", raw, re.IGNORECASE):
        return False
    if CHINESE_SUB_TAG_RE.search(raw):
        return True
    bracket_count = sum(len(p.findall(raw)) for p in ANIME_BRACKET_PATTERNS)
    if bracket_count < 2 or not re.search(r"[\u4e00-\u9fa5]", raw):
        return False
    for pat in ANIME_BRACKET_PATTERNS:
        for m in pat.findall(raw):
            inner = m[1:-1].strip()
            if not inner:
                continue
            if re.fullmatch(r"\d{1,4}(v\d+)?", inner):
                return True
            if re.search(r"[\u4e00-\u9fa5]{2,}", inner):
                return True
    return False


_ANIME_QUALITY_RE = re.compile(
    r"(?:1080p|720p|2160p|480p|4K|HDR|x264|x265|HEVC|AVC|WEB[- ]?DL|WEBRip|BluRay|BDRip|BDMV|HDTV|AAC|FLAC|OPUS|GB|MB|REMUX|Atmos|TrueHD|DTS|杜比视界|杜比全景声|原盘)",
    re.IGNORECASE,
)

# 国内常见的"质量/字幕/编码/语言"中文标签（**长标签 / 含数字标签**，title 里出现就剥离）
_CN_QUALITY_TAG_RE = re.compile(
    r"(?:"
    r"蓝光原盘|4K原盘|2K原盘|UHD原盘|REMUX|杜比视界|杜比全景声|杜比音效|HDR\d*\+?|"
    r"内封(?:简[繁日英中]?|繁[简日英]?|日[英简繁]?|中[简繁日英]?|英[简繁日中]?|特效|双语|多语|官方|官)?字幕|"
    r"外挂(?:简[繁日英中]?|繁[简日英]?|双语)?字幕|特效字幕|内嵌字幕|压制字幕|"
    r"简繁[中日英]*内封|国语配音|国语原声|"
    r"国[日英粤台韩]双语?(?:音|配)?|国粤[日英]?双?语?|国英台?双?语?|"
    r"多音轨|多声道|无损音轨|高码率|"
    r"压制版|压制组|"
    r"中英字幕|官方字幕"
    r")"
)

# 高歧义短标签（2-3 字，可能跟 title 重合），**只在前后有分隔符时才剥离**
# 例如 "蓝光指南" 是 title 一部分，不能剥；但 "电影 蓝光" 里的 "蓝光" 是标签
_CN_SHORT_TAG_RE = re.compile(
    r"(^|[\s._\-+\[\(【（])"
    r"(?:蓝光|原盘|双语|中字|国配|台配|港配|官中|压制|高清|超清|无损|HQ)"
    r"(?=[\s._\-+\]\)】）]|$)"
)

# 英文质量标签，guessit 通常能切走，但带特殊字符（点号/加号/破折号）的会残留
_EN_QUALITY_TAG_RE = re.compile(
    r"(?:"
    # 分辨率 / 来源 / 编码
    r"2160[pP]|1080[pP]|720[pP]|480[pP]|4[Kk]|2[Kk]|8[Kk]|UHD|FHD|FullHD|"
    r"WEB[-. ]?DL|WEB[-. ]?Rip|BluRay|BDRip|BDMV|BD25|BD50|HDTV|HDTVrip|DVDRip|DVD[-. ]?9|DVD[-. ]?5|"
    r"REMUX|Repack|Proper|Extended|Director'?s[. ]Cut|Theatrical|Uncut|"
    # HDR/色彩
    r"HDR10\+?|HDR|Dolby[. ]Vision|DoVi|SDR|HLG|10[. ]?bit|8[. ]?bit|"
    # 视频编码
    r"H\.?264|H\.?265|HEVC|AVC|x264|x265|VP9|AV1|"
    # 音频编码
    r"DTS[-.]?HD[. ]?MA|DTS[-.]?HD|DTS[-.]?X|DTS|DDP|DD\+|DD|AC3|EAC3|TrueHD|"
    r"Atmos|FLAC|AAC|OPUS|MP3|PCM|"
    # 声道（5.1/7.1/2.0 等，可带前缀）
    r"\d\.\d|"
    # 帧率
    r"\d{2,3}fps|"
    # 字幕/字幕组关键字（英文）
    r"Subs?|MultiSubs?|MultiAudio|Multi[. ]?Lang"
    r")"
)


def parse_anime_filename(name: str) -> dict:
    raw = (name or "").strip()
    if not raw:
        return {}
    stem = raw.rsplit(".", 1)[0] if "." in raw else raw
    work = stem

    work = CHINESE_SUB_TAG_RE.sub(" ", work)

    episode: Optional[int] = None

    def _strip_bracket(match):
        nonlocal episode
        block = match.group(0)
        inner = block[1:-1].strip()
        if not inner:
            return " "
        # 1) 纯数字集号
        m_ep = re.fullmatch(r"(\d{1,4})(?:v\d+)?", inner)
        if m_ep:
            try:
                if episode is None:
                    episode = int(m_ep.group(1))
            except ValueError:
                pass
            return " "
        # 2) 质量/分辨率/编码标签
        if _ANIME_QUALITY_RE.search(inner):
            return " "
        # 3) 短英数标签（≤6 字符的纯字母数字组合，如 [4K] [TV] [BD] [WEB]）
        if re.fullmatch(r"[A-Za-z]+\d?", inner) and len(inner) <= 6:
            return " "
        # 4) 含 @ 的团队/发布组标识，如 [bb@HDSky] [Group@Site]
        if "@" in inner:
            return " "
        # 5) 文件大小标签，如 [46.36GB] [1.2TB] [500MB]
        if re.fullmatch(r"\d+(?:\.\d+)?\s*[KMGT]B", inner, re.IGNORECASE):
            return " "
        # 6) 字幕组/字幕版本特征词
        if re.search(r"(?:字幕|Subs?|RAW|Raws?|fansub|DIY简|DIY繁|DIY双|DIY特效|双语特效|多语)",
                     inner, re.IGNORECASE):
            return " "
        # 7) 内含 4 位年份的 bracket：年份保留为 year 候选，其余文字保留
        m_year = re.search(r"((?:19|20)\d{2})", inner)
        if m_year:
            # 不在这里直接抽 year（外层有统一逻辑），但要把整段保留以便外层再处理
            pass
        return " " + inner + " "

    for pat in ANIME_BRACKET_PATTERNS:
        work = pat.sub(_strip_bracket, work)

    work = re.sub(r"[★☆♥◆■◇]", " ", work)
    work = re.sub(r"\s+", " ", work).strip(" -_.")

    if episode is None:
        m = re.search(r"(?:^|\s|-)\s*(\d{1,3})(?:v\d+)?\s*$", work)
        if m:
            try:
                episode = int(m.group(1))
                work = work[: m.start()].strip(" -_.")
            except ValueError:
                pass

    if episode is None:
        m = ANIME_EPISODE_RE.search(stem)
        if m:
            try:
                episode = int(m.group(1))
            except ValueError:
                pass

    title = work
    year = None
    m = re.search(r"\s*[\(（]?\s*((?:19|20)\d{2})\s*[\)）]?\s*$", title)
    if m:
        try:
            year = int(m.group(1))
            title = title[: m.start()].strip(" -_.")
        except ValueError:
            pass

    out: Dict[str, Any] = {"type": "episode" if episode is not None else "movie"}
    if title:
        out["title"] = strip_chinese_quality_tags(title.strip())
    if year:
        out["year"] = year
    if episode is not None:
        out["episode"] = episode
        out["season"] = 1
    return out


def _is_chinese_text(s: str) -> bool:
    return bool(s and re.search(r"[\u4e00-\u9fa5]", s))


def merge_three_layer_parsed(file_parsed: dict, dir_parsed: dict, root_parsed: dict) -> dict:
    out = dict(file_parsed or {})
    sources = [dir_parsed or {}, root_parsed or {}]

    file_title = (out.get("title") or "").strip()
    chosen_title = file_title
    for src in sources:
        src_title = (src.get("title") or "").strip()
        if not src_title or is_generic_media_dir(src_title) or is_season_dir_name(src_title):
            continue
        if not chosen_title:
            chosen_title = src_title
            continue
        if _is_chinese_text(src_title) and not _is_chinese_text(chosen_title):
            chosen_title = src_title
            break
    if chosen_title:
        out["title"] = chosen_title

    if not out.get("year"):
        for src in sources:
            if src.get("year"):
                out["year"] = src["year"]
                break

    if out.get("type") == "episode":
        if out.get("season") is None:
            for src in sources:
                if src.get("season") is not None:
                    out["season"] = src["season"]
                    break

    if out.get("season") is None and any(src.get("season") is not None for src in sources):
        for src in sources:
            if src.get("season") is not None:
                out["season"] = src["season"]
                break

    return out


def extract_part_label(name: str) -> Optional[str]:
    if not name:
        return None
    m = PART_LABEL_RE.search(name)
    if m:
        kind = m.group(1).upper()
        num = m.group(2)
        if re.fullmatch(r"[ABab]", num or ""):
            return f"{kind}{num.upper()}"
        try:
            num_i = int(num)
            return f"{kind}{num_i}"
        except ValueError:
            return f"{kind}{num}"
    m = VOL_LABEL_RE.search(name)
    if m:
        try:
            return f"vol{int(m.group(1))}"
        except ValueError:
            return None
    m = CN_PART_LABEL_RE.search(name)
    if m:
        return m.group(1)
    return None


def extract_special_label(name: str) -> Optional[str]:
    """识别 OVA/OAD/SP/番外/特别篇/剧场版 等特殊单集。返回标签或 None。"""
    if not name:
        return None
    m = SPECIAL_EPISODE_RE.search(name)
    if not m:
        return None
    kind = m.group(1).upper() if m.group(1).isascii() else m.group(1)
    num = m.group(2)
    if num:
        try:
            return f"{kind}{int(num):02d}"
        except ValueError:
            return f"{kind}{num}"
    return kind


