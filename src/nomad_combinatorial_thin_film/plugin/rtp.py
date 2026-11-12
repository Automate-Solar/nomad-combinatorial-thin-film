"""NOMAD schema for Rapid Thermal Processing (RTP) experiments."""

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    SectionProperties,
)
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Datetime, Package, Quantity, Section, SubSection
from plotly.subplots import make_subplots

from nomad_combinatorial_thin_film.categories import Uppsala

m_package = Package(
    name='Uppsala RTP Experiment',
    description=(
        'Rapid thermal processing experiment metadata, '
        'temperature programs, and process time-series measurements.'
    ),
    categories=[Uppsala],
)


# =====================================================================
# Helper functions
# =====================================================================


def _to_float(value):
    """Convert a scalar, including a Pint quantity, to a Python float."""
    if value is None:
        return None

    if hasattr(value, 'magnitude'):
        value = value.magnitude

    return float(value)


def _to_float_array(values):
    """Convert an array or Pint quantity array to a NumPy float array."""
    if values is None:
        return np.array([], dtype=float)

    if hasattr(values, 'magnitude'):
        values = values.magnitude

    return np.asarray(values, dtype=float)


def _normalize_channel_name(name):
    """Normalize a channel name for case- and punctuation-insensitive matching."""
    if not name:
        return ''

    return ''.join(character for character in name.lower() if character.isalnum())


def _find_channel(channels, aliases):
    """
    Find a channel using any accepted name or alias.

    Examples:
        temp_[C] -> tempc
        temp     -> temp
        pressure_[hPa] -> pressurehpa
    """
    normalized_aliases = {_normalize_channel_name(alias) for alias in aliases}

    for channel in channels:
        if not channel.name:
            continue

        normalized_name = _normalize_channel_name(channel.name)

        if normalized_name in normalized_aliases:
            return channel

    return None


# =====================================================================
# RTP temperature program step
# =====================================================================


