from mock_data.crops import CROP_PROFILES
from mock_data.environment import climate_for, soil_for
from schemas.farm import AnalysisResponse, FarmInput, RotationResponse

DISCLAIMER = (
    "Architecture demonstration using illustrative rules and mock data. "
    "Scores are not scientifically validated forecasts or farming advice."
)
DEPLETING_FAMILIES = {"cereal"}


def _family_of(crop_name: str) -> str:
    key = crop_name.strip().lower()
    profile = CROP_PROFILES.get(key)
    if profile is None:
        profile = next(
            (item for item in CROP_PROFILES.values() if item["name"].lower() == key),
            None,
        )
    return profile["family"].lower() if profile else ""


def _rotation_fatigue(previous_crop: str, suggested_crops: list[dict]) -> dict:
    families = [_family_of(previous_crop)]
    families.extend(_family_of(item["crop"]) for item in suggested_crops)
    repeats_family = any(
        current and current == previous for previous, current in zip(families, families[1:])
    )
    depletes_nutrients = sum(family in DEPLETING_FAMILIES for family in families) >= 2
    restores_nutrients = any(family == "legume" for family in families[1:])

    if repeats_family and depletes_nutrients and not restores_nutrients:
        level = "high"
        note = "Suggested rotation repeats a crop family and keeps depleting soil nutrients."
    elif repeats_family:
        level = "medium"
        note = "Suggested rotation repeats the same crop family as the crop before it."
    elif depletes_nutrients and not restores_nutrients:
        level = "medium"
        note = "Suggested rotation is mostly nutrient-depleting crops and includes no legume."
    else:
        level = "low"
        note = "Suggested rotation changes crop family and does not keep depleting soil nutrients."

    return {"type": "Rotation fatigue", "level": level, "note": note}


def _crop_scores(
    farm: FarmInput,
    soil: dict,
    climate: dict,
    priority: str | None = None,
    limit: int | None = 3,
) -> list[dict]:
    water_per_dunam = farm.available_water_m3 / farm.area_dunams
    previous = farm.previous_crop.strip().lower()
    active_priority = priority or farm.priority
    scores = []

    for key, crop in CROP_PROFILES.items():
        score = 72
        reasons = []

        if water_per_dunam >= crop["water_need_m3_per_dunam"]:
            score += 14
            reasons.append("demo water allocation meets the sample threshold")
        else:
            score -= min(28, int((crop["water_need_m3_per_dunam"] - water_per_dunam) * 1.2))
            reasons.append("sample water need may exceed the entered allocation")

        low_ph, high_ph = crop["preferred_ph"]
        if low_ph <= soil["ph"] <= high_ph:
            score += 8
            reasons.append("mock soil pH is within the preferred range")
        else:
            score -= 10
            reasons.append("mock soil pH is outside the preferred range")

        low_temp, high_temp = crop["preferred_temperature_c"]
        temperature = climate["average_temperature_c"]
        if low_temp <= temperature <= high_temp:
            score += 8
            reasons.append("scenario temperature suits this crop")
        else:
            distance = low_temp - temperature if temperature < low_temp else temperature - high_temp
            score -= min(20, round(distance * 2))
            reasons.append("scenario temperature is outside the sample comfort range")

        if climate["annual_rainfall_mm"] < 250:
            score -= 8
            reasons.append("low scenario rainfall adds pressure")

        if soil["organic_matter_percent"] >= 2:
            score += 4

        previous_crop = CROP_PROFILES.get(previous)
        previous_family = previous_crop["family"].lower() if previous_crop else ""
        family = crop["family"].lower()

        if key == previous:
            score -= 25
            reasons.append("penalized to avoid repeating the previous crop")
        elif previous_family and family == previous_family:
            score -= 18
            reasons.append("penalized because it repeats the previous crop family")
        elif family == "legume" and previous_family == "cereal":
            score += 6
            reasons.append("a legume follows the previous cereal")

        water_need = crop["water_need_m3_per_dunam"]
        if active_priority == "water_saving":
            if water_need <= 40:
                score += 10
                reasons.append("favored for the water-saving priority")
            elif water_need >= 55:
                score -= 10
                reasons.append("penalized for the water-saving priority")
        elif active_priority == "soil_health":
            if family == "legume":
                score += 10
                reasons.append("favored for the soil-health priority")
            elif family in DEPLETING_FAMILIES:
                score -= 8
                reasons.append("penalized for the soil-health priority")
        elif active_priority == "high_yield" and water_need >= 55:
            score += 12
            reasons.append("favored for the high-yield priority")

        scores.append(
            {
                "crop": crop["name"],
                "score": max(0, min(100, score)),
                "reason": "; ".join(reasons).capitalize() + ".",
                "water_need_m3_per_dunam": crop["water_need_m3_per_dunam"],
            }
        )

    ranked = sorted(scores, key=lambda item: item["score"], reverse=True)
    return ranked if limit is None else ranked[:limit]


