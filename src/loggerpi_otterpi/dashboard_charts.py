"""Chart-/JS-Helfer für das Dashboard."""


def _tooltip_date_logic(dates_json: str) -> str:
    """Erzeugt die JS-Tooltip-Logik für Datum/Zeit."""
    return f"""
                    title: (items) => {{
                        if (items.length > 0) {{
                            const idx = items[0].dataIndex;
                            const dateStr = {dates_json}[idx] || '';
                            const label = items[0].label;

                            let dateLabel = '';
                            if (dateStr) {{
                                const today = new Date();
                                const date = new Date(dateStr + 'T00:00:00');

                                const todayMidnight = new Date(
                                    today.getFullYear(), today.getMonth(), today.getDate()
                                );
                                const dateMidnight = new Date(
                                    date.getFullYear(), date.getMonth(), date.getDate()
                                );

                                const diffDays = Math.round(
                                    (todayMidnight - dateMidnight) / (1000 * 60 * 60 * 24)
                                );

                                if (diffDays === 0) {{
                                    dateLabel = 'today';
                                }} else if (diffDays === 1) {{
                                    dateLabel = 'yesterday';
                                }} else {{
                                    const dd = String(date.getDate()).padStart(2, '0');
                                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                                    const yyyy = date.getFullYear();
                                    dateLabel = `${{dd}}.${{mm}}.${{yyyy}}`;
                                }}
                            }}

                            return `📅 Date: ${{dateLabel}}\\n⏰ Time: ${{label}}`;
                        }}
                        return '';
                    }},"""


def _tooltip_label_color() -> str:
    """Erzeugt die JS-Tooltip-Farb-Logik."""
    return """
                    labelColor: (context) => ({
                        borderColor: context.dataset.borderColor,
                        backgroundColor: context.dataset.borderColor
                    }),
                    labelPointStyle: () => ({
                        pointStyle: 'circle',
                        rotation: 0
                    }),"""


