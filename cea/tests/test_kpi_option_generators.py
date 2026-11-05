"""`run_generator` picks the call form from the generator's signature, once, at registration."""

import pytest

from cea.inputlocator import InputLocator
from cea.kpi import option_generators
from cea.kpi.option_generators import register, run_generator


@pytest.fixture
def locator(tmp_path):
    return InputLocator(str(tmp_path))


@pytest.fixture(autouse=True)
def isolated_generators(monkeypatch):
    monkeypatch.setattr(option_generators, "_GENERATORS", dict(option_generators._GENERATORS))


def test_a_one_argument_generator_gets_only_the_locator(locator):
    @register("one_arg")
    def one_arg(loc):
        return [{"value": "a", "label": "A"}]

    assert run_generator("one_arg", locator, {"plan_name": "p"}) == [{"value": "a", "label": "A"}]


def test_a_two_argument_generator_gets_the_parameters(locator):
    @register("two_args")
    def two_args(loc, parameters):
        return [{"value": parameters["plan_name"], "label": "x"}]

    assert run_generator("two_args", locator, {"plan_name": "p"}) == [{"value": "p", "label": "x"}]


def test_a_type_error_inside_a_generator_is_not_retried_with_another_signature(locator):
    calls = []

    @register("raises")
    def raises(loc, parameters):
        calls.append(1)
        raise TypeError("bug inside the generator")

    with pytest.raises(TypeError, match="bug inside the generator"):
        run_generator("raises", locator, {})
    assert len(calls) == 1
