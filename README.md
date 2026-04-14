# PIMS v2 - 个人信息管理系统

> Personal Information Management System

## 项目简介

PIMS v2 是一个简洁、稳定、用户友好的个人信息管理系统，分为两部分：

- **录入系统**：快速记录个人信息，支持标签、附件、Git 版本控制
- **分析系统**：（待开发）基于向量数据库和 LLM 的智能分析

### 核心特性

- ✅ Markdown 纯文本存储，用户可直接查看和编辑
- ✅ 时间戳文件命名，易于查找和管理
- ✅ `#` 标签标记分类，简单直观
- ✅ 附件自动复制、重命名、引用
- ✅ Git 版本控制，支持历史回溯
- ✅ 加密增量备份（Restic）
- ✅ Agent 安全约束：禁止删除、禁止篡改用户数据

---

## Entry Input Skill

个人信息录入系统的第一版实现。

### 快速开始

```bash
# 进入 skill 目录
cd skills/entry_input

# 初始化系统（首次使用）
python index.py init

# 添加记录
python index.py add "这是一条测试记录"
python index.py add "#todo #project/xxx 完成设计文档"

# 查看记录
python index.py list today
python index.py show YYYYMMDD_HHMMSS
```

### 命令列表

| 命令 | 功能 |
|-----|------|
| `init` | 初始化系统，创建配置和目录 |
| `add <内容>` | 新增记录 |
| `add <内容> --attach <文件>` | 新增记录并保存附件 |
| `list [日期]` | 查看记录列表 |
| `show <ID>` | 查看单条记录详情 |
| `edit <ID> --attach <文件>` | 添加附件到已有记录 |
| `delete <ID>` | 删除记录 |
| `config` | 查看配置 |
| `git-push` | 推送到远程仓库 |
| `backup` | 执行加密备份 |

### 目录结构

```
raw/
└── 2026/
    └── 20260414/
        ├── 20260414.md              # 当日索引
        ├── 20260414_120000.md       # 单条记录
        └── attachment/              # 附件目录
            └── 20260414_120000_abc12345.pdf
```

### 配置

参考 `config.yaml.example` 创建自己的配置文件：

```yaml
raw_path: ./raw                     # 数据存储路径
git_auto_commit: true               # 自动提交
git_auto_push: false                # 自动推送
git_remote_url: ''                  # 远程仓库地址

backup:
  enabled: true
  tool: restic                      # 备份工具
  repo_path: ./backup-repo
  schedule: daily
```

---

## Agent 安全约束

本系统设计为 AI Agent 助手的个人信息管理工具，内置安全约束：

### 禁止删除

**Agent 绝对禁止删除用户数据。**

- delete 命令仅供用户直接操作使用
- Agent 无删除权限，必须保护用户数据安全

### 禁止篡改

**Agent 必须一字不差保存用户输入。**

- 不自动添加标签
- 不修改用户输入内容
- 用户说什么，就记录什么

---

## 依赖

- Python >= 3.10
- PyYAML
- Git（系统安装）
- Restic（可选，用于加密备份）

## 测试

```bash
cd skills/entry_input
python -m pytest tests/ -v
```

---

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 许可证

MIT License

## 作者

Lancewer