class RTPProgramStep(ArchiveSection):
    """One programmed temperature step in the RTP recipe."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'step_number',
                    'target_temperature_c',
                    'ramp_rate_c_min',
                    'dwell_time_min',
                ]
            )
        )
    )

    step_number = Quantity(
        type=int,
        description='Sequential number of the RTP program step.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    target_temperature_c = Quantity(
        type=np.float64,
        unit='°C',
        description='Programmed target temperature.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    ramp_rate_c_min = Quantity(
        type=np.float64,
        unit='°C/min',
        description='Programmed heating ramp rate.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    dwell_time_min = Quantity(
        type=np.float64,
        unit='min',
        description='Programmed dwell time at the target temperature.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )


# =====================================================================
# RTP measurement channel
# =====================================================================


class RTPChannel(ArchiveSection):
    """One measured channel from the RTP time-series data."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'name',
                    'unit',
                    'values',
                    'mean',
                    'minimum',
                    'maximum',
                ]
            )
        )
    )

    name = Quantity(
        type=str,
        description='Original channel name from the RTP log.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    unit = Quantity(
        type=str,
        description='Measurement unit of the channel.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    values = Quantity(
        type=np.float64,
        shape=['*'],
        description='Complete time-series values for this channel.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    mean = Quantity(
        type=np.float64,
        description='Mean of the recorded channel values.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    minimum = Quantity(
        type=np.float64,
        description='Minimum of the recorded channel values.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    maximum = Quantity(
        type=np.float64,
        description='Maximum of the recorded channel values.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )


# =====================================================================
# RTP experiment
# =====================================================================


class RTPRun(EntryData, PlotSection):
    """Rapid thermal processing experiment and its measurements."""

    m_def = Section(
        categories=[Uppsala],
        label='RTP Experiment',
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'sample_id',
                    'run_id',
                    'source_filename',
                    'start_datetime',
                    'end_datetime',
                    'start_temperature_c',
                    'base_pressure_hpa',
                    'process_gas_pressure',
                    'forced_cooling',
                    'final_cool_rate_c_min',
                    'stop_temperature_c',
                    'duration_s',
                    'number_of_samples',
                    'log_file',
                    'plot_file',
                    'errors',
                    'temperature_steps',
                    'time_s',
                    'channels',
                ]
            )
        ),
    )

    # -----------------------------------------------------------------
    # Experiment metadata
    # -----------------------------------------------------------------

    sample_id = Quantity(
        type=str,
        description='Sample identifier.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    run_id = Quantity(
        type=str,
        description='Unique RTP run identifier.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    source_filename = Quantity(
        type=str,
        description='Name of the original RTP JSON file.',
        a_eln=ELNAnnotation(component='FileEditQuantity'),
    )

    start_datetime = Quantity(
        type=Datetime,
        description='Recorded RTP experiment start datetime.',
        a_eln=ELNAnnotation(component='DateTimeEditQuantity'),
    )

    end_datetime = Quantity(
        type=Datetime,
        description='Recorded RTP experiment end datetime.',
        a_eln=ELNAnnotation(component='DateTimeEditQuantity'),
    )

    start_temperature_c = Quantity(
        type=np.float64,
        unit='°C',
        description='Temperature at the beginning of the RTP process.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    base_pressure_hpa = Quantity(
        type=np.float64,
        unit='hPa',
        description='Base chamber pressure before processing.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    process_gas_pressure = Quantity(
        type=np.float64,
        description=(
            'Configured process gas pressure. '
            'The original JSON does not specify its unit.'
        ),
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    forced_cooling = Quantity(
        type=bool,
        description='Whether forced cooling was enabled.',
        a_eln=ELNAnnotation(component='BoolEditQuantity'),
    )

    final_cool_rate_c_min = Quantity(
        type=np.float64,
        unit='°C/min',
        description='Configured final cooling rate.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    stop_temperature_c = Quantity(
        type=np.float64,
        unit='°C',
        description='Configured temperature at which the process stops.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    duration_s = Quantity(
        type=np.float64,
        unit='s',
        description='Duration of the recorded time-series data.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    number_of_samples = Quantity(
        type=int,
        description='Number of recorded time-series samples.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    log_file = Quantity(
        type=str,
        description='Original RTP CSV log-file path recorded in the JSON.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    plot_file = Quantity(
        type=str,
        description='Original RTP process-plot path recorded in the JSON.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    errors = Quantity(
        type=str,
        shape=['*'],
        description='Errors recorded during the RTP process.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    # -----------------------------------------------------------------
    # Programmed temperature steps
    # -----------------------------------------------------------------

    temperature_steps = SubSection(
        section_def=RTPProgramStep,
        repeats=True,
    )

    # -----------------------------------------------------------------
    # Time-series data
    # -----------------------------------------------------------------

    time_s = Quantity(
        type=np.float64,
        shape=['*'],
        unit='s',
        description='Elapsed process time in seconds.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    channels = SubSection(
        section_def=RTPChannel,
        repeats=True,
    )

    # =================================================================
    # Plotting
    # =================================================================

    def plot(self):
        """
        Generate three vertically stacked plots:

        1. Measured and recorded set temperature.
        2. Chamber pressure.
        3. Gas flow.

        All plots share the same time axis.
        """

        time_s = _to_float_array(self.time_s)

        if time_s.size == 0:
            self.figures = []
            return

        time_range = [float(time_s[0]), float(time_s[-1])]

        # -------------------------------------------------------------
        # Create subplots
        # -------------------------------------------------------------

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.09,
            subplot_titles=(
                'Temperature profile',
                'Chamber pressure',
                'Gas flow',
            ),
        )

        # -------------------------------------------------------------
        # 1. Measured temperature
        # -------------------------------------------------------------

        measured_temperature = _find_channel(
            self.channels,
            {
                'temp_[C]',
                'temp',
                'temperature',
                'measured_temperature',
            },
        )

        if measured_temperature is not None:
            values = _to_float_array(measured_temperature.values)

            if values.size == time_s.size:
                fig.add_trace(
                    go.Scatter(
                        x=time_s,
                        y=values,
                        mode='lines',
                        name='Measured temperature',
                        line=dict(
                            width=1.7,
                            dash='solid',
                        ),
                        connectgaps=False,
                    ),
                    row=1,
                    col=1,
                )

        # -------------------------------------------------------------
        # Recorded set temperature
        # -------------------------------------------------------------

        set_temperature = _find_channel(
            self.channels,
            {
                'set_temp_[C]',
                'set_temp',
                'set_temperature',
                'settemperature',
            },
        )

        if set_temperature is not None:
            values = _to_float_array(set_temperature.values)

            if values.size == time_s.size:
                fig.add_trace(
                    go.Scatter(
                        x=time_s,
                        y=values,
                        mode='lines',
                        name='Recorded set temperature',
                        line=dict(
                            width=1.5,
                            dash='dash',
                        ),
                        connectgaps=False,
                    ),
                    row=1,
                    col=1,
                )

        # -------------------------------------------------------------
        # Programmed target temperature reference lines
        # -------------------------------------------------------------

        for step in self.temperature_steps:
            target = _to_float(step.target_temperature_c)

            if target is None:
                continue

            fig.add_hline(
                y=target,
                line_dash='dot',
                line_color='gray',
                line_width=1.2,
                annotation_text=f'Programmed target: {target:.1f} °C',
                annotation_position='top right',
                row=1,
                col=1,
            )

        # -------------------------------------------------------------
        # 2. Chamber pressure
        # -------------------------------------------------------------

        pressure_channel = _find_channel(
            self.channels,
            {
                'pressure_[hpa]',
                'pressure',
                'chamber_pressure',
            },
        )

        if pressure_channel is not None:
            pressure_values = _to_float_array(pressure_channel.values)

            if pressure_values.size == time_s.size:
                fig.add_trace(
                    go.Scatter(
                        x=time_s,
                        y=pressure_values,
                        mode='lines',
                        name='Chamber pressure',
                        line=dict(width=1.7),
                        connectgaps=False,
                    ),
                    row=2,
                    col=1,
                )

        # -------------------------------------------------------------
        # 3. Gas flow
        # -------------------------------------------------------------

        flow_channel = _find_channel(
            self.channels,
            {
                'flow_[sccm]',
                'flow',
                'gas_flow',
            },
        )

        if flow_channel is not None:
            flow_values = _to_float_array(flow_channel.values)

            if flow_values.size == time_s.size:
                fig.add_trace(
                    go.Scatter(
                        x=time_s,
                        y=flow_values,
                        mode='lines',
                        name='Gas flow',
                        line=dict(width=1.7),
                        connectgaps=False,
                    ),
                    row=3,
                    col=1,
                )

        # -------------------------------------------------------------
        # Axis labels and grid
        # -------------------------------------------------------------

        fig.update_xaxes(
            title_text='Time (s)',
            showgrid=True,
            row=3,
            col=1,
        )

        fig.update_yaxes(
            title_text='Temperature (°C)',
            showgrid=True,
            row=1,
            col=1,
        )

        fig.update_yaxes(
            title_text='Pressure (hPa)',
            showgrid=True,
            row=2,
            col=1,
        )

        fig.update_yaxes(
            title_text='Flow (sccm)',
            showgrid=True,
            row=3,
            col=1,
        )

        # -------------------------------------------------------------
        # Figure layout
        # -------------------------------------------------------------

        fig.update_layout(
            title='Rapid Thermal Processing – Process Profile',
            template='plotly_white',
            hovermode='x unified',
            height=850,
            margin=dict(
                l=80,
                r=50,
                t=110,
                b=70,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
            ),
        )

        fig.update_xaxes(
            showgrid=True,
            range=time_range,
            autorange=False,
        )
        fig.update_yaxes(showgrid=True)

        # -------------------------------------------------------------
        # Attach figure using NOMAD's PlotlyFigure subsection
        # -------------------------------------------------------------

        self.figures = [
            PlotlyFigure(
                label='RTP Process Profile',
                figure=fig.to_plotly_json(),
            )
        ]


m_package.__init_metainfo__()
