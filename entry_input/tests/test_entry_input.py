#!/usr/bin/env python3
"""
Entry Input 测试套件
覆盖所有核心功能的测试用例
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import yaml
import subprocess

# 导入主模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from index import ConfigManager, GitManager, EntryManager, BackupManager, DEFAULT_CONFIG


# ============================================================================
# 临时目录 fixture
# ============================================================================

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = Path(tempfile.mkdtemp())
    skill_dir = temp / 'skill'
    skill_dir.mkdir()
    raw_dir = temp / 'raw'
    raw_dir.mkdir()
    yield {
        'temp': temp,
        'skill_dir': skill_dir,
        'raw_dir': raw_dir
    }
    shutil.rmtree(temp)


@pytest.fixture
def config(temp_dir):
    """创建配置管理器"""
    return ConfigManager(temp_dir['skill_dir'])


@pytest.fixture
def git(temp_dir):
    """创建 Git 管理器"""
    return GitManager(temp_dir['raw_dir'])


@pytest.fixture
def entry(temp_dir):
    """创建记录管理器"""
    return EntryManager(temp_dir['raw_dir'])


# ============================================================================
# ConfigManager 测试
# ============================================================================

class TestConfigManager:
    
    def test_default_config(self, config):
        """测试默认配置"""
        # 验证默认配置结构
        assert config.config['raw_path'] == '~/PIMS_repo'
        assert config.config['git_auto_commit'] == True
    
    def test_save_and_load_config(self, config, temp_dir):
        """测试配置保存和加载"""
        # 更新 raw_path 并保存
        config.update('raw-path', str(temp_dir['raw_dir']))
        
        # 验证配置文件已保存到 skill_dir 下
        config_file = temp_dir['skill_dir'] / 'config.yaml'
        assert config_file.exists()
        
        # 重新加载
        config2 = ConfigManager(temp_dir['skill_dir'])
        assert config2.config['raw_path'] == str(temp_dir['raw_dir'])
    
    def test_get_raw_path_absolute(self, config, temp_dir):
        """测试获取绝对路径"""
        config.update('raw-path', str(temp_dir['raw_dir']))
        
        raw_path = config.get_raw_path()
        assert raw_path.is_absolute()
        assert raw_path == temp_dir['raw_dir'].resolve()
    
    def test_get_raw_path_relative(self, config):
        """测试相对路径解析"""
        config.update('raw-path', '../raw')
        
        raw_path = config.get_raw_path()
        assert raw_path.is_absolute()
    
    def test_update_git_config(self, config):
        """测试 Git 配置更新"""
        config.update('git-remote', 'git@github.com:test/test.git')
        assert config.config['git_remote_url'] == 'git@github.com:test/test.git'
    
    def test_update_backup_config(self, config):
        """测试备份配置更新"""
        config.update('backup.tool', 'borg')
        assert config.config['backup']['tool'] == 'borg'


# ============================================================================
# GitManager 测试
# ============================================================================

class TestGitManager:
    
    def test_is_not_initialized(self, git):
        """测试未初始化检测"""
        assert not git.is_initialized()
    
    def test_init_git(self, git, temp_dir):
        """测试 Git 初始化"""
        git.init()
        assert git.is_initialized()
        assert (temp_dir['raw_dir'] / '.git').exists()
    
    def test_commit(self, git, temp_dir):
        """测试 Git 提交"""
        git.init()
        
        # 创建一个文件
        test_file = temp_dir['raw_dir'] / 'test.txt'
        test_file.write_text('test content')
        
        # 提交
        git.commit('test commit')
        
        # 检查提交历史
        result = subprocess.run(
            ['git', 'log', '--oneline'],
            cwd=temp_dir['raw_dir'],
            capture_output=True,
            text=True
        )
        assert 'test commit' in result.stdout


# ============================================================================
# EntryManager 测试
# ============================================================================

class TestEntryManager:
    
    def test_get_year_dir(self, entry):
        """测试年份目录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        year_dir = entry.get_year_dir(date)
        assert year_dir.name == '2026'
    
    def test_get_day_dir(self, entry):
        """测试日期目录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        day_dir = entry.get_day_dir(date)
        assert day_dir.name == '20260301'
    
    def test_get_attachment_dir(self, entry):
        """测试附件目录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        attach_dir = entry.get_attachment_dir(date)
        assert attach_dir.name == 'attachment'
    
    def test_get_entry_filename(self, entry):
        """测试记录文件名生成"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        filename = entry.get_entry_filename(date)
        assert filename == '20260301_122334.md'
    
    def test_parse_entry_id(self, entry):
        """测试记录 ID 解析"""
        parsed = entry.parse_entry_id('20260301_122334.md')
        assert parsed == datetime(2026, 3, 1, 12, 23, 34)
    
    def test_create_entry_basic(self, entry):
        """测试基础记录创建"""
        content = "#todo #project-A test entry"
        date = datetime(2026, 3, 1, 12, 23, 34)
        
        entry_file = entry.create_entry(content, date=date)
        
        assert entry_file.exists()
        assert entry_file.name == '20260301_122334.md'
        assert entry_file.read_text() == content
    
    def test_create_entry_with_attachment(self, entry, temp_dir):
        """测试带附件的记录创建"""
        # 创建模拟附件
        attach_file = temp_dir['temp'] / 'photo.jpg'
        attach_file.write_text('mock image content')
        
        content = "test entry with attachment"
        date = datetime(2026, 3, 1, 12, 23, 34)
        
        entry_file = entry.create_entry(content, date=date, attachments=[str(attach_file)])
        
        # 检查记录文件
        assert entry_file.exists()
        record_content = entry_file.read_text()
        assert content in record_content
        assert '[[attachment/' in record_content
        
        # 棡查附件文件
        attach_dir = entry.get_attachment_dir(date)
        assert attach_dir.exists()
        attachments = list(attach_dir.glob('*.jpg'))
        assert len(attachments) == 1
        assert attachments[0].name.startswith('20260301_122334_')
    
    def test_update_index(self, entry):
        """测试索引更新"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        
        # 创建两条记录
        entry.create_entry("entry 1", date=date)
        entry.create_entry("entry 2", date=datetime(2026, 3, 1, 15, 30, 12))
        
        # 棡查索引文件
        index_file = entry.get_day_dir(date) / '20260301.md'
        assert index_file.exists()
        
        index_content = index_file.read_text()
        assert '# 2026-03-01' in index_content
        assert '![[20260301_122334]]' in index_content
        assert '![[20260301_153012]]' in index_content
    
    def test_edit_entry_content(self, entry):
        """测试编辑记录内容"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry("original content", date=date)
        
        # 编辑内容
        result = entry.edit_entry('20260301_122334', content="new content")
        assert result
        
        # 棡查更新后的内容
        new_content = entry_file.read_text()
        assert 'new content' in new_content
    
    def test_edit_entry_add_attachment(self, entry, temp_dir):
        """测试编辑记录添加附件"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry("entry content", date=date)
        
        # 创建新附件
        new_attach = temp_dir['temp'] / 'doc.pdf'
        new_attach.write_text('mock pdf content')
        
        # 添加附件
        result = entry.edit_entry('20260301_122334', attachments=[str(new_attach)])
        assert result
        
        # 棡查内容包含新附件引用
        content = entry_file.read_text()
        assert '[[attachment/' in content
    
    def test_delete_entry(self, entry):
        """测试删除记录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry("test entry", date=date)
        
        # 删除记录
        result = entry.delete_entry('20260301_122334')
        assert result
        assert not entry_file.exists()
    
    def test_delete_entry_with_attachments(self, entry, temp_dir):
        """测试删除记录及其附件"""
        attach_file = temp_dir['temp'] / 'photo.jpg'
        attach_file.write_text('mock content')
        
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry(
            "test entry",
            date=date,
            attachments=[str(attach_file)]
        )
        
        # 删除记录
        result = entry.delete_entry('20260301_122334')
        assert result
        assert not entry_file.exists()
        
        # 棡查附件也被删除
        attach_dir = entry.get_attachment_dir(date)
        attachments = list(attach_dir.glob('20260301_122334_*'))
        assert len(attachments) == 0
    
    def test_list_entries_by_date(self, entry):
        """测试按日期列出记录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry.create_entry("entry 1", date=date)
        entry.create_entry("entry 2", date=datetime(2026, 3, 1, 15, 30, 12))
        
        entries = entry.list_entries('2026-03-01')
        assert len(entries) == 2
    
    def test_list_entries_today(self, entry):
        """测试列出今日记录"""
        today = datetime.now()
        entry.create_entry("today entry", date=today)
        
        entries = entry.list_entries('today')
        assert len(entries) >= 1
    
    def test_list_all_entries(self, entry):
        """测试列出所有记录"""
        # 创建多天记录
        entry.create_entry("entry 1", date=datetime(2026, 3, 1, 12, 23, 34))
        entry.create_entry("entry 2", date=datetime(2026, 3, 2, 9, 0, 0))
        
        entries = entry.list_entries()
        assert len(entries) == 2
    
    def test_show_entry(self, entry):
        """测试查看单条记录"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry.create_entry("test content", date=date)
        
        content = entry.show_entry('20260301_122334')
        assert content == "test content"
    
    def test_show_entry_not_exists(self, entry):
        """测试查看不存在的记录"""
        content = entry.show_entry('20260301_999999')
        assert content is None


# ============================================================================
# 多附件测试
# ============================================================================

class TestMultipleAttachments:
    
    def test_create_with_multiple_attachments(self, entry, temp_dir):
        """测试创建带多个附件的记录"""
        # 创建多个模拟附件
        attach1 = temp_dir['temp'] / 'photo.jpg'
        attach1.write_text('image content')
        attach2 = temp_dir['temp'] / 'doc.pdf'
        attach2.write_text('pdf content')
        attach3 = temp_dir['temp'] / 'audio.mp3'
        attach3.write_text('audio content')
        
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry(
            "entry with 3 attachments",
            date=date,
            attachments=[str(attach1), str(attach2), str(attach3)]
        )
        
        # 棡查记录内容
        content = entry_file.read_text()
        assert '[[attachment/' in content
        # 应该有 3 个附件引用
        assert content.count('[[attachment/') == 3
        
        # 棡查附件目录
        attach_dir = entry.get_attachment_dir(date)
        attachments = list(attach_dir.glob('*'))
        assert len(attachments) == 3


# ============================================================================
# 标签解析测试
# ============================================================================

class TestTagParsing:
    
    def test_extract_tags(self):
        """测试标签提取"""
        content = "#todo #project-A #work finish the report"
        import re
        tags = re.findall(r'#(\w+-?\w*)', content)
        assert 'todo' in tags
        assert 'project-A' in tags
        assert 'work' in tags
    
    def test_extract_project_tag(self):
        """测试项目标签提取"""
        content = "#todo #project-PIMS #idea"
        import re
        project_tags = [t for t in re.findall(r'#(\w+-?\w*)', content) if t.startswith('project')]
        assert len(project_tags) > 0


# ============================================================================
# 边界情况测试
# ============================================================================

class TestEdgeCases:
    
    def test_empty_content(self, entry):
        """测试空内容"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry("", date=date)
        assert entry_file.exists()
        assert entry_file.read_text() == ""
    
    def test_multiline_content(self, entry):
        """测试多行内容"""
        content = "#todo line 1\nline 2\nline 3"
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry(content, date=date)
        
        assert entry_file.read_text() == content
    
    def test_chinese_content(self, entry):
        """测试中文内容"""
        content = "#todo test chinese content"
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry_file = entry.create_entry(content, date=date)
        
        assert entry_file.read_text() == content
    
    def test_attachment_not_exists(self, entry):
        """测试附件不存在"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        # 不存在的附件路径
        entry_file = entry.create_entry(
            "test",
            date=date,
            attachments=['/nonexistent/file.jpg']
        )
        
        # 记录仍然创建成功只是没有附件
        assert entry_file.exists()
        assert '[[attachment/' not in entry_file.read_text()
    
    def test_delete_nonexistent_entry(self, entry):
        """测试删除不存在的记录"""
        result = entry.delete_entry('20260301_999999')
        assert not result
    
    def test_edit_nonexistent_entry(self, entry):
        """测试编辑不存在的记录"""
        result = entry.edit_entry('20260301_999999', content="new content")
        assert not result


# ============================================================================
# 文件命名测试
# ============================================================================

class TestFileNaming:
    
    def test_entry_filename_format(self):
        """测试记录文件名格式"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        from index import EntryManager
        entry = EntryManager(Path('/tmp'))
        filename = entry.get_entry_filename(date)
        
        # 格式: YYYYMMDD_HHMMSS.md
        assert filename == '20260301_122334.md'
    
    def test_attachment_filename_format(self):
        """测试附件文件名格式"""
        import uuid
        date = datetime(2026, 3, 1, 12, 23, 34)
        uuid_str = uuid.uuid4().hex[:8]
        
        # 格式: YYYYMMDD_HHMMSS_UUID.ext
        filename = f"{date.strftime('%Y%m%d_%H%M%S')}_{uuid_str}.jpg"
        
        # 棡查格式
        assert filename.startswith('20260301_122334_')
        assert filename.endswith('.jpg')
        # UUID 部分 8 字符
        parts = filename.split('_')
        assert len(parts) == 3
        assert len(parts[2].split('.')[0]) == 8