def analyze_farm(farm: FarmInput) -> AnalysisResponse:
    climate = climate_for(farm.latitude)
    soil = soil_for(farm.longitude)
    if farm.mock_temperature_c is not None:
        climate["average_temperature_c"] = farm.mock_temperature_c
        climate["source"] = "User-adjusted demo climate scenario"
    if farm.mock_rainfall_mm is not None:
        climate["annual_rainfall_mm"] = farm.mock_rainfall_mm
        climate["source"] = "User-adjusted demo climate scenario"
    if farm.mock_soil_ph is not None:
        soil["ph"] = farm.mock_soil_ph
        soil["source"] = "User-adjusted demo soil scenario"
    if farm.mock_organic_matter_percent is not None:
        soil["organic_matter_percent"] = farm.mock_organic_matter_percent
        soil["source"] = "User-adjusted demo soil scenario"

    water_per_dunam = farm.available_water_m3 / farm.area_dunams
    crops = _crop_scores(farm, soil, climate)

    rainfall = climate["annual_rainfall_mm"]
    if water_per_dunam < 32 and rainfall < 300:
        water_level = "high"
    elif water_per_dunam < 45 or rainfall < 400:
        water_level = "medium"
    else:
        water_level = "low"
    temperature = climate["average_temperature_c"]
    heat_level = "high" if temperature > 30 else "medium" if temperature > 24 else "low"

    return AnalysisResponse(
        data_label="Demo / Mock Data",
        disclaimer=DISCLAIMER,
        request_summary=farm,
        climate=climate,
        soil=soil,
        suggested_crops=crops,
        risks=[
            {
                "type": "Water pressure",
                "level": water_level,
                "note": f"Based on {water_per_dunam:.1f} m³ per dunam and {rainfall} mm scenario rainfall.",
            },
            {
                "type": "Heat exposure",
                "level": heat_level,
                "note": f"Based on the {temperature:.1f}°C adjustable scenario temperature.",
            },
            _rotation_fatigue(farm.previous_crop, crops),
        ],
    )


def _plan_metrics(picks: list[dict], water_per_dunam: float) -> dict:
    total_water = sum(item["water_need_m3_per_dunam"] for item in picks)
    average_water = round(total_water / len(picks))
    families = [_family_of(item["crop"]) for item in picks]
    cereal_count = sum(family == "cereal" for family in families)
    has_legume = "legume" in families
    if has_legume and cereal_count == 0:
        nutrient_effect = "restoring"
    elif cereal_count >= 2 and not has_legume:
        nutrient_effect = "depleting"
    else:
        nutrient_effect = "balanced"
    return {
        "average_water_m3_per_dunam": average_water,
        "total_water_m3_per_dunam": total_water,
        "average_suitability": round(sum(item["score"] for item in picks) / len(picks)),
        "nutrient_effect": nutrient_effect,
        "fits_water_allocation": average_water <= water_per_dunam,
    }


