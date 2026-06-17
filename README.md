# Quanta · 开发者工具链 Demo

面向具身智能算法 / 数据 / 标注开发者的工具链 Demo，门户 + 多平台架构：

- **数据平台** — 采集 → 质检 → 标注 → 数据集
- **模型平台** — 数据 → 训练 → 部署 → 评测
- **应用编排平台** — 模型服务 · 编排 · 资产
- **设备管理平台** — 设备 · 监测 · OTA

单文件 Flask 应用，集成 `data_platform.py` / `quanta_eval_platform.py` 作为模型平台数据 / 评测子模块。

## 本地运行

```bash
pip install -r requirements.txt
python toolchain_demo.py
# http://localhost:5004
```

## 部署 (Render)

仓库根目录已包含 `render.yaml` 蓝图。在 Render Dashboard → New + → Blueprint → 选择本仓库即可自动创建 Web Service。

启动命令：

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 toolchain_demo:app
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | 5004 | 监听端口（Render 会自动注入） |
| `DP_DIR` | 脚本所在目录 | data_platform.py 所在目录 |
| `EP_DIR` | 脚本所在目录 | quanta_eval_platform.py 所在目录 |
