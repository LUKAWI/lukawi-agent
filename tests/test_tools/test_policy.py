import pytest
from lukawi.tools.policy import ToolPolicy, PolicyContext
from lukawi.tools.base import ToolDefinition
from lukawi.config.models import ToolPolicyConfig, ToolProfileConfig


@pytest.fixture
def default_config():
    return ToolPolicyConfig(
        default_profile="default",
        profiles={
            "default": ToolProfileConfig(
                allowed_tools=["*"],
                denied_tools=[]
            ),
            "restricted": ToolProfileConfig(
                allowed_tools=["web_fetch", "read_file", "list_dir"],
                denied_tools=["exec_command", "write_file"]
            ),
            "safe": ToolProfileConfig(
                allowed_tools=["web_fetch", "read_file"],
                denied_tools=["*"]
            )
        }
    )


@pytest.fixture
def policy(default_config):
    return ToolPolicy(default_config)


@pytest.fixture
def tools():
    return [
        ToolDefinition(name="web_fetch", description="Fetch URL"),
        ToolDefinition(name="read_file", description="Read file"),
        ToolDefinition(name="write_file", description="Write file"),
        ToolDefinition(name="exec_command", description="Execute command"),
        ToolDefinition(name="list_dir", description="List directory"),
    ]


@pytest.fixture
def default_context():
    return PolicyContext(profile="default")


@pytest.fixture
def restricted_context():
    return PolicyContext(profile="restricted")


class TestToolPolicy:
    def test_default_allows_all(self, policy, tools, default_context):
        filtered = policy.filter_tools(tools, default_context)
        assert len(filtered) == 5
    
    def test_restricted_profile(self, policy, tools, restricted_context):
        filtered = policy.filter_tools(tools, restricted_context)
        names = [t.name for t in filtered]
        
        assert "web_fetch" in names
        assert "read_file" in names
        assert "list_dir" in names
        assert "exec_command" not in names
        assert "write_file" not in names
    
    def test_is_allowed_default(self, policy, default_context):
        assert policy.is_allowed("web_fetch", default_context)
        assert policy.is_allowed("exec_command", default_context)
    
    def test_is_allowed_restricted(self, policy, restricted_context):
        assert policy.is_allowed("web_fetch", restricted_context)
        assert not policy.is_allowed("exec_command", restricted_context)
        assert not policy.is_allowed("write_file", restricted_context)
    
    def test_deny_overrides_allow(self, policy, default_config):
        default_config.profiles["test"] = ToolProfileConfig(
            allowed_tools=["web_fetch"],
            denied_tools=["web_fetch"]
        )
        
        test_policy = ToolPolicy(default_config)
        context = PolicyContext(profile="test")
        
        # Deny should win
        assert not test_policy.is_allowed("web_fetch", context)
    
    def test_unknown_profile_uses_default(self, policy, tools):
        context = PolicyContext(profile="nonexistent")
        filtered = policy.filter_tools(tools, context)
        assert len(filtered) == 5
    
    def test_wildcard_patterns(self, default_config):
        default_config.profiles["wildcard"] = ToolProfileConfig(
            allowed_tools=["web_*", "read_*"],
            denied_tools=[]
        )
        
        policy = ToolPolicy(default_config)
        context = PolicyContext(profile="wildcard")
        
        assert policy.is_allowed("web_fetch", context)
        assert policy.is_allowed("read_file", context)
        assert not policy.is_allowed("write_file", context)