def _take_crops(ranked: list[dict], count: int = 3, blocked: set[str] | None = None) -> list[dict]:
    skipped = blocked or set()
    chosen = []
    for item in ranked:
        if item["crop"] in skipped or item["crop"] in {pick["crop"] for pick in chosen}:
            continue
        chosen.append(item)
        if len(chosen) == count:
            return chosen
    for item in ranked:
        if item["crop"] in {pick["crop"] for pick in chosen}:
            continue
        chosen.append(item)
        if len(chosen) == count:
            break
    return chosen


def _season_rows(picks: list[dict], explanations: list[str]) -> list[dict]:
    periods = ["Winter 2026", "Summer 2027", "Winter 2027"]
    return [
        {
            "season": index + 1,
            "period": periods[index],
            "crop": pick["crop"],
            "explanation": explanations[index],
        }
        for index, pick in enumerate(picks)
    ]


def suggest_rotation(farm: FarmInput) -> RotationResponse:
    climate = climate_for(farm.latitude)
    soil = soil_for(farm.longitude)
    if farm.mock_temperature_c is not None:
        climate["average_temperature_c"] = farm.mock_temperature_c
    if farm.mock_rainfall_mm is not None:
        climate["annual_rainfall_mm"] = farm.mock_rainfall_mm
    if farm.mock_soil_ph is not None:
        soil["ph"] = farm.mock_soil_ph
    if farm.mock_organic_matter_percent is not None:
        soil["organic_matter_percent"] = farm.mock_organic_matter_percent

    water_per_dunam = farm.available_water_m3 / farm.area_dunams
    water_ranked = sorted(
        _crop_scores(farm, soil, climate, priority="water_saving", limit=None),
        key=lambda item: (item["water_need_m3_per_dunam"], -item["score"]),
    )
    soil_ranked = _crop_scores(farm, soil, climate, priority="soil_health", limit=None)
    water_picks = _take_crops(water_ranked)
    soil_picks = _take_crops(soil_ranked)
    if [item["crop"] for item in water_picks] == [item["crop"] for item in soil_picks]:
        soil_picks = _take_crops(soil_ranked, blocked={water_picks[-1]["crop"]})

    water_plan = {
        "plan_name": "Plan A: Water-saving",
        "seasons": _season_rows(
            water_picks,
            [
                f"Lowest-water fit after the previous {farm.previous_crop} crop.",
                "Next lowest-water crop for the following season.",
                "Third low-water crop completes the water-saving sequence.",
            ],
        ),
        "metrics": _plan_metrics(water_picks, water_per_dunam),
    }
    soil_plan = {
        "plan_name": "Plan B: Soil-restoring",
        "seasons": _season_rows(
            soil_picks,
            [
                "Chosen to restore soil after the previous crop, preferring a legume when it fits.",
                "A different family keeps the rotation from drawing down the same nutrients.",
                "Remaining balanced option for the last season.",
            ],
        ),
        "metrics": _plan_metrics(soil_picks, water_per_dunam),
    }
    water_gap = abs(
        water_plan["metrics"]["average_water_m3_per_dunam"]
        - soil_plan["metrics"]["average_water_m3_per_dunam"]
    )
    lower_water_plan = (
        water_plan["plan_name"]
        if water_plan["metrics"]["average_water_m3_per_dunam"]
        <= soil_plan["metrics"]["average_water_m3_per_dunam"]
        else soil_plan["plan_name"]
    )

    return RotationResponse(
        data_label="Demo / Mock Data",
        disclaimer=DISCLAIMER,
        plan_name=water_plan["plan_name"],
        seasons=water_plan["seasons"],
        plans=[water_plan, soil_plan],
        comparison={
            "lower_water_plan": lower_water_plan,
            "water_difference_m3_per_dunam": water_gap,
            "summary": (
                f"{lower_water_plan} uses {water_gap} m³/dunam less water on average. "
                f"Plan B nutrient effect is {soil_plan['metrics']['nutrient_effect']}."
            ),
        },
    )

