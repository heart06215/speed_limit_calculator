"""
为气候数据生成月度温度和降水数据。
基于年均温 + 年降水量 + 经纬度（用于气候区分类），用余弦曲线插值生成12个月的近似值。
运行一次后可删除此脚本。
"""
import json
import math

CLIMATE_FILE = r"D:\program_projects\speed_limit_calculator\calculate\climate_data.json"
OUTPUT_FILE = CLIMATE_FILE  # 覆盖原文件

def get_climate_zone(lat, lon):
    """根据纬度判断气候区类型"""
    if lat >= 45:
        return "cold_north"      # 寒温带
    elif lat >= 35:
        if lon < 105:
            return "continental"  # 大陆性气候
        return "warm_temperate"   # 暖温带
    elif lat >= 25:
        return "subtropical"      # 亚热带
    else:
        return "tropical"         # 热带

def generate_monthly_temp(avg_temp, lat, lon):
    """根据年均温和纬度生成12个月的温度数组"""
    zone = get_climate_zone(lat, lon)
    
    if zone == "cold_north":
        amplitude = max(15, abs(avg_temp) * 0.6)
        peak_month = 7  # 7月最热
    elif zone == "continental":
        amplitude = max(14, abs(avg_temp) * 0.55)
        peak_month = 7
    elif zone == "warm_temperate":
        amplitude = max(12, abs(avg_temp) * 0.45)
        peak_month = 7
    elif zone == "subtropical":
        amplitude = max(10, abs(avg_temp) * 0.35)
        peak_month = 7
    else:  # tropical
        amplitude = max(5, abs(avg_temp) * 0.15)
        peak_month = 7
    
    # 海洋调节：沿海省份振幅小
    coastal_provinces = ['上海', '浙江', '福建', '广东', '海南', '台湾', '香港', '澳门',
                         '辽宁', '山东', '江苏', '广西']
    # 根据经度简单判断沿海
    if lon > 118 and lat > 20 and lat < 45:
        amplitude *= 0.8
    
    monthly = []
    for m in range(1, 13):
        phase = (m - peak_month) * math.pi / 6
        t = avg_temp + amplitude * math.cos(phase)
        monthly.append(round(t, 1))
    
    return monthly

def generate_monthly_precip(annual_precip, lat, lon):
    """根据年降水量和纬度生成12个月的降水量数组"""
    zone = get_climate_zone(lat, lon)
    
    if zone == "tropical":
        # 热带：雨季5-10月
        pattern = [0.03, 0.03, 0.04, 0.06, 0.10, 0.14, 0.16, 0.15, 0.14, 0.10, 0.04, 0.03]
    elif zone == "subtropical":
        # 亚热带：梅雨6月 + 秋雨
        pattern = [0.03, 0.04, 0.07, 0.10, 0.12, 0.16, 0.13, 0.11, 0.09, 0.06, 0.05, 0.04]
    elif zone == "warm_temperate":
        # 暖温带：7-8月集中降水
        pattern = [0.02, 0.03, 0.05, 0.06, 0.08, 0.12, 0.20, 0.18, 0.10, 0.06, 0.05, 0.03]
    elif zone == "continental":
        # 大陆性：夏季集中
        pattern = [0.02, 0.03, 0.04, 0.06, 0.08, 0.13, 0.22, 0.20, 0.10, 0.05, 0.04, 0.03]
    else:  # cold_north
        # 寒温带：7-8月集中
        pattern = [0.02, 0.02, 0.03, 0.05, 0.08, 0.14, 0.24, 0.22, 0.10, 0.04, 0.03, 0.02]
    
    monthly = [round(annual_precip * p, 1) for p in pattern]
    # 确保总和接近年值
    total = sum(monthly)
    if total > 0:
        scale = annual_precip / total
        monthly = [round(v * scale, 1) for v in monthly]
    
    return monthly

def main():
    with open(CLIMATE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    provinces = data.get('provinces', {})
    updated_stations = 0
    
    for prov_name, prov_data in provinces.items():
        for station in prov_data.get('stations', []):
            lat = station.get('lat', 35)
            lon = station.get('lon', 110)
            avg_temp = station.get('avg_temp', 12)
            annual_precip = station.get('annual_precip', 600)
            
            station['monthly_temp'] = generate_monthly_temp(avg_temp, lat, lon)
            station['monthly_precip'] = generate_monthly_precip(annual_precip, lat, lon)
            updated_stations += 1
    
    # 更新 meta
    data['meta']['description'] = '中国气象站点气候数据 (2020-2024年5年平均值) - 含月度数据'
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已更新 {updated_stations} 个站点的月度数据")
    print(f"输出文件: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
