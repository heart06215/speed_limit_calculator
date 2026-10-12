# speed_limit_calculator

> 竞赛赛区获奖作品存放

一个用于**道路限速计算**的 Python 工具：根据道路等级、气候条件与历史事故数据，计算推荐限速值，并输出可视化结果。

## 功能

- **限速计算引擎**（`calculate/`）：按道路等级、天气与事故率等参数计算推荐限速
- **气候数据更新**（`update_climate.py`）：拉取并更新气候数据集
- **数据核验**（`verify.py`）：校验输入数据完整性与计算结果合理性
- **可视化输出**（`china_housing_map.html`、`front/`）：生成地图与前端展示页面
- **可部署**：提供 `Procfile` 与 `pyproject.toml`，支持 Render 等平台部署

## 目录结构

```
speed_limit_calculator/
├── app.py                 # 主程序入口
├── calculate/             # 限速计算核心逻辑
├── front/                 # 前端展示页面
├── data/                  # 运行时数据（已忽略）
├── update_climate.py      # 气候数据更新
├── verify.py              # 数据与结果校验
├── requirements.txt       # 依赖
├── pyproject.toml         # 项目配置
├── build.spec             # 打包配置
└── Procfile               # 部署配置
```

## 运行

```bash
pip install -r requirements.txt
python app.py
```

## 说明

- `data_resource/` 与 `software_result/` 中的大体量数据文件与打包产物不纳入版本管理，请按需自行准备
- 打包：`pyinstaller build.spec`

## 许可

MIT License
