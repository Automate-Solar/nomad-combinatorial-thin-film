from nomad_combinatorial_thin_film.parser.experiment_plan_parser import (
    parse_experiment_plan_document,
)

EXPECTED_CONFIG_ID = 19
EXPECTED_POWER_W = 41
EXPECTED_FIGURE_COUNT = 2


def test_parse_experiment_plan_and_profiles():
    text = """
    { sample_id: 'sample-1', expt_plan_id: 'plan-1', sputter_process_id: 'process-1',
      start_datetime: '2026-09-07T10:31:03', multilayers: NumberInt('0'),
      system_state: { system_config_id: NumberInt('19'), target_kWh: [Double('2.5')],
        'sputter gas': 'Ar', qcm_lifetimes: ['10.0'], 'base_pressure [Torr]': '2.0E-7' } }
    { type: 'ZnCu', expt_id: 'exp-1', sputter_process_id: 'process-1',
      target_composition: { Zn: NumberInt('4'), Cu: NumberInt('1') },
      recipe: { 'source_1_set_power_[W]': NumberInt('41'),
        'set_pressure_[mTorr]': NumberInt('5'), 'dwell_time_[s]': NumberInt('137'),
        flux_model: 'cosine_old', Zn_fract: Double('0.8'), Cu_fract: Double('0.2') },
      x_profiles_pred: { X: [Double('-1'), Double('0'), Double('1')],
        Y: [Double('0'), Double('0'), Double('0')],
        'Zn_AD_(cosine_old)': [Double('10'), Double('20'), Double('30')],
        'Zn_AD_error_(cosine_old)': [Double('1'), Double('1'), Double('1')],
        'Cu_AD_(cosine_old)': [Double('3'), Double('4'), Double('5')],
        'Cu_AD_error_(cosine_old)': [Double('0.2'), Double('0.2'), Double('0.2')],
        'Zn_fract_(cosine_old)': [Double('0.8'), Double('0.83'), Double('0.86')],
        'Cu_fract_(cosine_old)': [Double('0.2'), Double('0.17'), Double('0.14')] } }
    """
    result = parse_experiment_plan_document(text)
    assert result.sample_id == 'sample-1'
    assert result.system_state.system_config_id == EXPECTED_CONFIG_ID
    assert result.recipe.source_1_set_power_w == EXPECTED_POWER_W
    assert list(result.x_profile.x) == [-1, 0, 1]
    assert len(result.figures) == EXPECTED_FIGURE_COUNT
    #assert result.figures[0].figure['data'][0]['name'] == 'Zn'


def test_missing_required_documents_is_reported():
    try:
        parse_experiment_plan_document("{ sample_id: 'only-plan' }")
    except ValueError as error:
        assert 'experiment document' in str(error)
    else:
        raise AssertionError(
            'Expected a ValueError when no recipe document is supplied'
        )
