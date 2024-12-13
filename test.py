import pytest
from io import StringIO
from config_converter import parse_config, convert_to_yaml, remove_comments, substitute_constants, replace_strings

@pytest.fixture
def example_config():
    return """* Комментарий
    set SERVER_PORT = 80;
    set SERVER_NAME = "example.com";

    /+ Многострочный комментарий +/
    section server {
        listen = 80;
        server_name = example.com;
        root = "/var/www/html";
        location = "/";
        index = "index.html";
    }

    [
        server_port => !{SERVER_PORT},
        server_name => !{SERVER_NAME},
        root_directory => q(/var/www/html)
    ]"""

@pytest.fixture
def expected_output():
    return {
        "constants": {"SERVER_NAME": "example.com", "SERVER_PORT": "80"},
        "sections": [{
            "name": "server",
            "content": """listen = 80;
            server_name = example.com;
            root = "/var/www/html";
            location = "/";
            index = "index.html";"""
        }],
        "dictionaries": [{
            "server_port": "80",
            "server_name": "example.com",
            "root_directory": "/var/www/html"
        }]
    }

def test_remove_comments():
    input_text = """* Comment
    set VALUE = 42;/+ Multi-line
    comment +/section example {}"""
    expected = "set VALUE = 42;section example {}"
    assert remove_comments(input_text) == expected

def test_parse_config(example_config, expected_output):
    constants, sections, dictionaries = parse_config(example_config)
    assert constants == expected_output["constants"]
    assert sections == expected_output["sections"]
    assert dictionaries == expected_output["dictionaries"]

def test_convert_to_yaml(example_config, expected_output):
    constants, sections, dictionaries = parse_config(example_config)
    yaml_output = convert_to_yaml(constants, sections, dictionaries)
    expected_yaml = """constants:
  SERVER_NAME: example.com
  SERVER_PORT: '80'
dictionaries:
- root_directory: /var/www/html
  server_name: example.com
  server_port: '80'
sections:
- content: |-
    listen = 80;
    server_name = example.com;
    root = "/var/www/html";
    location = "/";
    index = "index.html";
  name: server
"""
    assert yaml_output == expected_yaml

def test_invalid_config():
    input_text = "section missing_end { key = value;"
    with pytest.raises(Exception):
        parse_config(input_text)

def test_constants_in_dictionaries():
    input_text = """set KEY = value;
    [
        key1 => !{KEY},
        key2 => q(string_value)
    ]"""
    constants, sections, dictionaries = parse_config(input_text)
    assert dictionaries[0] == {
        "key1": "value",
        "key2": "string_value"
    }

def test_replace_strings():
    input_text = "set GREETING = q(Hello, world!);"
    constants, sections, dictionaries = parse_config(input_text)
    assert constants["GREETING"] == "Hello, world!"
