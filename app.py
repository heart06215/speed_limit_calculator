"""道路护栏安全设计系统 v4.1 - Flask后端"""

import os
import sys
import json
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, make_response

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
FRONT_DIR = os.path.join(BASE_DIR, "front")
CALCULATE_DIR = os.path.join(BASE_DIR, "calculate")
DATA_DIR = os.path.join(BASE_DIR, "data")  # JSON数据存储目录
os.makedirs(DATA_DIR, exist_ok=True)


def send_html(filename):
    resp = make_response(send_from_directory(FRONT_DIR, filename))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

app = Flask(__name__, static_folder=None, template_folder=None)
from flask_cors import CORS
CORS(app)

HISTORY_FILE = os.path.join(DATA_DIR, "simulation_history.json")

def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def _save_history(records):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

_next_id = [0]
def _next_record_id():
    _next_id[0] += 1
    return _next_id[0]


@app.route("/")
def landing():
    return send_html("landing.html")


@app.route("/simulator")
def index():
    return send_html("index.html")


@app.route("/map")
def map_page():
    return send_html("map.html")


@app.route("/province/<name>")
def province_page(name):
    return send_html("province.html")


@app.route("/history")
def history_page():
    return send_html("history.html")


@app.route("/chat")
def chat_page():
    return send_html("chat.html")


@app.route("/api/data", methods=["GET"])
def api_get_data():
    from calculate.sample import get_all_data_summary
    data = get_all_data_summary()
    return jsonify({"success": True, "data": data})


@app.route("/api/data/road-conditions", methods=["GET"])
def api_get_road_conditions():
    from calculate.sample import ROAD_CONDITION_LIST
    return jsonify({"success": True, "data": ROAD_CONDITION_LIST})


@app.route("/api/data/barrier-levels", methods=["GET"])
def api_get_barrier_levels():
    from calculate.sample import BARRIER_LEVEL_LIST
    return jsonify({"success": True, "data": BARRIER_LEVEL_LIST})


