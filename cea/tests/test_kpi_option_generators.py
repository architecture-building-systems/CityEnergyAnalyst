import pytest

from cea.kpi import option_generators


def _unregister(name):
    option_generators._GENERATORS.pop(name, None)
    option_generators._GENERATOR_ACCEPTS_PARAMETERS.pop(name, None)


def test_legacy_one_argument_generator_is_called_once():
    name = "test_legacy_one_argument"
    calls = []

    @option_generators.register(name)
    def generator(locator):
        calls.append(locator)
        return [{"value": "choice", "label": "Choice"}]

    locator = object()
    try:
        assert option_generators.run_generator(name, locator, {"draft": "value"}) == [
            {"value": "choice", "label": "Choice"}
        ]
        assert calls == [locator]
    finally:
        _unregister(name)


def test_two_argument_generator_receives_parameter_draft():
    name = "test_parameter_draft"
    calls = []

    @option_generators.register(name)
    def generator(_locator, parameters):
        calls.append(parameters)
        return []

    draft = {"plan_name": "DistrictPlan"}
    try:
        assert option_generators.run_generator(name, object(), draft) == []
        assert calls == [draft]
    finally:
        _unregister(name)


def test_generator_typeerror_is_not_retried_as_a_legacy_signature():
    name = "test_internal_typeerror"
    calls = []

    @option_generators.register(name)
    def generator(_locator, parameters=None):
        calls.append(parameters)
        if len(calls) == 1:
            raise TypeError("synthetic generator logic error")
        return [{"value": "unexpected", "label": "unexpected"}]

    try:
        with pytest.raises(TypeError, match="synthetic generator logic error"):
            option_generators.run_generator(name, object(), {})
        assert calls == [{}]
    finally:
        _unregister(name)
