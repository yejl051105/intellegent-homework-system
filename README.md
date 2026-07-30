# 阅作 · 智能作业批改系统

结合 OCR 与大语言模型的作业批改平台：学生拍照上传作业，教师选择评分标准与 AI 模型一键生成批改草稿（分数、评语、错误框标注），在画布上复核调整后发布给学生。减少教师重复批改同份作业的次数，加快批改效率，提升教学质量。

## 功能特性

### 学生端

- **提交作业**：填写标题 + 上传图片，服务端同步完成 OCR 识别，原图字节原样保留
- **查看批改结果**：原图上叠加红色错误框与逐框扣分标注，附最终得分与教师评语（AI 草稿在教师确认前对学生不可见）
- **优秀作业墙**：浏览教师精选的优秀作业及其得分、评语
- **回收站**：软删除 / 恢复 / 永久删除，与教师侧相互独立

### 教师端

- **作业总览**：查看全部学生提交，跟踪批改状态（待 AI 评阅 / 待教师复核 / 已有得分）
- **AI 批改工作台**：选择评分标准与模型（DeepSeek / OpenAI / Gemini）生成草稿 → 在 fabric.js 画布上拖拽、缩放错误框并编辑逐框扣分（1–100 整数，最多 12 框）→ 调整分数评语后确认发布，也可重置重新生成
- **评分标准管理**：支持纯文本（≤12000 字），或上传 PDF / DOC / DOCX 附件自动提取文字
- **优秀作业管理**：一键设为优秀（独立拷贝图片，源作业删除不影响展示墙），也可直接上传展示作品
- **回收站**：与学生侧独立；学生、教师双方都永久删除后才真正清理磁盘文件

### 批改流程状态机

```
pending_ai ──AI 评阅──► ai_suggested ──教师确认──► confirmed
    ▲                       │                      │
    └────────重置评阅────────┴──────────────────────┘
```

教师不能跳过 AI 评阅直接打分（后端强制校验）；确认后结果才对学生可见。已确认的作业仍可重置或重新生成 AI 评阅，但会清空教师已确认的结果。

## 设计要点

- **坐标契约**：全链路统一 `coordinate_space: "source_pixel"`（原图像素坐标，原点左上）。LLM 只返回 OCR 行 id，错误框坐标由服务端按 id 反查 OCR 结果得到——模型给出的坐标永远不被信任；前端画布仅在渲染/编辑时换算显示坐标（`utils/coordinate.js`）。
- **后端驱动路由**：前端只静态注册登录页，登录后从 `GET /api/routes` 拉取当前角色的路由表，按组件文件名动态注册页面并生成导航菜单（`services/permission_service.py` 增删路由即可，前端无需改路由代码）。
- **按角色裁剪响应**：`api/serializers.py` 过滤字段，未复核的 AI 草稿（`ai_*` 字段）不会下发给学生；优秀作业墙走白名单字段。
- **AI 输出强校验**：模型必须返回严格 JSON（分数 0–100、评语、错题 id 列表与扣分），服务端逐项校验，不合格直接报错要求重新生成，绝不落库脏数据。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python ≥ 3.10 · FastAPI + Uvicorn · Starlette Session（Cookie 会话）· httpx |
| OCR | PaddleOCR（中文，首次识别时懒加载）· PP-FormulaNet_plus-S 公式识别（懒加载） |
| 文档解析 | pypdf（PDF）· python-docx（DOCX）· macOS `textutil`（DOC） |
| 前端 | Vue 3.5 + Vite 6 · Element Plus 2.14 · Vue Router 4（动态路由）· axios · fabric.js 7 · Less |
| 存储 | `data/` 下 JSON 文件（用户、作业、评分标准、优秀作业）· `uploads/` 上传文件 |
| 工具链 | uv（Python 依赖与运行）· npm |

## 项目结构

```
backend/                    # FastAPI 后端
├── main.py                 # 应用入口（app factory + SPA 托管，127.0.0.1:5000）
├── core/
│   └── config.py           # 路径、.env 加载、会话密钥等全局配置
├── api/                    # 接口层
│   ├── router.py           # 聚合并统一注册全部业务路由
│   ├── deps.py             # 请求依赖（登录/角色校验）
│   ├── serializers.py      # 按角色裁剪响应字段
│   └── routes/
│       ├── auth.py         # 登录、登出、当前用户、路由权限
│       ├── student.py      # 学生端：提交作业、查看批改结果、回收站、优秀作业
│       ├── teacher/        # 教师端：作业、AI 复核、评分标准、优秀作业子路由
│       └── recognition.py  # 独立识别接口：OCR / 公式 / 组合识别
├── schemas/
│   └── response.py         # Pydantic 统一响应模型
├── exceptions/             # 业务异常与系统异常
│   ├── base.py             # BaseAppException
│   ├── business/           # 用户、订单、认证及通用业务异常
│   │   ├── __init__.py
│   │   └── exceptions.py
│   └── system/             # Redis、数据库、第三方服务异常
│       ├── __init__.py
│       └── exceptions.py
├── handlers/
│   └── exception_handler.py # 全局异常处理器与集中注册函数
├── utils/
│   └── response.py         # success / fail 响应封装（fail 仅处理器使用）
└── services/               # 业务逻辑层
    ├── auth_service.py     # 用户认证（data/users.json）
    ├── permission_service.py  # 角色路由权限配置
    ├── homework_service.py # 作业领域兼容入口
    ├── homework/           # 查询、复核、回收站、评分标准、优秀作业
    ├── criteria_service.py # 评分标准附件文字提取
    ├── ocr_service.py      # OCR 领域兼容入口
    ├── ocr/                # 模型运行时、文档适配、上传存储
    ├── model_service.py    # 模型领域兼容入口
    └── model/              # 配置、提示词、结果校验、供应商调用

异常分层：

```text
BaseAppException
├── BusinessException
│   ├── UserException
│   ├── OrderException
│   └── AuthException
└── SystemException
    ├── RedisException
    ├── DatabaseException
    └── ThirdPartyServiceException
