---
name: entry_input
description: 个人信息录入系统 - 简洁、稳定、用户友好的记录录入工具。使用 Markdown 纯文本存储，时间戳文件命名，# 标签标记分类，Git 版本控制，支持附件管理和加密备份。第一版不包含队列系统。
metadata: { "builtin_skill_version": "1.0.0", "copaw": { "emoji": "📝" } }
---

# Entry Input（个人信息录入系统）Skill

## 概述

Entry Input 是一个**简洁稳定**的个人信息录入系统，核心理念：

> **原始数据保持简单干净，用户可直接查看和编辑**

---

## 🚫 Agent 安全约束

### 绝对禁止删除数据

**Agent 绝对禁止使用任何手段删除用户的任何数据。**

- delete 命令仅供用户直接操作使用
- Agent 无删除权限，必须保护用户数据安全
- 当用户要求删除时，Agent 应回复"没有删除权限，请手动删除"

### 绝对禁止篡改用户输入

**Agent 必须一字不差地保存用户输入，不可添加或修改任何内容。**

- 不可自动添加标签
- 不可修改用户输入内容
- 用户说什么，就记录什么

---

## 配置与数据目录

### 配置文件位置

> 📍 配置文件 `config.yaml` 存放在 **skill 目录**下。

首次运行 `init` 命令时，系统会在 skill 目录下创建 `config.yaml`。

**示例路径**：
- Skill 目录：`~/.copaw/workspaces/personal_assistant/skills/entry_input/`
- 配置文件：`~/.copaw/workspaces/personal_assistant/skills/entry_input/config.yaml`

### 数据目录位置

> 📍 数据目录由配置文件中的 `raw_path` 指定，默认为 `~/PIMS_repo`。

首次运行 `init` 命令时，系统会询问数据目录位置，并在该目录下创建数据结构。

**示例路径**：
- 数据目录：`~/PIMS_repo/`（用户指定）

---

## 目录结构

```
~/PIMS_repo/                       # 数据目录（raw_path，用户指定）
├── .git/                          # Git 仓库（自动初始化）
├── raw/                           # 记录数据目录
│   └── 2026/
│       └── 20260414/
│           ├── 20260414.md        # 当日索引
│           ├── 20260414_120000.md # 单条记录
│           └── attachment/        # 附件目录
│               └── 20260414_120000_abc12345.pdf
└── backups/                       # 备份仓库（默认位置）

skill_dir/                         # Skill 目录
├── SKILL.md                       # Skill 说明文档
├── config.yaml                    # 配置文件（存放在此）
├── config.yaml.example            # 配置模板（供参考）
├── index.py                       # 主入口脚本
└── tests/                         # 测试目录
```

---

## Skill 目录结构（源码）

```
entry_input/                       # Skill 源码目录
├── SKILL.md                       # Skill 说明文档
├── config.yaml.example            # 配置模板（供参考）
├── index.py                       # 主入口脚本
├── tests/                         # 测试目录
│   └── test_entry_input.py
└── docs/                          # 文档目录

---

## 何时使用

### 应该使用
- 用户要快速记录一条信息
- 用户说"记一下"、"备忘"、"写下"
- 用户要查看某日的记录列表
- 用户要保存附件并关联到记录

### 不应使用
- 需要复杂的分类和智能分析（使用分析系统）
- 需要任务提醒功能（第一版不支持）

## 使用方式

### 1. 初始化系统

首次使用时初始化：

```bash
python skills/entry_input/index.py init
```

系统会询问数据目录位置，创建配置文件，初始化 Git 仓库。

### 2. 添加记录

```bash
# 基础添加（原样保存用户输入）
python skills/entry_input/index.py add "这是一条记录"

# 用户自带标签（原样保存）
python skills/entry_input/index.py add "#todo #project-A 完成设计文档"

# 带附件（系统自动处理）
python skills/entry_input/index.py add "拍了一张照片" --attach ~/Downloads/photo.jpg
```

> ⚠️ **Agent 注意**：add 命令的内容必须原样保存用户输入，不可自动添加标签。

> 📎 **附件处理**：`--attach` 参数会自动将用户原文件复制到当日 `attachment/` 目录，并重命名为 `YYYYMMDD_HHMMSS_UUID.类型` 格式，同时在记录中添加附件引用。Agent 只需提供用户原文件路径，无需手动处理复制和重命名。

### 3. 查看记录

```bash
# 查看某日记录列表
python skills/entry_input/index.py list 2026-03-01

