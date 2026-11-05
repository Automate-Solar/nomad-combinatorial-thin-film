"""Parser for Mongo-shell-style experiment_plan.txt exports."""

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

from nomad.parsing.parser import MatchingParser

from nomad_combinatorial_thin_film.plugin.experiment_plan import (
    ExperimentRecipe,
    ExperimentSystemState,
    PredictedProfile,
    SputteringExperimentPlan,
)

logger_module = logging.getLogger(__name__)


def _top_level_documents(text: str) -> list[str]:
    """Extract balanced top-level object literals while respecting quoted strings."""
    documents: list[str] = []
    start = None
    depth = 0
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == '{':
            if depth == 0:
                start = index
            depth += 1
        elif char == '}':
            depth -= 1
            if depth < 0:
                raise ValueError('Unexpected closing brace in experiment plan.')
            if depth == 0 and start is not None:
                documents.append(text[start : index + 1])
                start = None
    if depth or quote:
        raise ValueError('Incomplete object or string in experiment plan.')
    return documents


def _parse_mongo_shell_object(source: str) -> dict[str, Any]:
    """Convert Mongo shell wrappers and unquoted keys to Python literals."""
    source = re.sub(
        r"""\bObjectId\(\s*(['"])(.*?)\1\s*\)""",
        lambda match: repr(match.group(2)),
        source,
    )

    def convert_numeric(match: re.Match[str]) -> str:
        wrapper, value = match.group(1), match.group(3).strip()
        try:
            number = int(value) if wrapper == 'NumberInt' else float(value)
        except ValueError as exc:
            raise ValueError(f'Invalid {wrapper} value: {value}') from exc
        return repr(number)

    source = re.sub(
        r"""\b(NumberInt|Double)\(\s*(['"]?)([-+0-9.eE]+)\2\s*\)""",
        convert_numeric,
        source,
    )
    source = re.sub(
        r'([,{]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
        lambda match: f'{match.group(1)}{match.group(2)!r}:',
        source,
    )
    value = ast.literal_eval(source)
    if not isinstance(value, dict):
        raise ValueError('Each experiment-plan document must be an object.')
    return value


def _populate_system_state(
    plan: SputteringExperimentPlan, data: dict[str, Any]
) -> None:
    if not data:
        return
    state = ExperimentSystemState()
    state.datetime = data.get('datetime')
    if data.get('system_config_id') is not None:
        state.system_config_id = int(data['system_config_id'])
    if data.get('target_kWh') is not None:
        state.target_kWh = [float(item) for item in data['target_kWh']]
    state.sputter_gas = data.get('sputter gas')
    state.qcm_crystal_types = data.get('qcm_crystal_types')
    if data.get('qcm_lifetimes') is not None:
        state.qcm_lifetimes = [float(item) for item in data['qcm_lifetimes']]
    pressure = data.get('base_pressure [Torr]')
    if pressure is not None:
        state.base_pressure_torr = float(pressure)
    plan.system_state = state


