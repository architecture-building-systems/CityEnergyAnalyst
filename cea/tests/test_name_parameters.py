"""Name parameters become folder names, so a non-name value must be refused, not stringified.

The dashboard can end up sending a list where a single name is expected (a multi-choice
`what-if-name` of one tool carried over to the free-text `what-if-name` of another).
`str(['baseline'])` is a perfectly valid folder name, so nothing downstream would notice.
"""

import pytest

import cea.config


@pytest.fixture
def config():
    return cea.config.Configuration(cea.config.DEFAULT_CONFIG)


@pytest.mark.parametrize('section, name', [('final-energy', 'what-if-name'), ('network-layout', 'network-name')])
def test_a_list_is_not_a_name(config, section, name):
    parameter = config.sections[section].parameters[name]
    with pytest.raises(ValueError, match='single name'):
        parameter.encode(['baseline'])


@pytest.mark.parametrize('section, name', [('final-energy', 'what-if-name'), ('network-layout', 'network-name')])
def test_a_plain_name_is_still_accepted(config, section, name):
    parameter = config.sections[section].parameters[name]
    assert parameter.encode('baseline') == 'baseline'
    # multipart form values are JSON-decoded by the job server, so a name typed as "4" arrives as 4
    assert parameter.encode(4) == '4'