# 查看今日记录
python skills/entry_input/index.py list today

# 查看单条记录
python skills/entry_input/index.py show 20260301_122334
```

### 4. 编辑记录

```bash
# 添加附件到现有记录
python skills/entry_input/index.py edit 20260301_122334 --attach ~/Downloads/doc.pdf
```

> 🚫 **Agent 禁止使用 --content 参数修改记录内容。**

> 用户可手动编辑文件：raw/YYYY/YYYYMMDD/YYYYMMDD_HHMMSS.md

### 5. 删除记录

```bash
# 删除记录（同时删除附件）
python skills/entry_input/index.py delete 20260301_122334
```

> 🚫 **Agent 绝对禁止执行 delete 命令。**
>
> 此命令仅供用户直接操作使用，Agent 无删除权限。

### 6. 配置管理

```bash
# 查看当前配置
python skills/entry_input/index.py config

# 更新数据目录路径
python skills/entry_input/index.py config --raw-path ~/Documents/PIMS_data

# 设置备份目录
python skills/entry_input/index.py config --backup.repo-path ~/PIMS_repo/backups

# 设置 Git 远程仓库
python skills/entry_input/index.py config --git-remote git@github.com:xxx/private.git
```

### 7. Git 操作

```bash
# 推送到远程仓库
python skills/entry_input/index.py git-push
```

### 8. 备份操作

```bash
# 执行加密备份（使用 Restic）
python skills/entry_input/index.py backup

# 查看备份快照列表
python skills/entry_input/index.py backup --list

# 恢复备份
python skills/entry_input/index.py backup --restore latest --target /path/to/restore
```

## 记录格式

### 文件命名

`YYYYMMDD_HHMMSS.md`

示例：`20260301_122334.md`

### 文件内容

纯文本，无 YAML front matter：

```
#todo #project-A this project is late for timeline.
```

### 标签约定（仅供参考）

| 格式 | 含义 |
|-----|------|
| `#todo` | 待办事项 |
| `#memo` | 备忘 |
| `#idea` | 想法 |
| `#project-xxx` | 所属项目 |
| `#xxx` | 其他标签 |

> ⚠️ **注意**：标签仅供用户参考，Agent 不自动添加。只有用户在输入中明确写了标签才保存。

### 附件引用

系统会自动在记录中添加附件引用：

```
#todo 拍了一张设计草图：

[[attachment/20260301_122334_a1b2c3d4.jpg]]
```

> 📎 **自动处理**：使用 `--attach` 参数时，系统自动完成：复制文件 → 重命名 → 添加引用。

## 配置文件说明

配置文件存放在 skill 目录下（如 `~/.copaw/workspaces/personal_assistant/skills/entry_input/config.yaml`），主要配置项：

| 配置项 | 说明 | 默认值 |
|-------|------|--------|
| `raw_path` | 数据目录路径 | `~/PIMS_repo` |
| `git_auto_commit` | 自动 Git 提交 | `true` |
| `git_auto_push` | 自动推送远程 | `false` |
| `git_remote_url` | 远程仓库地址 | 空 |
| `backup.repo_path` | 备份仓库路径 | `~/PIMS_repo/backups` |

> 📍 配置模板参考：`skill_dir/config.yaml.example`

> 💡 所有路径支持 `~` 符号（用户主目录）

## 安全机制

- **Git 版本控制**：所有变更自动提交，支持历史回溯
- **私有远程仓库**：不推送公开仓库，保护隐私
- **加密备份**：使用 Restic 增量加密备份
- **用户可编辑**：Markdown 纯文本，用户可直接修改
- **Agent 禁删**：Agent 无删除权限，保护数据安全
- **原样保存**：Agent 不篡改用户输入，保持原始记录完整

## 第一版说明

第一版不包含以下功能（待录入系统稳定后加入）：
- 队列系统（persist-queue）
- 与分析系统的自动同步
- 定时自动备份（需手动执行 backup 命令）

## 测试

运行测试套件：

```bash
cd skills/entry_input
python -m pytest tests/
```

## 依赖

- Python >= 3.10
- PyYAML
- Git（系统安装）
- Restic（可选，用于加密备份）

---

**版本**: v1.0.1
**更新日期**: 2026-04-14

## 详细文档

完整设计方案请参阅：项目仓库 `docs/录入系统设计方案.md`