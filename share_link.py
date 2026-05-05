"""Encode a BeanData object into a Beanconqueror share URL.

Mirrors the official /create/ JS encoder byte-for-byte: every field is
written explicitly (incl. empty strings, zero ints, empty sub-messages
with all their zero-valued fields), because the Beanconqueror import
handler silently rejects payloads that omit them.
"""

import base64
import logging
from datetime import datetime
from urllib.parse import urlencode

import beanconqueror_pb2 as bc
from models import BeanData

logger = logging.getLogger(__name__)

SHARE_BASE_URL = "https://beanconqueror.com/"
CHUNK_SIZE = 400


def build_share_link(bean: BeanData) -> str:
    proto = _to_proto(bean)
    payload = base64.b64encode(proto.SerializeToString()).decode("ascii")
    params = [
        (f"shareUserBean{i}", payload[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE])
        for i in range((len(payload) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    ]
    url = SHARE_BASE_URL + "?" + urlencode(params)
    logger.info("Built share URL for '%s' (%d bytes proto, %d chunks)",
                bean.coffee_name, len(payload), len(params))
    return url


def _to_proto(bean: BeanData) -> bc.BeanProto:
    p = bc.BeanProto()

    # Top-level scalars — set ALL of them, including empty strings/zeros,
    # so the wire format matches the JS encoder exactly.
    p.name = bean.coffee_name
    p.roastingDate = _to_iso(bean.roasting_date) if bean.roasting_date else ""
    p.note = bean.notes or ""
    p.roaster = bean.roaster or ""
    p.roast = bc.Roast.Value(bean.roast.value) if bean.roast else bc.UNKNOWN_ROAST
    p.roast_range = int(bean.degree_of_roast) if bean.degree_of_roast is not None else 0
    p.beanMix = bc.BeanMix.Value(bean.bean_mix.value) if bean.bean_mix else bc.UNKNOWN_BEAN_MIX
    p.roast_custom = bean.roast_custom or ""
    p.aromatics = bean.flavour_profile or ""
    p.weight = bean.weight or 0
    p.finished = False
    p.cost = int(round(bean.cost)) if bean.cost is not None else 0
    p.cupping_points = bean.cupping_points or ""
    p.decaffeinated = bool(bean.decaffeinated)
    p.url = bean.website or ""
    p.ean_article_number = bean.ean_article or ""
    p.rating = 0
    p.bean_roasting_type = (
        bc.BeanRoastingType.Value(bean.bean_roasting_type.value)
        if bean.bean_roasting_type
        else bc.UNKNOWN_BEAN_ROASTING_TYPE
    )
    p.qr_code = ""
    p.favourite = False
    p.shared = False

    # Empty sub-message: set in parent so it's serialized as an empty msg.
    p.config.SetInParent()
    p.cupped_flavor.SetInParent()

    # Sub-messages with all-zero numeric fields (matches JS literal).
    bri = p.bean_roast_information
    bri.drop_temperature = 0
    bri.roast_length = 0
    bri.roaster_machine = ""
    bri.green_bean_weight = 0
    bri.outside_temperature = 0
    bri.humidity = 0
    bri.bean_uuid = ""
    bri.first_crack_minute = 0
    bri.first_crack_temperature = 0
    bri.second_crack_minute = 0
    bri.second_crack_temperature = 0

    cup = p.cupping
    cup.dry_fragrance = 0
    cup.wet_aroma = 0
    cup.brightness = 0
    cup.flavor = 0
    cup.body = 0
    cup.finish = 0
    cup.sweetness = 0
    cup.clean_cup = 0
    cup.complexity = 0
    cup.uniformity = 0
    cup.cuppers_correction = 0

    # Varieties — JS always includes at least one (empty if no input).
    varieties = bean.varieties or [None]
    for v in varieties:
        info = p.bean_information.add()
        if v is None:
            continue
        info.country = v.country or ""
        info.region = v.region or ""
        info.farm = v.farm or ""
        info.farmer = v.farmer or ""
        info.elevation = v.elevation or ""
        info.harvest_time = v.harvest_time or ""
        info.variety = v.variety or ""
        info.processing = v.processing or ""
        info.certification = v.certification or ""
        info.percentage = v.percentage if v.percentage is not None else 0

    return p


def _to_iso(date_str: str) -> str:
    """Accept either 'YYYY-MM-DD' or full ISO; emit JS-style ISO with Z."""
    try:
        if "T" in date_str:
            return date_str
        return datetime.fromisoformat(date_str).isoformat() + ".000Z"
    except ValueError:
        return date_str