```

业务异常返回具体业务码；系统异常由全局处理器记录日志，并向客户端返回脱敏后的系统错误信息。

frontend/                   # Vue 3 + Element Plus 前端（Vite，`@` 指向 src/）
├── src/
│   ├── api/                # 接口层
│   │   ├── http.js         # axios 实例（baseURL /api，携带会话 Cookie）
│   │   ├── auth.js         # 登录、登出、当前用户、权限路由
│   │   ├── student.js      # 学生端接口
│   │   └── teacher.js      # 教师端接口
│   ├── router/             # 路由（根据后端权限动态注册，按组件文件名映射视图）
│   ├── layouts/            # 应用外壳（顶栏 AppHeader、导航 AppNav）
│   ├── views/
│   │   ├── student/        # 学生端页面（列表、上传、详情、优秀作业墙）
│   │   ├── teacher/        # 教师端页面（列表、批改工作台、评分标准、优秀作业）
│   │   └── shared/         # 双角色共用页面（登录、回收站、优秀作业详情）
│   ├── components/         # HomeworkAnnotationCanvas：fabric.js 错误框批注画布
│   ├── styles/             # Less 样式
│   └── utils/              # coordinate.js：原图像素坐标 ⇄ 画布显示坐标换算
└── dist/                   # 构建产物（后端直接托管）

data/                       # JSON 数据（users / homeworks / criteria / exemplary）
uploads/                    # 上传文件（original/ 下保留原图，经 /uploads 公开访问）
tests/                      # 后端单元测试（模型结果解析、OCR 坐标适配）
```

## 快速开始

### 环境要求

- Python ≥ 3.10 与 [uv](https://docs.astral.sh/uv/)
- Node.js 20+（前端，fabric 7 要求 Node ≥ 20）
- 首次启动会自动下载 PaddleOCR 模型（缓存在 `~/.paddlex/official_models/`），耗时较长属正常现象
- 解析 `.doc` 旧格式附件依赖 macOS 自带 `textutil`，其他平台请改用 PDF / DOCX

### 1. 配置环境变量

```bash
cp .env.example .env
```

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` | DeepSeek | `deepseek-v4-flash` · `https://api.deepseek.com` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI | `gpt-5.6` |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini | `gemini-3.5-flash` |
| `SESSION_SECRET_KEY` | 会话 Cookie 签名密钥（`.env.example` 未列出，需要时手动添加） | 有开发默认值，生产必须覆盖 |

只需配置想启用的模型，未配置的会在教师端置灰；前端只会收到"该模型是否可用"，永远拿不到密钥。**不要提交真实的 `.env`。**

### 2. 启动后端（http://127.0.0.1:5000）

```bash
uv run uvicorn backend.main:app --host 127.0.0.1 --port 5000 --reload
```

### 3. 启动前端开发服务器（http://localhost:5173）

```bash
cd frontend && npm install && npm run dev
```

开发服务器将 `/api` 与 `/uploads` 代理到后端 5000 端口，后端必须先启动。

### 测试账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 学生 | `student1` | `123456` |
| 教师 | `teacher1` | `123456` |

### 生产部署

```bash
cd frontend && npm run build
```

构建产物输出到 `frontend/dist/`，后端检测到后会直接托管（含 SPA history 路由回退与按角色跳转首页），此时只需运行后端即可。

## 测试

```bash
uv run python -m unittest discover -s tests
```

在仓库根目录运行（测试以 `backend.*` 绝对导入）。覆盖 AI 评阅结果解析（坐标信任链、非法扣分拒绝）与 PaddleOCR 坐标适配、原图保存。

## 已知限制（上线前必须处理）

- `data/users.json` 明文存储密码，仅供开发演示，正式环境需改为哈希（如 bcrypt）
- 独立识别接口 `POST /upload`、`/upload/formula`、`/upload/combined` 未做登录校验
- CORS 当前允许所有来源，需收紧为前端域名白名单
- JSON 文件存储为整文件读写、无并发锁，计划迁移 SQLite
- `/uploads` 目录公开可访问，上传文件未做访问控制