def _render_device_script(device: dict) -> str:
    """Erzeugt das Chart.js-Skript für ein Gerät."""
    chart_var = device["chart_id"].replace("-", "_")

    if device["type"] == "placeholder":
        return ""

    limit_datasets = ""
    for label, value, color, axis in device.get("limit_lines", []):
        limit_datasets += f"""
            {{
                label: '{label}',
                data: {chart_var}Labels.map(() => {value}),
                borderColor: '{color}',
                borderDash: [5, 5],
                pointRadius: 0,
                borderWidth: 1,
                yAxisID: '{axis}',
            }},"""

    if device["type"] in ("freezer", "memmert", "weatherhub_id01"):
        return f"""
const {chart_var}Labels = {device["labels_json"]};
const {chart_var}Dates = {device["dates_json"]};
new Chart(document.getElementById('{device["chart_id"]}'), {{
    type: 'line',
    data: {{
        labels: {chart_var}Labels,
        datasets: [
            {{
                label: 'Temperature',
                data: {device["temp_values_json"]},
                borderColor: '#fb923c',
                borderWidth: 1.5,
                pointRadius: 2,
                pointHoverRadius: 4,
                yAxisID: 'temperature',
                tension: 0.3
            }},{limit_datasets}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{
                labels: {{
                    color: '#d1d5db',
                    usePointStyle: true,
                    pointStyle: 'line',
                    filter: (item) => {{
                        const label = item.text || '';
                        return !label.startsWith('Warning') && !label.startsWith('Critical');
                    }},
                }}
            }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                filter: (item) => {{
                    const label = item.dataset.label || '';
                    return !label.startsWith('Warning') && !label.startsWith('Critical');
                }},
                callbacks: {{
                    labelColor: (context) => ({{
                        borderColor: context.dataset.borderColor,
                        backgroundColor: context.dataset.borderColor
                    }}),
                    labelPointStyle: () => ({{
                        pointStyle: 'circle',
                        rotation: 0
                    }}),
                    title: (items) => {{
                        if (items.length > 0) {{
                            const idx = items[0].dataIndex;
                            const dateStr = {chart_var}Dates[idx] || '';
                            const label = items[0].label;

                            let dateLabel = '';
                            if (dateStr) {{
                                const today = new Date();
                                const date = new Date(dateStr + 'T00:00:00');

                                const todayMidnight = new Date(
                                    today.getFullYear(), today.getMonth(), today.getDate()
                                );
                                const dateMidnight = new Date(
                                    date.getFullYear(), date.getMonth(), date.getDate()
                                );

                                const diffDays = Math.round(
                                    (todayMidnight - dateMidnight) / (1000 * 60 * 60 * 24)
                                );

                                if (diffDays === 0) {{
                                    dateLabel = 'today';
                                }} else if (diffDays === 1) {{
                                    dateLabel = 'yesterday';
                                }} else {{
                                    const dd = String(date.getDate()).padStart(2, '0');
                                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                                    const yyyy = date.getFullYear();
                                    dateLabel = `${{dd}}.${{mm}}.${{yyyy}}`;
                                }}
                            }}

                            return `📅 Date: ${{dateLabel}}\\n⏰ Time: ${{label}}`;
                        }}
                        return '';
                    }},
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        return `Temperature: ${{value}} °C`;
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{
                ticks: {{
                    color: '#9ca3af',
                    callback: (value) => {chart_var}Labels[value]
                }}
            }},
            temperature: {{
                type: 'linear',
                ticks: {{
                    color: '#fb923c',
                    callback: (value) => {{
                        const rounded = Math.round(value * 10) / 10;
                        return rounded + ' °C'
                    }}
                }}
            }}
        }}
    }}
}});
"""

    return f"""
const {chart_var}Labels = {device["labels_json"]};
const {chart_var}Dates = {device["dates_json"]};
const {chart_var}HasHumidity = {device["hum_values_json"]}.length > 0;

const {chart_var}Datasets = [
    {{
        label: 'Temperature',
        data: {device["temp_values_json"]},
        borderColor: '#fb923c',
        borderWidth: 1.5,
        pointRadius: 2,
        pointHoverRadius: 4,
        yAxisID: 'temperature',
        tension: 0.3
    }},{limit_datasets}
];

const {chart_var}Scales = {{
    x: {{
        ticks: {{
            color: '#9ca3af',
            callback: (value) => {chart_var}Labels[value]
        }}
    }},
    temperature: {{
        type: 'linear',
        position: 'left',
        ticks: {{
            color: '#fb923c',
            callback: (value) => {{
                const rounded = Math.round(value * 10) / 10;
                return rounded + ' °C';
            }}
        }}
    }}
}};

if ({chart_var}HasHumidity) {{
    {chart_var}Datasets.push({{
        label: 'Relative Humidity',
        data: {device["hum_values_json"]},
        borderColor: '#38bdf8',
        borderWidth: 1.5,
        pointRadius: 2,
        pointHoverRadius: 4,
        yAxisID: 'humidity',
        tension: 0.3
    }});
}}
{chart_var}Scales.humidity = {{
    type: 'linear',
    position: 'right',
    ticks: {{
        color: '#38bdf8',
        callback: (value) => {{
            const rounded = Math.round(value * 10) / 10;
            return rounded + ' %';
        }}
    }},
    grid: {{ drawOnChartArea: false }}
}};

new Chart(document.getElementById('{device["chart_id"]}'), {{
    type: 'line',
    data: {{
        labels: {chart_var}Labels,
        datasets: {chart_var}Datasets
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{
                labels: {{
                    color: '#d1d5db',
                    usePointStyle: true,
                    pointStyle: 'line',
                    filter: (item) => {{
                        const label = item.text || '';
                        return !label.startsWith('Warning') && !label.startsWith('Critical');
                    }},
                }}
            }},
            tooltip: {{
                usePointStyle: true,
                boxWidth: 6,
                boxHeight: 6,
                filter: (item) => {{
                    const label = item.dataset.label || '';
                    return !label.startsWith('Warning') && !label.startsWith('Critical');
                }},
                callbacks: {{
                    labelColor: (context) => ({{
                        borderColor: context.dataset.borderColor,
                        backgroundColor: context.dataset.borderColor
                    }}),
                    labelPointStyle: () => ({{
                        pointStyle: 'circle',
                        rotation: 0
                    }}),
                    title: (items) => {{
                        if (items.length > 0) {{
                            const idx = items[0].dataIndex;
                            const dateStr = {chart_var}Dates[idx] || '';
                            const label = items[0].label;

                            let dateLabel = '';
                            if (dateStr) {{
                                const today = new Date();
                                const date = new Date(dateStr + 'T00:00:00');

                                const todayMidnight = new Date(
                                    today.getFullYear(), today.getMonth(), today.getDate()
                                );
                                const dateMidnight = new Date(
                                    date.getFullYear(), date.getMonth(), date.getDate()
                                );

                                const diffDays = Math.round(
                                    (todayMidnight - dateMidnight) / (1000 * 60 * 60 * 24)
                                );

                                if (diffDays === 0) {{
                                    dateLabel = 'today';
                                }} else if (diffDays === 1) {{
                                    dateLabel = 'yesterday';
                                }} else {{
                                    const dd = String(date.getDate()).padStart(2, '0');
                                    const mm = String(date.getMonth() + 1).padStart(2, '0');
                                    const yyyy = date.getFullYear();
                                    dateLabel = `${{dd}}.${{mm}}.${{yyyy}}`;
                                }}
                            }}

                            return `📅 Date: ${{dateLabel}}\\n⏰ Time: ${{label}}`;
                        }}
                        return '';
                    }},
                    label: (context) => {{
                        const value = (Math.round(context.parsed.y * 10) / 10).toFixed(1);
                        if (context.dataset.label === 'Temperature') {{
                            return `Temperature: ${{value}} °C`;
                        }}
                        return `Rel. Humidity: ${{value}} %`;
                    }}
                }}
            }}
        }},
        scales: {chart_var}Scales
    }}
}});
"""
