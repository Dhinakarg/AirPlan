"""Domain enumerations for demographic, environmental, and behavioral attributes."""

from enum import StrEnum


class AgeGroup(StrEnum):
    """Demographic age categories determining physiological breathing rates."""

    TODDLER = "toddler"
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    SENIOR = "senior"


class Sensitivity(StrEnum):
    """Health susceptibility and vulnerability classifications."""

    NONE = "none"
    ASTHMA_OR_HEART = "asthma_or_heart"
    PREGNANT = "pregnant"


class Activity(StrEnum):
    """Physical activity categories determining minute ventilation rates."""

    SLEEP = "sleep"
    REST = "rest"
    LIGHT = "light"
    WALK = "walk"
    EXERCISE = "exercise"
    COOK = "cook"


class Mode(StrEnum):
    """Micro-environment and commute transit modes."""

    HOME = "home"
    WALK = "walk"
    CYCLE = "cycle"
    METRO = "metro"
    BUS = "bus"
    AUTO_RICKSHAW = "auto_rickshaw"
    CAR = "car"
    OUTDOOR = "outdoor"


class Leakiness(StrEnum):
    """Building envelope tightness classification."""

    TIGHT = "tight"
    AVERAGE = "average"
    LEAKY = "leaky"


class CookingFuel(StrEnum):
    """Primary household cooking fuel classification."""

    LPG = "lpg"
    WOOD = "wood"
    BIOMASS = "biomass"
    INDUCTION = "induction"
    ELECTRIC_COIL = "electric_coil"


class KitchenExhaust(StrEnum):
    """Kitchen ventilation and exhaust configuration."""

    NONE = "none"
    INTERNAL = "internal"
    VENTED = "vented"


class SweepingType(StrEnum):
    """Floor dust cleaning modality."""

    DRY = "dry"
    WET = "wet"


class InterventionCategory(StrEnum):
    """Domain grouping for household and individual air quality interventions."""

    TIMING = "timing"
    HOME = "home"
    TRANSPORT = "transport"
    COMMUNITY = "community"
