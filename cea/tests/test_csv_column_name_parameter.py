"""CsvColumnNameParameter / SourceParameterMixin: GUI-only column-preview metadata.

`emissions:csv-carbon-intensity-column-name` is typed by hand against a CSV the user just
uploaded, with no way to see its header first (see `cea/analysis/lca/CLAUDE.md`'s "Grid
Emission Intensity Override"). `SourceParameterMixin.source_parameter` names the sibling
InputFileParameter (`grid-carbon-intensity-dataset-csv`) so the GUI can watch that field and
offer a dropdown of the file's real columns instead. This has no effect on decode()/encode()
or on the actual CSV read (`_load_grid_emission_intensity_override`) -- it is pure metadata
carried through `deconstruct_parameters` to the frontend.
"""

import cea.config
from cea.interfaces.dashboard.api.utils import deconstruct_parameters


def _get_column_name_parameter():
    config = cea.config.Configuration()
    return config, config.sections['emissions'].parameters['csv-carbon-intensity-column-name']


def test_is_csv_column_name_parameter_backed_by_string_behaviour():
    _, parameter = _get_column_name_parameter()
    assert isinstance(parameter, cea.config.CsvColumnNameParameter)
    assert isinstance(parameter, cea.config.StringParameter)
    assert isinstance(parameter, cea.config.SourceParameterMixin)


def test_source_parameter_points_at_sibling_upload_field():
    _, parameter = _get_column_name_parameter()
    assert parameter.source_parameter == 'grid-carbon-intensity-dataset-csv'


def test_decode_encode_unaffected_by_mixin():
    """The mixin only adds metadata -- value handling stays identical to StringParameter."""
    _, parameter = _get_column_name_parameter()
    assert parameter.decode('Carbon intensity') == 'Carbon intensity'
    assert parameter.encode('Carbon intensity') == 'Carbon intensity'


def test_deconstruct_parameters_exposes_source_parameter_metadata():
    config, parameter = _get_column_name_parameter()
    metadata = deconstruct_parameters(parameter, config)
    assert metadata['type'] == 'CsvColumnNameParameter'
    assert metadata['source_parameter'] == 'grid-carbon-intensity-dataset-csv'


def test_deconstruct_parameters_omits_source_parameter_for_unrelated_parameter():
    """A parameter not paired with any upload must not gain the key."""
    config = cea.config.Configuration()
    unrelated = next(
        p for p in config.sections['general'].parameters.values()
        if not isinstance(p, cea.config.SourceParameterMixin)
    )
    metadata = deconstruct_parameters(unrelated, config)
    assert 'source_parameter' not in metadata
