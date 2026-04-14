# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2026-04-14

### 新增

- **Entry Input Skill** 个人信息录入系统首次发布
- `init` 命令：初始化系统，创建配置文件和目录结构
- `add` 命令：新增记录，支持纯文本和附件
- `list` 命令：查看记录列表（支持按日期、今日、全部）
- `show` 命令：查看单条记录详情
- `edit` 命令：编辑记录（添加附件）
- `delete` 命令：删除记录（仅供用户直接操作）
- `config` 命令：配置管理
- `git-push` 命令：推送到远程仓库
- `backup` 命令：加密增量备份（Restic）

### 功能特性

- Markdown 纯文本存储，无 YAML front matter
- 时间戳文件命名：`YYYYMMDD_HHMMSS.md`
- `#` 标签标记分类（todo/memo/idea/note/project）
- 附件自动处理：复制 → 重命名 → 添加引用
- 当日索引自动生成（Obsidian `![[ ]]` 嵌入语法）
- Git 自动提交记录变更
- 配置文件模板 `config.yaml.example`

### 安全设计

- **Agent 禁删**：Agent 无删除权限，保护用户数据
- **原样保存**：Agent 不篡改用户输入，不自动添加标签
- **用户可编辑**：纯文本格式，用户可直接修改文件

### 测试

- 40 个单元测试全部通过
- 覆盖配置管理、Git 管理、记录 CRUD、附件处理、边界情况

### 文档

- 设计方案文档 `docs/录入系统设计方案.md`
- Skill 说明文档 `skills/entry_input/SKILL.md`
- Agent 指南更新（禁止删除、禁止篡改）

---

## 版本规划

### [1.1.0] - 待定

- 改进错误处理和用户提示
- 支持更多附件类型预览
- 配置文件交互式编辑

### [2.0.0] - 待定

- 引入队列系统（persist-queue）
- 与分析系统同步
- 定时自动备份
- 分析系统开发（向量数据库 + LLM）