"""NOMAD schema for planned combinatorial sputtering experiments."""

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, SectionProperties
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

m_package = Package(
    name='Uppsala Sputtering Experiment Plan',
    description='Recipe, system state, and predicted composition profiles for sputtering plans.',
)


class ExperimentSystemState(ArchiveSection):
    """Instrument state captured when the plan was prepared."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'datetime',
                    'system_config_id',
                    'target_kWh',
                    'sputter_gas',
                    'qcm_crystal_types',
                    'qcm_lifetimes',
                    'base_pressure_torr',
                ]
            )
        )
    )

    datetime = Quantity(
        type=str,
        description='System-state timestamp as recorded.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    system_config_id = Quantity(
        type=int,
        description='System configuration ID, as recorded in the instrument database.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    target_kWh = Quantity(
        type=np.float64,
        shape=['*'],
        description='Target energy counters.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    sputter_gas = Quantity(
        type=str,
        description='Sputter gas.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    qcm_crystal_types = Quantity(type=str, shape=['*'])
    qcm_lifetimes = Quantity(type=np.float64, shape=['*'])
    base_pressure_torr = Quantity(
        type=np.float64,
        description='Base pressure in Torr.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )


class ExperimentRecipe(ArchiveSection):
    """Predicted sputtering recipe and target composition."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'experiment_type',
                    'expt_id',
                    'sputter_process_id',
                    'cosputter_process_id',
                    'target_composition_zn',
                    'target_composition_cu',
                    'source_1_set_power_w',
                    'source_2_set_power_w',
                    'source_3_set_power_w',
                    'source_4_set_power_w',
                    'source_5_set_power_w',
                    'source_6_set_power_w',
                    'set_pressure_mtorr',
                    'dwell_time_s',
                    'total_rate',
                    'position',
                    'flux_model',
                    'zn_fraction',
                    'cu_fraction',
                    'zn_source_rate',
                    'zn_source_rate_error',
                    'cu_source_rate',
                    'cu_source_rate_error',
                    'raw_recipe_json',
                ]
            )
        )
    )

    experiment_type = Quantity(
        type=str,
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    expt_id = Quantity(type=str)
    sputter_process_id = Quantity(type=str)
    cosputter_process_id = Quantity(type=str)
    target_composition_zn = Quantity(type=np.float64)
    target_composition_cu = Quantity(type=np.float64)

    source_1_set_power_w = Quantity(
        type=np.float64,
        description='Source 1 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    source_2_set_power_w = Quantity(
        type=np.float64,
        description='Source 2 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    source_3_set_power_w = Quantity(
        type=np.float64,
        description='Source 3 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    source_4_set_power_w = Quantity(
        type=np.float64,
        description='Source 4 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    source_5_set_power_w = Quantity(
        type=np.float64,
        description='Source 5 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    source_6_set_power_w = Quantity(
        type=np.float64,
        description='Source 6 set power in W.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    set_pressure_mtorr = Quantity(
        type=np.float64,
        description='Set pressure in mTorr.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    dwell_time_s = Quantity(
        type=np.float64,
        description='Dwell time in seconds.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    total_rate = Quantity(
        type=np.float64,
        description='Total rate, in source units (10^15 at/cm2/s).',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )
    position = Quantity(
        type=str,
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )
    flux_model = Quantity(type=str)
    zn_fraction = Quantity(
        type=np.float64, description='Predicted Zn fraction in the deposited film.'
    )
    cu_fraction = Quantity(
        type=np.float64, description='Predicted Cu fraction in the deposited film.'
    )
    zn_source_rate = Quantity(
        type=np.float64,
        description='Predicted Zn source rate (10^15 at/cm2/s).',
    )
    zn_source_rate_error = Quantity(
        type=np.float64,
        description='Uncertainty in predicted Zn source rate (10^15 at/cm2/s).',
    )
    cu_source_rate = Quantity(
        type=np.float64,
        description='Predicted Cu source rate (10^15 at/cm2/s).',
    )
    cu_source_rate_error = Quantity(
        type=np.float64,
        description='Uncertainty in predicted Cu source rate (10^15 at/cm2/s).',
    )
    raw_recipe_json = Quantity(
        type=str,
        description='Complete recipe object as JSON, retaining fields not modeled individually.',
    )


class PredictedProfile(ArchiveSection):
    """One predicted line profile; arrays retain the source values and units."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'x',
                    'y',
                    'zn_areal_density',
                    'zn_areal_density_error',
                    'cu_areal_density',
                    'cu_areal_density_error',
                    'zn_fraction',
                    'cu_fraction',
                    'flux_model',
                ]
            )
        )
    )

    x = Quantity(
        type=np.float64,
        shape=['*'],
        description='X coordinate, in source coordinate units.',
    )
    y = Quantity(
        type=np.float64,
        shape=['*'],
        description='Y coordinate, in source coordinate units.',
    )
    zn_areal_density = Quantity(
        type=np.float64,
        shape=['*'],
        description='Predicted Zn AD values, in source units.',
    )
    zn_areal_density_error = Quantity(type=np.float64, shape=['*'])
    cu_areal_density = Quantity(
        type=np.float64,
        shape=['*'],
        description='Predicted Cu AD values, in source units.',
    )
    cu_areal_density_error = Quantity(type=np.float64, shape=['*'])
    zn_fraction = Quantity(type=np.float64, shape=['*'])
    cu_fraction = Quantity(type=np.float64, shape=['*'])
    flux_model = Quantity(type=str)


class SputteringExperimentPlan(EntryData, PlotSection):
    """Parsed experiment plan with source and deposition-map plots."""

    m_def = Section(
        label='Sputtering Experiment Plan',
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'sample_id',
                    'expt_plan_id',
                    'sputter_process_id',
                    'start_datetime',
                    'multilayers',
                    'system_state',
                    'recipe',
                    'x_profile',
                    'y_profile',
                ]
            )
        ),
    )

    sample_id = Quantity(type=str)
    expt_plan_id = Quantity(type=str)
    sputter_process_id = Quantity(type=str)
    start_datetime = Quantity(
        type=str, description='Planned start timestamp as recorded.'
    )
    multilayers = Quantity(type=int)
    system_state = SubSection(section_def=ExperimentSystemState)
    recipe = SubSection(section_def=ExperimentRecipe)
    x_profile = SubSection(section_def=PredictedProfile)
    y_profile = SubSection(section_def=PredictedProfile)

    def plot(self) -> None:
        """Plot all six source powers and their circular source arrangement.

        Composition and thickness maps are intentionally deferred until the
        cosine model provides spatially resolved predictions.
        """
        powers = [
            (
                getattr(self.recipe, f'source_{number}_set_power_w', None)
                if self.recipe is not None
                else None
            )
            for number in range(1, 7)
        ]
        # In the supplied recipe, source 1 is the active Zn target and source 3
        # is the active Cu target; the other source powers are zero.
        source_elements = {1: 'Zn', 3: 'Cu'}
        element_colors = {'Zn': '#2878a5', 'Cu': '#c66a32', 'Unknown': '#aab2b9'}
        source_names = [
            f'Source {number} ({source_elements.get(number, "unassigned")})'
            for number in range(1, 7)
        ]
        source_rates = [
            (
                getattr(self.recipe, f'{element.lower()}_source_rate', None)
                if self.recipe is not None and (element := source_elements.get(number))
                else None
            )
            for number in range(1, 7)
        ]
        source_rate_errors = [
            (
                getattr(self.recipe, f'{element.lower()}_source_rate_error', None)
                if self.recipe is not None and (element := source_elements.get(number))
                else None
            )
            for number in range(1, 7)
        ]

        power_figure = go.Figure(
            go.Bar(
                x=source_names,
                y=[float(power) if power is not None else None for power in powers],
                marker_color=[
                    element_colors.get(
                        source_elements.get(number, 'Unknown'),
                        element_colors['Unknown'],
                    )
                    for number in range(1, 7)
                ],
                text=[
                    f'{float(power):g} W' if power is not None else 'Not set'
                    for power in powers
                ],
                textposition='outside',
                customdata=[
                    [
                        source_elements.get(number, 'Unassigned'),
                        rate,
                        rate_error,
                    ]
                    for number, rate, rate_error in zip(
                        range(1, 7), source_rates, source_rate_errors
                    )
                ],
                hovertemplate=(
                    '%{x}<br>Element: %{customdata[0]}'
                    '<br>Set power: %{y} W'
                    '<br>Predicted source rate: %{customdata[1]:.3f}'
                    ' +/- %{customdata[2]:.3f} (10^15 at/cm2/s)<extra></extra>'
                ),
            )
        )
        composition_summary = ''
        if self.recipe is not None:
            composition_parts = [
                f'{element} {fraction * 100:.1f}%'
                for element, fraction in (
                    ('Zn', self.recipe.zn_fraction),
                    ('Cu', self.recipe.cu_fraction),
                )
                if fraction is not None
            ]
            summary_parts = []
            if composition_parts:
                summary_parts.append(
                    'Predicted composition: ' + ', '.join(composition_parts)
                )
            if self.recipe.total_rate is not None:
                summary_parts.append(
                    f'Total rate: {self.recipe.total_rate:.3f} x 10^15 at/cm2/s'
                )
            if self.recipe.set_pressure_mtorr is not None:
                summary_parts.append(
                    f'Pressure: {self.recipe.set_pressure_mtorr:g} mTorr'
                )
            if self.recipe.dwell_time_s is not None:
                summary_parts.append(f'Dwell: {self.recipe.dwell_time_s:g} s')
            if summary_parts:
                composition_summary = '<br><sup>' + ' | '.join(summary_parts) + '</sup>'
        power_figure.update_layout(
            title='Source power and predicted element rates' + composition_summary,
            xaxis_title='Source',
            yaxis_title='Set power (W)',
            template='plotly_white',
            showlegend=False,
        )

        # Index the six sources clockwise from the top to show their 60-degree
        # spacing. This is a schematic; it does not imply physical distances.
        angles = np.deg2rad(90 - np.arange(6) * 60)
        radius = 1.0
        x_positions = radius * np.cos(angles)
        y_positions = radius * np.sin(angles)
        positions_figure = go.Figure()
        substrate_radius = 0.38
        notch_half_width = 0.07
        notch_tip_y = -0.25
        circle_angles = np.linspace(0, 2 * np.pi, 181)
        substrate_x = substrate_radius * np.cos(circle_angles)
        substrate_y = substrate_radius * np.sin(circle_angles)
        before_notch = circle_angles < np.deg2rad(250)
        after_notch = circle_angles > np.deg2rad(290)
        substrate_x = np.concatenate(
            [
                substrate_x[before_notch],
                [-notch_half_width, 0, notch_half_width],
                substrate_x[after_notch],
            ]
        )
        substrate_y = np.concatenate(
            [
                substrate_y[before_notch],
                [-0.37, notch_tip_y, -0.37],
                substrate_y[after_notch],
            ]
        )
        positions_figure.add_trace(
            go.Scatter(
                x=substrate_x,
                y=substrate_y,
                mode='lines',
                fill='toself',
                fillcolor='#e8eef2',
                line=dict(color='#405563', width=2),
                hoverinfo='skip',
                showlegend=False,
            )
        )
        positions_figure.add_annotation(
            x=0,
            y=0,
            text='Circular<br>substrate',
            showarrow=False,
            font=dict(size=12, color='#263746'),
        )
        positions_figure.add_trace(
            go.Scatter(
                x=radius * np.cos(circle_angles),
                y=radius * np.sin(circle_angles),
                mode='lines',
                line=dict(color='#9aa7b2', dash='dash'),
                hoverinfo='skip',
                showlegend=False,
            )
        )
        positions_figure.add_trace(
            go.Scatter(
                x=x_positions,
                y=y_positions,
                mode='markers+text',
                text=source_names,
                textposition=[
                    'top center',
                    'middle right',
                    'middle right',
                    'bottom center',
                    'middle left',
                    'middle left',
                ],
                marker=dict(
                    size=18,
                    color=[
                        element_colors.get(
                            source_elements.get(number, 'Unknown'),
                            element_colors['Unknown'],
                        )
                        for number in range(1, 7)
                    ],
                    line=dict(color='white', width=2),
                ),
                customdata=np.arange(6) * 60,
                hovertemplate='%{text}<br>Angular spacing: 60 degrees<extra></extra>',
                showlegend=False,
            )
        )
        for element, color in (
            ('Zn source', element_colors['Zn']),
            ('Cu source', element_colors['Cu']),
            ('Unassigned / off', element_colors['Unknown']),
        ):
            positions_figure.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='markers',
                    marker=dict(size=11, color=color),
                    name=element,
                    hoverinfo='skip',
                )
            )
        positions_figure.update_layout(
            title='Source positions around circular substrate (60 degrees apart)',
            template='plotly_white',
            xaxis=dict(
                title='X position (schematic)',
                visible=True,
                showgrid=True,
                zeroline=True,
                zerolinecolor='#6c7a86',
                scaleanchor='y',
                scaleratio=1,
                range=[-1.65, 1.65],
            ),
            yaxis=dict(
                title='Y position (schematic)',
                visible=True,
                showgrid=True,
                zeroline=True,
                zerolinecolor='#6c7a86',
                range=[-1.4, 1.4],
            ),
            margin=dict(l=20, r=20, t=55, b=20),
            legend=dict(
                orientation='h', yanchor='top', y=-0.02, x=0.5, xanchor='center'
            ),
        )

        self.figures = [
            PlotlyFigure(label='Source powers', figure=power_figure.to_plotly_json()),
            PlotlyFigure(
                label='Source position schematic',
                figure=positions_figure.to_plotly_json(),
            ),
        ]


m_package.__init_metainfo__()