@app.route("/api/data/vehicle-presets", methods=["GET"])
def api_get_vehicle_presets():
    from calculate.sample import VEHICLE_PRESET_LIST
    return jsonify({"success": True, "data": VEHICLE_PRESET_LIST})


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    try:
        from calculate.collision_simulator import CollisionSimulator, SimulationInput

        data = request.get_json(force=True)
        params = SimulationInput(
            vehicle_mass=float(data.get("vehicle_mass", 1.5)),
            initial_speed=float(data.get("initial_speed", 80)),
            brake_reaction_time=float(data.get("brake_reaction_time", 1.2)),
            road_length=float(data.get("road_length", 100)),
            slope_grade=float(data.get("slope_grade", 0)),
            barrier_level=str(data.get("barrier_level", "A")),
            brake_failure=bool(data.get("brake_failure", False)),
        )

        # 参数校验
        if params.vehicle_mass <= 0 or params.vehicle_mass > 50:
            return jsonify({"success": False, "error": "车辆质量应在0.1~50吨之间"}), 400
        if params.initial_speed <= 0 or params.initial_speed > 300:
            return jsonify({"success": False, "error": "速度应在0~300 km/h之间"}), 400
        if params.road_length <= 0 or params.road_length > 10000:
            return jsonify({"success": False, "error": "道路长度应在0~10000米之间"}), 400
        if params.barrier_level not in ("B", "A", "SB", "SA", "SS", "HB"):
            return jsonify({"success": False, "error": f"无效护栏等级: {params.barrier_level}"}), 400

        simulator = CollisionSimulator()
        result = simulator.simulate(params)
        result_dict = simulator.result_to_dict(result)

        return jsonify({
            "success": True,
            "data": result_dict,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/simulate/single", methods=["POST"])
def api_simulate_single():
    try:
        from calculate.collision_simulator import CollisionSimulator, SimulationInput
        import math as _math

        data = request.get_json(force=True)
        params = SimulationInput(
            vehicle_mass=float(data.get("vehicle_mass", 1.5)),
            initial_speed=float(data.get("initial_speed", 80)),
            brake_reaction_time=float(data.get("brake_reaction_time", 1.2)),
            road_length=float(data.get("road_length", 100)),
            slope_grade=float(data.get("slope_grade", 0)),
            barrier_level=str(data.get("barrier_level", "A")),
            brake_failure=bool(data.get("brake_failure", False)),
        )
        road_key = str(data.get("road_key", "dry_asphalt"))

        simulator = CollisionSimulator()
        result = simulator.simulate_single_road(params, road_key)

        def _safe(v, d=99999):
            if v is None or (isinstance(v, float) and (_math.isinf(v) or _math.isnan(v))):
                return d
            return v

        return jsonify({
            "success": True,
            "data": {
                "road_key": result.road_key,
                "road_name": result.road_name,
                "adhesion": result.adhesion,
                "reaction_distance": result.reaction_distance,
                "braking_distance": _safe(result.braking_distance),
                "total_stopping_distance": _safe(result.total_stopping_distance),
                "time_to_stop": _safe(result.time_to_stop),
                "hits_barrier": result.hits_barrier,
                "collision_speed_kmh": result.collision_speed_kmh,
                "collision_speed_ms": result.collision_speed_ms,
                "collision_energy_kj": result.collision_energy_kj,
                "barrier_can_hold": result.barrier_can_hold,
                "barrier_design_energy": result.barrier_design_energy,
                "safety_margin": _safe(result.safety_margin),
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
                    for f in result.frames
                ],
            },
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/climate", methods=["GET"])
def api_climate():
    """获取气候数据（按省份聚合的气温和降水数据）"""
    climate_file = os.path.join(CALCULATE_DIR, "climate_data.json")
    if not os.path.exists(climate_file):
        return jsonify({"success": False, "error": "气候数据文件不存在"}), 404
    try:
        with open(climate_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/standards", methods=["GET"])
def api_standards():
    std_file = os.path.join(CALCULATE_DIR, "standards.json")
    if not os.path.exists(std_file):
        return jsonify({"success": False, "error": "国标数据文件不存在"}), 404
    try:
        with open(std_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def api_get_history():
    records = _load_history()
    return jsonify({"success": True, "data": records})


@app.route("/api/history", methods=["POST"])
def api_save_history():
    try:
        data = request.get_json(force=True)
        record = {
            "id": int(time.time() * 1000) % 100000000,
            "timestamp": datetime.now().isoformat(),
            "province": data.get("province", ""),
            "location": data.get("location", ""),
            "params": {
                "vehicle_mass": data.get("vehicle_mass"),
                "initial_speed": data.get("initial_speed"),
                "brake_reaction_time": data.get("brake_reaction_time"),
                "road_length": data.get("road_length"),
                "slope_grade": data.get("slope_grade"),
                "barrier_level": data.get("barrier_level"),
                "brake_failure": data.get("brake_failure", False),
            },
            "results": data.get("results", {}),
        }
        records = _load_history()
        records.append(record)
        _save_history(records)
        return jsonify({"success": True, "id": record["id"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/history/<int:record_id>", methods=["DELETE"])
def api_delete_history(record_id):
    records = _load_history()
    records = [r for r in records if r.get("id") != record_id]
    _save_history(records)
    return jsonify({"success": True})


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    _save_history([])
    return jsonify({"success": True})


@app.route("/api/health", methods=["GET"])
def api_health():
    """API健康检查"""
    checks = {"flask": True, "numpy": False, "simulator": False}
    try:
        import numpy
        checks["numpy"] = True
    except ImportError:
        pass
    try:
        from calculate.collision_simulator import CollisionSimulator
        checks["simulator"] = True
    except ImportError:
        pass

    return jsonify({
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks,
        "version": "3.0.0",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
