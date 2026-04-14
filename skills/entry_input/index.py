#!/usr/bin/env python3
"""
Entry Input - 个人信息录入系统
简洁、稳定、用户友好的记录录入工具

版本: v1.0.0
"""

import argparse
import subprocess
import shutil
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


# ============================================================================
# 配置管理
# ============================================================================

DEFAULT_CONFIG = {
    'raw_path': './raw',
    'git_auto_commit': True,
    'git_auto_push': False,
    'git_remote_url': '',
    'backup': {
        'enabled': True,
        'tool': 'restic',
        'repo_path': './backup-repo',
        'schedule': 'daily'
    }
}


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
        self.config_file = skill_dir / 'config.yaml'
        self.config = self.load()
    
    def load(self) -> dict:
        """加载配置"""
        if self.config_file.exists():
            return yaml.safe_load(self.config_file.read_text())
        return DEFAULT_CONFIG.copy()
    
    def save(self):
        """保存配置"""
        self.config_file.write_text(yaml.dump(self.config, allow_unicode=True, default_flow_style=False))
    
    def get_raw_path(self) -> Path:
        """获取 raw 库路径（解析为绝对路径）"""
        raw_path = self.config.get('raw_path', './raw')
        # 先展开 ~ 符号，再判断是否绝对路径
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            p = self.skill_dir / p
        return p.resolve()
    
    def update(self, key: str, value: str):
        """更新配置项"""
        if key == 'raw-path':
            self.config['raw_path'] = value
        elif key == 'git-remote':
            self.config['git_remote_url'] = value
        elif key == 'git-auto-commit':
            self.config['git_auto_commit'] = value.lower() in ('true', 'yes', '1')
        elif key == 'git-auto-push':
            self.config['git_auto_push'] = value.lower() in ('true', 'yes', '1')
        elif key.startswith('backup.'):
            backup_key = key.split('.', 1)[1]
            self.config['backup'][backup_key] = value
        else:
            self.config[key] = value
        self.save()


# ============================================================================
# Git 管理
# ============================================================================