def _populate_recipe(
    plan: SputteringExperimentPlan, document: dict[str, Any]
) -> dict[str, Any]:
    values = document.get('recipe') or {}
    recipe = ExperimentRecipe()
    recipe.experiment_type = document.get('type')
    recipe.expt_id = document.get('expt_id')
    recipe.sputter_process_id = document.get('sputter_process_id')
    recipe.cosputter_process_id = values.get('cosputter_process_id')
    target = document.get('target_composition') or {}
    for key, attribute in (
        ('Zn', 'target_composition_zn'),
        ('Cu', 'target_composition_cu'),
    ):
        if target.get(key) is not None:
            setattr(recipe, attribute, float(target[key]))
    for number in range(1, 7):
        value = values.get(f'source_{number}_set_power_[W]')
        if value is not None:
            setattr(recipe, f'source_{number}_set_power_w', float(value))
    for key, attribute in (
        ('set_pressure_[mTorr]', 'set_pressure_mtorr'),
        ('dwell_time_[s]', 'dwell_time_s'),
        ('total_rate_[10^15at/cm2s]', 'total_rate'),
        ('Zn_fract', 'zn_fraction'),
        ('Cu_fract', 'cu_fraction'),
        ('Zn_source_rate_[10^15at/cm2s]_pred', 'zn_source_rate'),
        ('Zn_source_rate_[10^15at/cm2s]_error_pred', 'zn_source_rate_error'),
        ('Cu_source_rate_[10^15at/cm2s]_pred', 'cu_source_rate'),
        ('Cu_source_rate_[10^15at/cm2s]_error_pred', 'cu_source_rate_error'),
    ):
        if values.get(key) is not None:
            setattr(recipe, attribute, float(values[key]))
    recipe.position = values.get('position')
    recipe.flux_model = values.get('flux_model')
    recipe.raw_recipe_json = json.dumps(values, ensure_ascii=False)
    plan.recipe = recipe
    return values


def _populate_profile(
    plan: SputteringExperimentPlan,
    document: dict[str, Any],
    recipe: dict[str, Any],
    source_key: str,
    attribute: str,
) -> None:
    data = document.get(source_key) or {}
    if not data:
        return
    profile = PredictedProfile()
    fields = (
        ('X', 'x'),
        ('Y', 'y'),
        ('Zn_AD_(cosine_old)', 'zn_areal_density'),
        ('Zn_AD_error_(cosine_old)', 'zn_areal_density_error'),
        ('Cu_AD_(cosine_old)', 'cu_areal_density'),
        ('Cu_AD_error_(cosine_old)', 'cu_areal_density_error'),
        ('Zn_fract_(cosine_old)', 'zn_fraction'),
        ('Cu_fract_(cosine_old)', 'cu_fraction'),
    )
    for source, destination in fields:
        if data.get(source) is not None:
            setattr(profile, destination, [float(item) for item in data[source]])
    profile.flux_model = recipe.get('flux_model')
    setattr(plan, attribute, profile)


def parse_experiment_plan_document(text: str) -> SputteringExperimentPlan:
    """Parse the supplied two-document text export into a NOMAD schema section."""
    documents = [_parse_mongo_shell_object(item) for item in _top_level_documents(text)]
    plan_document = next((doc for doc in documents if 'sample_id' in doc), None)
    experiment_document = next((doc for doc in documents if 'recipe' in doc), None)
    if plan_document is None:
        raise ValueError('No experiment-plan document with sample_id was found.')
    if experiment_document is None:
        raise ValueError('No experiment document with recipe was found.')

    plan = SputteringExperimentPlan()
    plan.sample_id = str(plan_document['sample_id'])
    for key in ('expt_plan_id', 'sputter_process_id', 'start_datetime'):
        if plan_document.get(key) is not None:
            setattr(plan, key, plan_document[key])
    if plan_document.get('multilayers') is not None:
        plan.multilayers = int(plan_document['multilayers'])
    _populate_system_state(plan, plan_document.get('system_state') or {})
    recipe = _populate_recipe(plan, experiment_document)
    _populate_profile(plan, experiment_document, recipe, 'x_profiles_pred', 'x_profile')
    _populate_profile(plan, experiment_document, recipe, 'y_profiles_pred', 'y_profile')
    plan.plot()
    return plan


class ExperimentPlanParser(MatchingParser):
    """NOMAD parser for a Mongo-shell text export named experiment_plan.txt."""

    def parse(self, mainfile, archive, logger=None, child_archives=None) -> None:
        log = logger or logger_module
        if archive.data is not None:
            log.debug('Archive already has data, skipping experiment-plan parse')
            return
        text = Path(mainfile).read_text(encoding='utf-8')
        archive.data = parse_experiment_plan_document(text)
        log.info('Parsed sputtering experiment plan for %s', archive.data.sample_id)
