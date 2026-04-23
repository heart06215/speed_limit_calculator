"""固定数据集 - 路面附着系数、护栏等级、车型数据"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

GRAVITY = 9.80665
GRAVITY_APPROX = 9.81
KM_H_TO_M_S = 1.0 / 3.6
@dataclass
class RoadSurfaceCondition:
    key: str
    name: str
    adhesion: float
    description: str


ROAD_CONDITIONS: Dict[str, RoadSurfaceCondition] = {
    "dry_asphalt": RoadSurfaceCondition(
        key="dry_asphalt",
        name="干燥沥青路面",
        adhesion=0.7,
        description="干燥天气，普通沥青路面"
    ),
    "wet_asphalt": RoadSurfaceCondition(
        key="wet_asphalt",
        name="潮湿沥青路面",
        adhesion=0.4,
        description="雨天或路面潮湿的沥青路面"
    ),
    "dry_concrete": RoadSurfaceCondition(
        key="dry_concrete",
        name="干燥水泥路面",
        adhesion=0.75,
        description="干燥天气，水泥混凝土路面"
    ),
    "wet_concrete": RoadSurfaceCondition(
        key="wet_concrete",
        name="潮湿水泥路面",
        adhesion=0.45,
        description="雨天或路面潮湿的水泥路面"
    ),
    "snow": RoadSurfaceCondition(
        key="snow",
        name="积雪路面",
        adhesion=0.2,
        description="冰雪覆盖路面"
    ),
    "ice": RoadSurfaceCondition(
        key="ice",
        name="结冰路面",
        adhesion=0.1,
        description="路面结冰，极低摩擦"
    ),
    "gravel": RoadSurfaceCondition(
        key="gravel",
        name="砂石路面",
        adhesion=0.35,
        description="碎石或砂土路面"
    ),
    "dry_new_tire": RoadSurfaceCondition(
        key="dry_new_tire",
        name="干燥路面(新轮胎)",
        adhesion=0.85,
        description="干燥路面+新轮胎最佳附着情况"
    ),
}

ROAD_CONDITION_LIST: List[dict] = [
    {"key": rc.key, "name": rc.name, "adhesion": rc.adhesion, "description": rc.description}
    for rc in ROAD_CONDITIONS.values()
]


@dataclass
class BarrierLevel:
    level_code: str
    name: str
    design_energy: float
    description: str

    @property
    def collision_angle(self) -> float:
        return 20.0


BARRIER_LEVELS: Dict[str, BarrierLevel] = {
    "B":  BarrierLevel("B",  "B级 - 最低防护",  70,  "路侧最低防护等级"),
    "A":  BarrierLevel("A",  "A级 - 一般防护",  160, "一般路段常用等级"),
    "SB": BarrierLevel("SB", "SB级 - 较高防护", 280, "危险路段使用"),
    "SA": BarrierLevel("SA", "SA级 - 高防护",   400, "高危险路段"),
    "SS": BarrierLevel("SS", "SS级 - 最高公路防护", 520, "极高危险路段"),
    "HB": BarrierLevel("HB", "HB级 - 超高防护(城市道路)", 640, "特殊超高防护"),
}

BARRIER_LEVEL_LIST: List[dict] = [
    {"code": bl.level_code, "name": bl.name, "energy": bl.design_energy, "description": bl.description}
    for bl in BARRIER_LEVELS.values()
]


@dataclass
class BarrierCollisionSpec:
    level: str
    vehicle_type: str
    vehicle_mass: float
    collision_speed: float
    collision_angle: float
    design_energy: float
    source: str
    notes: str


BARRIER_COLLISION_SPECS: List[BarrierCollisionSpec] = [
    # B级 - 最低防护等级
    BarrierCollisionSpec("B", "小客车", 1.5,  60, 20, 70,  "GB 50688-2011 表7.2.1", "路侧最低防护等级"),
    BarrierCollisionSpec("B", "大客车", 10.0, 40, 20, 70,  "GB 50688-2011 表7.2.1", "路侧最低防护等级"),
    # A级 - 一般防护
    BarrierCollisionSpec("A", "小客车", 1.5, 100, 20, 160, "GB 50688-2011 表7.2.1", "一般路段常用等级"),
    BarrierCollisionSpec("A", "大客车", 10.0, 60, 20, 160, "GB 50688-2011 表7.2.1", "一般路段常用等级"),
    # SB级 - 较高防护
    BarrierCollisionSpec("SB", "小客车", 1.5, 100, 20, 280, "GB 50688-2011 表7.2.1", "危险路段使用"),
    BarrierCollisionSpec("SB", "大客车", 10.0, 80, 20, 280, "GB 50688-2011 表7.2.1", "危险路段使用"),
    # SA级 - 高防护
    BarrierCollisionSpec("SA", "小客车", 1.5, 100, 20, 400, "GB 50688-2011 表7.2.1", "高危险路段"),
    BarrierCollisionSpec("SA", "大客车", 14.0, 80, 20, 400, "GB 50688-2011 表7.2.1", "高危险路段"),
    # SS级 - 最高公路防护
    BarrierCollisionSpec("SS", "小客车", 1.5, 100, 20, 520, "GB 50688-2011 表7.2.1", "极高危险路段"),
    BarrierCollisionSpec("SS", "大客车", 18.0, 80, 20, 520, "GB 50688-2011 表7.2.1", "极高危险路段"),
    # HB级 - 超高防护（城市道路新增）
    BarrierCollisionSpec("HB", "小客车", 1.5, 100, 20, 640, "GB 50688-2011 表7.2.1", "特殊超高防护"),
    BarrierCollisionSpec("HB", "大客车", 25.0, 80, 20, 640, "GB 50688-2011 表7.2.1", "特殊超高防护"),
]


@dataclass
class BarrierFailureThreshold:
    level: str
    design_energy: float
    max_safe_speed_small_car: float
    max_safe_speed_bus: float
    max_safe_speed_truck: float
    description: str


BARRIER_FAILURE_THRESHOLDS: List[BarrierFailureThreshold] = [
    BarrierFailureThreshold(
        level="B", design_energy=70,
        max_safe_speed_small_car=60, max_safe_speed_bus=40, max_safe_speed_truck=0,
        description="最低防护等级。小客车超过60km/h撞击、大客车超过40km/h撞击时护栏可能失效"
    ),
    BarrierFailureThreshold(
        level="A", design_energy=160,
        max_safe_speed_small_car=100, max_safe_speed_bus=60, max_safe_speed_truck=0,
        description="一般防护等级。小客车超过100km/h撞击时护栏可能失效"
    ),
    BarrierFailureThreshold(
        level="SB", design_energy=280,
        max_safe_speed_small_car=100, max_safe_speed_bus=80, max_safe_speed_truck=0,
        description="较高防护等级。大客车超过80km/h撞击时护栏可能失效"
    ),
    BarrierFailureThreshold(
        level="SA", design_energy=400,
        max_safe_speed_small_car=100, max_safe_speed_bus=80, max_safe_speed_truck=80,
        description="高防护等级。14t大客车超过80km/h撞击时护栏可能失效"
    ),
    BarrierFailureThreshold(
        level="SS", design_energy=520,
        max_safe_speed_small_car=100, max_safe_speed_bus=80, max_safe_speed_truck=80,
        description="最高公路防护等级。18t大货车超过80km/h撞击时护栏可能失效"
    ),
    BarrierFailureThreshold(
        level="HB", design_energy=640,
        max_safe_speed_small_car=100, max_safe_speed_bus=80, max_safe_speed_truck=80,
        description="超高防护等级（城市道路）。25t大货车超过80km/h撞击时护栏可能失效"
    ),
]

BARRIER_THRESHOLDS_BY_LEVEL: Dict[str, BarrierFailureThreshold] = {
    t.level: t for t in BARRIER_FAILURE_THRESHOLDS
}


HIGHWAY_BARRIER_CONDITIONS: List[dict] = [
    {"level": "B",       "car_mass": 1.5, "car_speed": 100, "bus_mass": 10,  "bus_speed": 40, "energy": 70},
    {"level": "A/Am",    "car_mass": 1.5, "car_speed": 100, "bus_mass": 10,  "bus_speed": 60, "energy": 160},
    {"level": "SB/SBm",  "car_mass": 1.5, "car_speed": 100, "bus_mass": 10,  "bus_speed": 80, "energy": 280},
    {"level": "SA/SAm",  "car_mass": 1.5, "car_speed": 100, "bus_mass": 14,  "bus_speed": 80, "energy": 400},
    {"level": "SS",      "car_mass": 1.5, "car_speed": 100, "bus_mass": 18,  "bus_speed": 80, "energy": 520},
]


@dataclass
class VehiclePreset:
    key: str
    name: str
    mass: float
    description: str


VEHICLE_PRESETS: Dict[str, VehiclePreset] = {
    "small_car":    VehiclePreset("small_car",    "小客车",   1.5,  "普通小轿车，约1.5吨"),
    "sedan":        VehiclePreset("sedan",        "中型轿车", 1.8,  "中型轿车，约1.8吨"),
    "suv":          VehiclePreset("suv",          "SUV",      2.2,  "运动型多用途车，约2.2吨"),
    "minibus":      VehiclePreset("minibus",      "小型客车", 3.5,  "小型客车/面包车，约3.5吨"),
    "bus":          VehiclePreset("bus",          "大型客车", 10.0, "大型客车，约10吨"),
    "heavy_bus":    VehiclePreset("heavy_bus",    "重型客车", 14.0, "重型客车，约14吨"),
    "truck_medium": VehiclePreset("truck_medium", "中型货车", 10.0, "中型货车，约10吨"),
    "truck_heavy":  VehiclePreset("truck_heavy",  "重型货车", 18.0, "重型货车，约18吨"),
}

VEHICLE_PRESET_LIST: List[dict] = [
    {"key": vp.key, "name": vp.name, "mass": vp.mass, "description": vp.description}
    for vp in VEHICLE_PRESETS.values()
]


def get_road_condition(key: str) -> RoadSurfaceCondition:
    if key not in ROAD_CONDITIONS:
        available = ", ".join(ROAD_CONDITIONS.keys())
        raise ValueError(f"未知路面条件: {key}\n可用: {available}")
    return ROAD_CONDITIONS[key]


def get_barrier_level(code: str) -> BarrierLevel:
    if code not in BARRIER_LEVELS:
        available = ", ".join(BARRIER_LEVELS.keys())
        raise ValueError(f"未知护栏等级: {code}\n可用: {available}")
    return BARRIER_LEVELS[code]


def get_barrier_threshold(level_code: str) -> BarrierFailureThreshold:
    return BARRIER_THRESHOLDS_BY_LEVEL.get(level_code.upper())


def get_vehicle_preset(key: str) -> VehiclePreset:
    if key not in VEHICLE_PRESETS:
        available = ", ".join(VEHICLE_PRESETS.keys())
        raise ValueError(f"未知车型: {key}\n可用: {available}")
    return VEHICLE_PRESETS[key]


def get_all_data_summary() -> dict:
    return {
        "road_conditions": ROAD_CONDITION_LIST,
        "barrier_levels": BARRIER_LEVEL_LIST,
        "vehicle_presets": VEHICLE_PRESET_LIST,
        "barrier_specs": [
            {
                "level": s.level,
                "vehicle_type": s.vehicle_type,
                "vehicle_mass": s.vehicle_mass,
                "collision_speed": s.collision_speed,
                "collision_angle": s.collision_angle,
                "design_energy": s.design_energy,
                "source": s.source,
                "notes": s.notes,
            }
            for s in BARRIER_COLLISION_SPECS
        ],
        "barrier_thresholds": [
            {
                "level": t.level,
                "design_energy": t.design_energy,
                "max_safe_speed_small_car": t.max_safe_speed_small_car,
                "max_safe_speed_bus": t.max_safe_speed_bus,
                "max_safe_speed_truck": t.max_safe_speed_truck,
                "description": t.description,
            }
            for t in BARRIER_FAILURE_THRESHOLDS
        ],
    }