class GitManager:
    """Git 版本控制管理器"""
    
    def __init__(self, raw_path: Path):
        self.raw_path = raw_path
        self.git_dir = raw_path / '.git'
    
    def is_initialized(self) -> bool:
        """检查 Git 是否已初始化"""
        return self.git_dir.exists()
    
    def init(self):
        """初始化 Git 仓库"""
        if not self.is_initialized():
            subprocess.run(['git', 'init'], cwd=self.raw_path, check=True, capture_output=True)
            # 创建初始提交
            subprocess.run(['git', 'add', '.'], cwd=self.raw_path, check=True, capture_output=True)
            result = subprocess.run(
                ['git', 'commit', '-m', 'init: 初始化录入系统'],
                cwd=self.raw_path,
                capture_output=True,
                text=True
            )
            # 可能没有文件，commit 可能失败，忽略
    
    def commit(self, message: str):
        """提交变更"""
        subprocess.run(['git', 'add', '.'], cwd=self.raw_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', message], cwd=self.raw_path, check=True, capture_output=True)
    
    def push(self):
        """推送到远程仓库"""
        result = subprocess.run(
            ['git', 'push'],
            cwd=self.raw_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"推送失败: {result.stderr}")
            return False
        print("推送成功")
        return True
    
    def set_remote(self, url: str):
        """设置远程仓库"""
        # 先检查是否已有 remote
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=self.raw_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # 已有，更新
            subprocess.run(['git', 'remote', 'set-url', 'origin', url], cwd=self.raw_path, check=True)
        else:
            # 没有，添加
            subprocess.run(['git', 'remote', 'add', 'origin', url], cwd=self.raw_path, check=True)


# ============================================================================
# 记录管理
# ============================================================================

class EntryManager:
    """记录管理器"""
    
    def __init__(self, raw_path: Path):
        self.raw_path = raw_path
    
    def get_year_dir(self, date: datetime) -> Path:
        """获取年份目录"""
        return self.raw_path / str(date.year)
    
    def get_day_dir(self, date: datetime) -> Path:
        """获取日期目录"""
        return self.get_year_dir(date) / date.strftime('%Y%m%d')
    
    def get_attachment_dir(self, date: datetime) -> Path:
        """获取附件目录"""
        return self.get_day_dir(date) / 'attachment'
    
    def get_entry_filename(self, date: datetime) -> str:
        """生成记录文件名"""
        return date.strftime('%Y%m%d_%H%M%S') + '.md'
    
    def get_index_filename(self, date: datetime) -> str:
        """获取索引文件名"""
        return date.strftime('%Y%m%d') + '.md'
    
    def parse_entry_id(self, filename: str) -> datetime:
        """从文件名解析时间"""
        # 格式: YYYYMMDD_HHMMSS.md
        stem = Path(filename).stem
        try:
            return datetime.strptime(stem, '%Y%m%d_%H%M%S')
        except ValueError:
            return None
    
    def get_weekday_cn(self, date: datetime) -> str:
        """获取中文星期"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[date.weekday()]
    
    def create_entry(self, content: str, date: datetime = None, attachments: list = None) -> Path:
        """创建记录"""
        if date is None:
            date = datetime.now()
        
        day_dir = self.get_day_dir(date)
        day_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建附件目录
        if attachments:
            attachment_dir = self.get_attachment_dir(date)
            attachment_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理附件
        attachment_refs = []
        if attachments:
            for attach_path in attachments:
                attach_file = Path(attach_path)
                if not attach_file.exists():
                    print(f"警告: 附件不存在: {attach_path}")
                    continue
                
                # 生成附件名: YYYYMMDD_HHMMSS_UUID.类型
                uuid_str = uuid.uuid4().hex[:8]
                ext = attach_file.suffix or '.bin'
                new_name = f"{date.strftime('%Y%m%d_%H%M%S')}_{uuid_str}{ext}"
                new_path = attachment_dir / new_name
                
                # 复制附件
                shutil.copy2(attach_file, new_path)
                attachment_refs.append(f"\n\n[[attachment/{new_name}]]")
        
        # 创建记录文件
        entry_file = day_dir / self.get_entry_filename(date)
        full_content = content + ''.join(attachment_refs)
        entry_file.write_text(full_content, encoding='utf-8')
        
        # 更新当日索引
        self.update_index(date)
        
        return entry_file
    
    def update_index(self, date: datetime):
        """更新当日索引"""
        day_dir = self.get_day_dir(date)
        index_file = day_dir / self.get_index_filename(date)
        
        # 收集当日所有记录
        entries = sorted([
            f.stem for f in day_dir.glob('*.md')
            if f != index_file and not f.name.startswith('.')
        ])
        
        # 生成索引内容
        weekday = self.get_weekday_cn(date)
        lines = [f"# {date.strftime('%Y-%m-%d')} {weekday}\n"]
        
        for entry in entries:
            lines.append("\n---\n")
            lines.append(f"\n![[{entry}]]\n")
        
        index_file.write_text(''.join(lines), encoding='utf-8')
    
    def edit_entry(self, entry_id: str, content: str = None, attachments: list = None) -> bool:
        """编辑记录"""
        # 解析 entry_id (YYYYMMDD_HHMMSS)
        try:
            date = datetime.strptime(entry_id, '%Y%m%d_%H%M%S')
        except ValueError:
            print(f"无效的记录 ID: {entry_id}")
            return False
        
        day_dir = self.get_day_dir(date)
        entry_file = day_dir / f"{entry_id}.md"
        
        if not entry_file.exists():
            print(f"记录不存在: {entry_id}")
            return False
        
        # 读取现有内容
        existing = entry_file.read_text(encoding='utf-8')
        
        # 更新内容
        if content is not None:
            # 保留附件引用，只更新正文
            lines = existing.split('\n')
            # 找到第一个附件引用之前的内容作为正文
            content_lines = []
            attachment_lines = []
            in_attachment = False
            for line in lines:
                if line.startswith('[[attachment/'):
                    in_attachment = True
                if in_attachment:
                    attachment_lines.append(line)
                else:
                    content_lines.append(line)
            
            # 合并新内容和附件引用
            new_content = content.rstrip()
            if attachment_lines:
                new_content += '\n\n' + '\n'.join(attachment_lines)
            entry_file.write_text(new_content, encoding='utf-8')
        
        # 添加新附件
        if attachments:
            attachment_dir = self.get_attachment_dir(date)
            attachment_dir.mkdir(parents=True, exist_ok=True)
            
            existing = entry_file.read_text(encoding='utf-8')
            
            for attach_path in attachments:
                attach_file = Path(attach_path)
                if not attach_file.exists():
                    print(f"警告: 附件不存在: {attach_path}")
                    continue
                
                uuid_str = uuid.uuid4().hex[:8]
                ext = attach_file.suffix or '.bin'
                new_name = f"{entry_id}_{uuid_str}{ext}"
                new_path = attachment_dir / new_name
                
                shutil.copy2(attach_file, new_path)
                existing += f"\n\n[[attachment/{new_name}]]"
            
            entry_file.write_text(existing, encoding='utf-8')
        
        return True
    
    def delete_entry(self, entry_id: str) -> bool:
        """删除记录"""
        try:
            date = datetime.strptime(entry_id, '%Y%m%d_%H%M%S')
        except ValueError:
            print(f"无效的记录 ID: {entry_id}")
            return False
        
        day_dir = self.get_day_dir(date)
        entry_file = day_dir / f"{entry_id}.md"
        
        if not entry_file.exists():
            print(f"记录不存在: {entry_id}")
            return False
        
        # 删除记录文件
        entry_file.unlink()
        
        # 删除相关附件（匹配 entry_id 前缀）
        attachment_dir = self.get_attachment_dir(date)
        if attachment_dir.exists():
            for attach in attachment_dir.glob(f"{entry_id}_*"):
                attach.unlink()
        
        # 更新索引
        self.update_index(date)
        
        return True
    
    def list_entries(self, date_str: str = None) -> list:
        """列出记录"""
        if date_str == 'today':
            date = datetime.now()
        elif date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                print(f"无效的日期格式: {date_str}")
                return []
        else:
            # 列出所有记录
            entries = []
            for year_dir in self.raw_path.glob('*'):
                if not year_dir.is_dir() or not year_dir.name.isdigit():
                    continue
                for day_dir in year_dir.glob('*'):
                    if not day_dir.is_dir() or not day_dir.name.isdigit():
                        continue
                    for entry_file in day_dir.glob('*.md'):
                        if entry_file.stem.isdigit():  # 索引文件
                            continue
                        entries.append({
                            'file': entry_file.stem,
                            'path': entry_file,
                            'date': self.parse_entry_id(entry_file.name)
                        })
            return sorted(entries, key=lambda x: x['date'], reverse=True)
        
        # 列出指定日期
        day_dir = self.get_day_dir(date)
        if not day_dir.exists():
            return []
        
        entries = []
        for entry_file in day_dir.glob('*.md'):
            if entry_file.stem.isdigit():  # 索引文件
                continue
            entries.append({
                'file': entry_file.stem,
                'path': entry_file,
                'date': self.parse_entry_id(entry_file.name)
            })
        
        return sorted(entries, key=lambda x: x['date'])
    
    def show_entry(self, entry_id: str) -> Optional[str]:
        """查看单条记录"""
        try:
            date = datetime.strptime(entry_id, '%Y%m%d_%H%M%S')
        except ValueError:
            return None
        
        day_dir = self.get_day_dir(date)
        entry_file = day_dir / f"{entry_id}.md"
        
        if not entry_file.exists():
            return None
        
        return entry_file.read_text(encoding='utf-8')


# ============================================================================
# 备份管理
# ============================================================================

class BackupManager:
    """备份管理器"""
    
    def __init__(self, config: dict, raw_path: Path):
        self.config = config.get('backup', {})
        self.raw_path = raw_path
        self.tool = self.config.get('tool', 'restic')
        self.repo_path = Path(self.config.get('repo_path', './backup-repo'))
    
    def backup(self):
        """执行备份"""
        if self.tool == 'restic':
            self._restic_backup()
        else:
            print(f"不支持的备份工具: {self.tool}")
    
    def list_snapshots(self):
        """列出备份快照"""
        if self.tool == 'restic':
            result = subprocess.run(
                ['restic', 'snapshots', '--repo', str(self.repo_path)],
                capture_output=True,
                text=True
            )
            print(result.stdout if result.stdout else result.stderr)
    
    def restore(self, snapshot: str, target: Path):
        """恢复备份"""
        if self.tool == 'restic':
            result = subprocess.run(
                ['restic', 'restore', '--repo', str(self.repo_path), snapshot, '--target', str(target)],
                capture_output=True,
                text=True
            )
            print(result.stdout if result.stdout else result.stderr)
    
    def _restic_backup(self):
        """Restic 备份"""
        # 检查 restic 是否安装
        if not shutil.which('restic'):
            print("restic 未安装，请先安装: brew install restic")
            return
        
        # 检查仓库是否初始化
        if not self.repo_path.exists():
            print(f"备份仓库不存在，请先初始化: restic init --repo {self.repo_path}")
            return
        
        # 执行备份
        print(f"正在备份: {self.raw_path} -> {self.repo_path}")
        result = subprocess.run(
            ['restic', 'backup', '--repo', str(self.repo_path), str(self.raw_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("备份成功")
            print(result.stdout)
        else:
            print(f"备份失败: {result.stderr}")


# ============================================================================
# 初始化系统
# ============================================================================

def init_system(config: ConfigManager, git: GitManager):
    """初始化系统"""
    raw_path = config.get_raw_path()
    
    # 检查是否已初始化
    if raw_path.exists() and git.is_initialized():
        print(f"系统已初始化: {raw_path}")
        return
    
    # 询问用户 raw 库位置
    print("\n欢迎使用录入系统！")
    print(f"请指定 raw 库存放位置（默认: {config.config.get('raw_path')}）:")
    
    try:
        user_input = input("> ").strip()
    except EOFError:
        user_input = ""
    
    if user_input:
        config.update('raw-path', user_input)
        raw_path = config.get_raw_path()
    
    # 创建目录
    raw_path.mkdir(parents=True, exist_ok=True)
    print(f"已创建 raw 库: {raw_path}")
    
    # 初始化 Git
    git.init()
    print("已完成 Git 初始化")
    
    # 保存配置
    config.save()
    print(f"已创建配置文件: {config.config_file}")


# ============================================================================
# 主入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='个人信息录入系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # init 命令
    subparsers.add_parser('init', help='初始化系统')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加记录')
    add_parser.add_argument('content', help='记录内容')
    add_parser.add_argument('--attach', action='append', help='附件路径（可多次指定）')
    
    # edit 命令
    edit_parser = subparsers.add_parser('edit', help='编辑记录')
    edit_parser.add_argument('entry_id', help='记录 ID (YYYYMMDD_HHMMSS)')
    edit_parser.add_argument('--content', help='新内容')
    edit_parser.add_argument('--attach', action='append', help='添加附件（可多次指定）')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除记录')
    delete_parser.add_argument('entry_id', help='记录 ID (YYYYMMDD_HHMMSS)')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='查看记录列表')
    list_parser.add_argument('date', nargs='?', help='日期 (YYYY-MM-DD 或 today)')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='查看单条记录')
    show_parser.add_argument('entry_id', help='记录 ID (YYYYMMDD_HHMMSS)')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--raw-path', help='更新 raw 库路径')
    config_parser.add_argument('--git-remote', help='设置 Git 远程仓库地址')
    config_parser.add_argument('--git-auto-commit', help='设置自动提交 (true/false)')
    config_parser.add_argument('--git-auto-push', help='设置自动推送 (true/false)')
    
    # git-push 命令
    subparsers.add_parser('git-push', help='推送到远程仓库')
    
    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='加密备份')
    backup_parser.add_argument('--list', action='store_true', help='列出备份快照')
    backup_parser.add_argument('--restore', help='恢复快照 (latest 或快照 ID)')
    backup_parser.add_argument('--target', help='恢复目标路径')
    
    args = parser.parse_args()
    
    # 确定 skill 目录
    skill_dir = Path(__file__).parent.resolve()
    
    # 初始化管理器
    config = ConfigManager(skill_dir)
    
    # 检查是否需要初始化
    if args.command != 'init' and not config.get_raw_path().exists():
        print(f"raw 库不存在: {config.get_raw_path()}")
        print("请先运行: python index.py init")
        return
    
    raw_path = config.get_raw_path()
    git = GitManager(raw_path)
    entry = EntryManager(raw_path)
    backup = BackupManager(config.config, raw_path)
    
    # 执行命令
    if args.command == 'init':
        init_system(config, git)
    
    elif args.command == 'add':
        entry_file = entry.create_entry(args.content, attachments=args.attach)
        print(f"✓ 已创建记录: {entry_file.stem}")
        
        if config.config.get('git_auto_commit'):
            git.commit(f"add: {entry_file.stem}")
    
    elif args.command == 'edit':
        if entry.edit_entry(args.entry_id, content=args.content, attachments=args.attach):
            print(f"✓ 已更新记录: {args.entry_id}")
            
            if config.config.get('git_auto_commit'):
                git.commit(f"edit: {args.entry_id}")
    
    elif args.command == 'delete':
        if entry.delete_entry(args.entry_id):
            print(f"✓ 已删除记录: {args.entry_id}")
            
            if config.config.get('git_auto_commit'):
                git.commit(f"delete: {args.entry_id}")
    
    elif args.command == 'list':
        entries = entry.list_entries(args.date)
        if not entries:
            print("无记录")
        else:
            print(f"共 {len(entries)} 条记录:")
            for e in entries:
                content_preview = e['path'].read_text(encoding='utf-8')[:50].replace('\n', ' ')
                print(f"  {e['file']}: {content_preview}...")
    
    elif args.command == 'show':
        content = entry.show_entry(args.entry_id)
        if content:
            print(f"--- {args.entry_id} ---")
            print(content)
        else:
            print(f"记录不存在: {args.entry_id}")
    
    elif args.command == 'config':
        if args.raw_path:
            config.update('raw-path', args.raw_path)
            print(f"✓ 已更新 raw 库路径: {args.raw_path}")
        elif args.git_remote:
            config.update('git-remote', args.git_remote)
            git.set_remote(args.git_remote)
            print(f"✓ 已设置远程仓库: {args.git_remote}")
        elif args.git_auto_commit:
            config.update('git-auto-commit', args.git_auto_commit)
            print(f"✓ 已设置自动提交: {args.git_auto_commit}")
        elif args.git_auto_push:
            config.update('git-auto-push', args.git_auto_push)
            print(f"✓ 已设置自动推送: {args.git_auto_push}")
        else:
            # 显示当前配置
            print("当前配置:")
            print(yaml.dump(config.config, allow_unicode=True, default_flow_style=False))
    
    elif args.command == 'git-push':
        if not config.config.get('git_remote_url'):
            print("未配置远程仓库，请先运行: config --git-remote <url>")
            return
        git.push()
    
    elif args.command == 'backup':
        if args.list:
            backup.list_snapshots()
        elif args.restore and args.target:
            backup.restore(args.restore, Path(args.target))
        else:
            backup.backup()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()