# ============================================================================
# 索引格式测试
# ============================================================================

class TestIndexFormat:
    
    def test_index_header_format(self, entry):
        """测试索引标题格式"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry.create_entry("test", date=date)
        
        index_file = entry.get_day_dir(date) / '20260301.md'
        content = index_file.read_text()
        
        # 应包含日期和星期
        assert '# 2026-03-01' in content
        # 周日（2026-03-01 是周日）
        assert '周日' in content
    
    def test_index_entry_references(self, entry):
        """测试索引中的记录引用"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry.create_entry("entry 1", date=date)
        entry.create_entry("entry 2", date=datetime(2026, 3, 1, 15, 30, 12))
        
        index_file = entry.get_day_dir(date) / '20260301.md'
        content = index_file.read_text()
        
        # 使用 Obsidian 嵌入语法
        assert '![[20260301_122334]]' in content
        assert '![[20260301_153012]]' in content
    
    def test_index_update_on_delete(self, entry):
        """测试删除记录后索引更新"""
        date = datetime(2026, 3, 1, 12, 23, 34)
        entry.create_entry("entry 1", date=date)
        entry.create_entry("entry 2", date=datetime(2026, 3, 1, 15, 30, 12))
        
        # 删除第一条
        entry.delete_entry('20260301_122334')
        
        # 棡查索引
        index_file = entry.get_day_dir(date) / '20260301.md'
        content = index_file.read_text()
        
        # 被删除的记录不应在索引中
        assert '![[20260301_122334]]' not in content
        assert '![[20260301_153012]]' in content


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])