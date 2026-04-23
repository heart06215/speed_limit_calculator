"""车辆撞击护栏模拟计算器"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from calculate.sample import (
    ROAD_CONDITIONS, ROAD_CONDITION_LIST,
    BARRIER_LEVELS, BARRIER_THRESHOLDS_BY_LEVEL, BARRIER_FAILURE_THRESHOLDS,
    BARRIER_COLLISION_SPECS,
    VEHICLE_PRESETS,
    GRAVITY, KM_H_TO_M_S,
    get_road_condition, get_barrier_level, get_barrier_threshold,
)

@dataclass
class SimulationInput:
    vehicle_mass: float
    initial_speed: float
    brake_reaction_time: float
    road_length: float
    slope_grade: float
    barrier_level: str
    brake_start_distance: float = 0.0
    brake_failure: bool = False

@dataclass
class TimeFrame:
    time: float
    speed_kmh: float
    speed_ms: float
    position: float
    deceleration: float
    is_braking: bool
    is_stopped: bool
    is_collision: bool

@dataclass
class RoadConditionResult:
    road_key: str
    road_name: str
    adhesion: float
    reaction_distance: float
    braking_distance: float
    total_stopping_distance: float
    time_to_stop: float
    hits_barrier: bool
    collision_speed_kmh: float
    collision_speed_ms: float
    collision_energy_kj: float
    barrier_can_hold: bool
    barrier_design_energy: float
    safety_margin: float
    frames: List[TimeFrame] = field(default_factory=list)


@dataclass
class SimulationResult:
    input_params: dict
    total_real_time: float
    results_by_road: Dict[str, RoadConditionResult]
    summary: dict


class CollisionSimulator:

    DT = 0.05
    MIN_SPEED = 0.1
    COLLISION_ANGLE = 20.0

    def __init__(self):
        pass

    def _calc_deceleration(self, adhesion: float, slope_percent: float) -> float:
        theta = math.atan(slope_percent / 100.0)
        decel = adhesion * GRAVITY * math.cos(theta) - GRAVITY * math.sin(theta)
        return decel

    def _simulate_single_road(
        self, params: SimulationInput, road_key: str
    ) -> RoadConditionResult:

        road = get_road_condition(road_key)
        barrier = get_barrier_level(params.barrier_level)
        threshold = get_barrier_threshold(params.barrier_level)

        # 转换单位
        v0_ms = params.initial_speed * KM_H_TO_M_S
        slope_rad = math.atan(params.slope_grade / 100.0)
        decel = self._calc_deceleration(road.adhesion, params.slope_grade)

        # 反应距离（匀速段）
        reaction_distance = v0_ms * params.brake_reaction_time

        # 刹车失灵处理：制动减速度为0（完全滑行）
        effective_decel = 0.0 if params.brake_failure else decel

        # 制动距离（匀减速到0）
        if effective_decel > 0:
            braking_distance = (v0_ms ** 2) / (2 * effective_decel)
            time_braking = v0_ms / effective_decel
        else:
            braking_distance = float('inf')
            time_braking = float('inf')

        total_stopping_distance = reaction_distance + braking_distance
        time_to_stop = params.brake_reaction_time + time_braking

        # 判定是否撞击
        distance_to_barrier = params.road_length - params.brake_start_distance
        hits_barrier = total_stopping_distance > distance_to_barrier

        if hits_barrier:
            # 计算撞击时的速度
            # 制动后可用的减速距离 = distance_to_barrier - reaction_distance
            braking_distance_before_barrier = distance_to_barrier - reaction_distance
            if braking_distance_before_barrier < 0:
                # 还在反应时间内就撞了
                collision_speed_ms = v0_ms
                braking_distance_before_barrier = 0
            elif effective_decel > 0:
                # v² = v0² - 2×a×d
                v_sq = v0_ms ** 2 - 2 * effective_decel * braking_distance_before_barrier
                collision_speed_ms = math.sqrt(max(0, v_sq))
            else:
                collision_speed_ms = v0_ms

            collision_speed_kmh = collision_speed_ms / KM_H_TO_M_S

            # 碰撞能量（20°碰撞角修正）
            mass_kg = params.vehicle_mass * 1000
            # E = ½mv² / sin(20°)，除以1000转kJ
            collision_energy = (
                0.5 * mass_kg * collision_speed_ms ** 2
                / math.sin(math.radians(self.COLLISION_ANGLE))
                / 1000
            )

            # 护栏判定
            barrier_can_hold = collision_energy <= barrier.design_energy
            if threshold:
                safety_margin = (
                    (barrier.design_energy - collision_energy) / collision_energy * 100
                    if collision_energy > 0 else float('inf')
                )
            else:
                safety_margin = 0

            barrier_design_energy = barrier.design_energy
        else:
            collision_speed_ms = 0
            collision_speed_kmh = 0
            collision_energy = 0
            barrier_can_hold = True
            safety_margin = float('inf')
            barrier_design_energy = barrier.design_energy

        # 生成时间序列帧（用于前端动画）
        frames = self._generate_frames(
            v0_ms=v0_ms,
            decel=effective_decel,
            reaction_time=params.brake_reaction_time,
            distance_to_barrier=distance_to_barrier,
            hits_barrier=hits_barrier,
            brake_failure=params.brake_failure,
        )

        return RoadConditionResult(
            road_key=road_key,
            road_name=road.name,
            adhesion=road.adhesion,
            reaction_distance=round(reaction_distance, 2),
            braking_distance=round(min(braking_distance, 9999), 2),
            total_stopping_distance=round(min(total_stopping_distance, 9999), 2),
            time_to_stop=round(time_to_stop, 2),
            hits_barrier=hits_barrier,
            collision_speed_kmh=round(collision_speed_kmh, 1),
            collision_speed_ms=round(collision_speed_ms, 2),
            collision_energy_kj=round(collision_energy, 1),
            barrier_can_hold=barrier_can_hold,
            barrier_design_energy=barrier_design_energy,
            safety_margin=round(safety_margin, 1),
            frames=frames,
        )

    def _generate_frames(
        self, v0_ms: float, decel: float,
        reaction_time: float, distance_to_barrier: float,
        hits_barrier: bool,
        brake_failure: bool = False,
    ) -> List[TimeFrame]:
        frames = []
        t = 0
        speed = v0_ms
        position = 0
        is_braking = False
        is_stopped = False
        is_collision = False

        max_time = 30.0  # 最多模拟30秒
        max_frames = 600  # 最多600帧

        while t <= max_time and len(frames) < max_frames:
            frames.append(TimeFrame(
                time=round(t, 3),
                speed_kmh=round(speed / KM_H_TO_M_S, 1),
                speed_ms=round(speed, 2),
                position=round(position, 2),
                deceleration=round(decel if is_braking else 0, 2),
                is_braking=is_braking,
                is_stopped=is_stopped,
                is_collision=is_collision,
            ))

            if is_stopped or is_collision:
                break

            dt = self.DT

            # 更新状态
            if t < reaction_time:
                # 反应阶段：匀速
                position += speed * dt
            elif brake_failure:
                # 刹车失灵：完全不制动，匀速滑行
                position += speed * dt
            else:
                is_braking = True
                if decel > 0 and speed > self.MIN_SPEED * KM_H_TO_M_S:
                    # 制动阶段：匀减速
                    new_speed = speed - decel * dt
                    if new_speed <= self.MIN_SPEED * KM_H_TO_M_S:
                        new_speed = 0
                    # 位移：s = v*t - ½*a*t²
                    position += speed * dt - 0.5 * decel * dt * dt
                    speed = new_speed
                else:
                    speed = 0

            # 判定停止
            if speed <= self.MIN_SPEED * KM_H_TO_M_S and is_braking:
                speed = 0
                is_stopped = True

            # 判定撞击
            if position >= distance_to_barrier and not is_stopped:
                is_collision = True
                position = distance_to_barrier

            t += dt

        return frames

    def simulate(self, params: SimulationInput) -> SimulationResult:
        results_by_road = {}

        for road_key in ROAD_CONDITIONS:
            results_by_road[road_key] = self._simulate_single_road(params, road_key)

        # 汇总统计
        hit_count = sum(1 for r in results_by_road.values() if r.hits_barrier)
        fail_count = sum(1 for r in results_by_road.values() if r.hits_barrier and not r.barrier_can_hold)
        total_road_types = len(results_by_road)
        worst_case = max(
            (r for r in results_by_road.values() if r.hits_barrier),
            key=lambda r: r.collision_energy_kj,
            default=None
        )

        summary = {
            "total_road_types": total_road_types,
            "hit_count": hit_count,
            "safe_count": total_road_types - hit_count,
            "barrier_fail_count": fail_count,
            "worst_road": {
                "key": worst_case.road_key,
                "name": worst_case.road_name,
                "collision_speed": worst_case.collision_speed_kmh,
                "collision_energy": worst_case.collision_energy_kj,
                "barrier_can_hold": worst_case.barrier_can_hold,
            } if worst_case else None,
            "road_results_summary": [
                {
                    "key": r.road_key,
                    "name": r.road_name,
                    "adhesion": r.adhesion,
                    "hits_barrier": r.hits_barrier,
                    "collision_speed": r.collision_speed_kmh,
                    "barrier_can_hold": r.barrier_can_hold,
                }
                for r in results_by_road.values()
            ],
        }

        return SimulationResult(
            input_params={
                "vehicle_mass": params.vehicle_mass,
                "initial_speed": params.initial_speed,
                "brake_reaction_time": params.brake_reaction_time,
                "road_length": params.road_length,
                "slope_grade": params.slope_grade,
                "barrier_level": params.barrier_level,
                "barrier_name": get_barrier_level(params.barrier_level).name,
                "barrier_energy": get_barrier_level(params.barrier_level).design_energy,
                "brake_failure": params.brake_failure,
            },
            total_real_time=round(sum(len(r.frames) * self.DT for r in results_by_road.values()) / total_road_types, 2),
            results_by_road=results_by_road,
            summary=summary,
        )

    def simulate_single_road(
        self, params: SimulationInput, road_key: str
    ) -> RoadConditionResult:
        return self._simulate_single_road(params, road_key)

    def result_to_dict(self, result: SimulationResult) -> dict:

        def safe_float(val, default=99999):
            if val is None or (isinstance(val, float) and (math.isinf(val) or math.isnan(val))):
                return default
            return val

        road_results = {}
        for key, r in result.results_by_road.items():
            road_results[key] = {
                "road_key": r.road_key,
                "road_name": r.road_name,
                "adhesion": r.adhesion,
                "reaction_distance": r.reaction_distance,
                "braking_distance": safe_float(r.braking_distance),
                "total_stopping_distance": safe_float(r.total_stopping_distance),
                "time_to_stop": safe_float(r.time_to_stop),
                "hits_barrier": r.hits_barrier,
                "collision_speed_kmh": r.collision_speed_kmh,
                "collision_speed_ms": r.collision_speed_ms,
                "collision_energy_kj": r.collision_energy_kj,
                "barrier_can_hold": r.barrier_can_hold,
                "barrier_design_energy": r.barrier_design_energy,
                "safety_margin": safe_float(r.safety_margin, default=99999),
                "frames": [
                    {
                        "time": f.time,
                        "speed_kmh": f.speed_kmh,
                        "speed_ms": f.speed_ms,
                        "position": f.position,
                        "deceleration": f.deceleration,
                        "is_braking": f.is_braking,
                        "is_stopped": f.is_stopped,
                        "is_collision": f.is_collision,
                    }
                    for f in r.frames
                ],
            }

        return {
            "input_params": result.input_params,
            "total_real_time": result.total_real_time,
            "results_by_road": road_results,
            "summary": result.summary,
        }


def quick_simulate(
    mass: float = 1.5,
    speed: float = 80,
    reaction_time: float = 1.2,
    road_length: float = 100,
    slope: float = 0,
    barrier_level: str = "A",
) -> SimulationResult:
    params = SimulationInput(
        vehicle_mass=mass,
        initial_speed=speed,
        brake_reaction_time=reaction_time,
        road_length=road_length,
        slope_grade=slope,
        barrier_level=barrier_level,
    )
    return CollisionSimulator().simulate(params)


if __name__ == "__main__":

    result = quick_simulate(
        mass=1.5, speed=80, reaction_time=1.2,
        road_length=80, slope=0, barrier_level="A"
    )

    p = result.input_params
    print(f"\n参数: {p['vehicle_mass']}t @ {p['initial_speed']}km/h, "
          f"反应{p['brake_reaction_time']}s, 直道{p['road_length']}m, "
          f"坡度{p['slope_grade']}%, 护栏{p['barrier_level']}级({p['barrier_energy']}kJ)")
    print("-" * 60)

    for key, r in result.results_by_road.items():
        status = "撞击! " + ("阻挡失败" if not r.barrier_can_hold else "成功阻挡") if r.hits_barrier else "安全停止"
        print(f"  {r.road_name:16s} | 停车距离: {r.total_stopping_distance:7.1f}m | "
              f"{'撞击速度: ' + str(r.collision_speed_kmh) + 'km/h' if r.hits_barrier else '未撞击':20s} | {status}")

    print(f"\n汇总: {result.summary['hit_count']}/{result.summary['total_road_types']}种路面会撞击护栏, "
          f"{result.summary['barrier_fail_count']}种路面护栏无法阻挡")
