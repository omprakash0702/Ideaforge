import enum


class ProjectStatus(str, enum.Enum):
    CREATED = "CREATED"
    GENERATING = "GENERATING"
    REVIEWING = "REVIEWING"
    JUDGING = "JUDGING"
    EVOLVING = "EVOLVING"
    TOURNAMENT = "TOURNAMENT"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JudgeType(str, enum.Enum):
    INVESTOR = "INVESTOR"
    ENGINEER = "ENGINEER"
    SKEPTIC = "SKEPTIC"


class GeneratorType(str, enum.Enum):
    CREATIVE = "CREATIVE"
    MARKET = "MARKET"
    BUILDER = "BUILDER"
    ANALYST = "ANALYST"
