# Anime Fighter Web

基于 Phaser 3 + JavaScript + Vite 的 Web 端 AI 卡通横版格斗游戏。用户上传照片后，后端仅提取并动漫化头像；前端把透明头像挂载到完整格斗身体模板上，保证自拍、半身照和全身照都能生成完整角色。

## 已实现功能

- A/D 移动、W 跳跃、S 下蹲、Shift + 方向滑跳
- J 普通攻击，Q/E/R 三个技能
- 攻击框、受伤框、击退、无敌帧和血量条
- PVE 自动移动与攻击 AI
- 动态加载后端生成的头像和卡通场景
- 头像与预制格斗身体组合，四肢随移动和跳跃摆动
- 预留 WebSocket PVP 接口

## 项目结构

```text
.
├── index.html
├── package.json
├── .env.example
└── src
    ├── config/gameplay.js
    ├── entities/Fighter.js
    ├── scenes/
    ├── services/AnimeGanService.js
    ├── services/MultiplayerGateway.js
    ├── systems/
    └── ui/AssetGeneratorController.js
```

## 启动

要求 Node.js 18+：

```bash
npm install
npm start
```

打开 `http://127.0.0.1:5173/`。

修改后端地址时，把 `.env.example` 复制为 `.env.local`：

```dotenv
VITE_ANIMEGAN_API_URL=http://127.0.0.1:8000
```

## 后端接口

后端代码位于同一仓库的 `backend`（兼容原 `feature/backend-dev`）分支，默认地址为 `http://127.0.0.1:8000`。

人物头像流程：

1. `POST /api/v1/avatars/analyze`
   - `multipart/form-data`，字段 `file`
   - 自动裁出脸、头发和耳饰，返回 `avatar_id` 与 `features`
2. `POST /api/v1/avatars/compose`
   - JSON：`{ "avatar_id": "...", "features": { ... } }`
   - 生成透明二维动漫头像，失败时自动使用本地保真卡通化
3. 前端读取 `image.url`，把头像挂到 Phaser 格斗身体模板

背景接口：

```http
POST /api/v1/backgrounds/cartoonize
Content-Type: application/json

{"prompt":"夜晚霓虹都市屋顶"}
```

健康检查：`GET /api/health`。

## 后端环境变量

在后端分支将 `.env.example` 复制为 `.env`。不要提交真实密钥：

```dotenv
NAILONG_ZHIPU_API_KEY=
NAILONG_OPENAI_API_KEY=
NAILONG_OPENAI_BASE_URL=https://api.example.com/v1
NAILONG_OPENAI_IMAGE_MODEL=gpt-image-2
NAILONG_DEVICE=cpu
NAILONG_DISABLE_MEDIAPIPE=true
```

## 直接指定素材

```text
?player=https://example.com/head.png&opponent=https://example.com/enemy.png&background=https://example.com/stage.jpg
```

接口封装位于 `src/services/AnimeGanService.js`，生成页面控制位于 `src/ui/AssetGeneratorController.js`。

## 参考说明

运动状态、跳跃速度、攻击框/受伤框、击退、血量和场景分层思路参考 `samurai-js/sf3js-old`（MIT）。本项目为重新设计的 Phaser 3 ES Module 实现，没有复制原仓库素材或完整项目。
