import type { EChartsOption } from "echarts";

export interface TrendPoint {
  label: string;
  score?: number | null;
  rank?: number | null;
}

const PRIMARY_COLOR = "#1f6c98";
const ACCENT_COLOR = "#d18d48";
const MUTED_COLOR = "#a8b3bd";

export function buildTotalTrendOption(points: TrendPoint[]): EChartsOption {
  const xLabels = points.map((point) => point.label);
  const scoreSeries = points.map((point) => (point.score ?? null) as number | null);
  const rankSeries = points.map((point) => (point.rank ?? null) as number | null);
  return {
    grid: { top: 40, right: 50, bottom: 30, left: 50 },
    tooltip: { trigger: "axis", confine: true },
    legend: { data: ["总分", "校内名次"], top: 6, right: 8 },
    xAxis: {
      type: "category",
      data: xLabels,
      axisLabel: { color: "#5b6a76", fontSize: 11 },
    },
    yAxis: [
      {
        type: "value",
        name: "总分",
        nameTextStyle: { color: "#5b6a76", fontSize: 11 },
        axisLabel: { color: "#5b6a76", fontSize: 11 },
        scale: true,
      },
      {
        type: "value",
        name: "校排（越小越好）",
        nameTextStyle: { color: "#5b6a76", fontSize: 11 },
        axisLabel: { color: "#5b6a76", fontSize: 11 },
        inverse: true,
        scale: true,
      },
    ],
    series: [
      {
        name: "总分",
        type: "line",
        smooth: true,
        data: scoreSeries,
        connectNulls: true,
        symbol: "circle",
        symbolSize: 8,
        itemStyle: { color: PRIMARY_COLOR },
        lineStyle: { width: 2.5, color: PRIMARY_COLOR },
      },
      {
        name: "校内名次",
        type: "line",
        smooth: true,
        yAxisIndex: 1,
        data: rankSeries,
        connectNulls: true,
        symbol: "circle",
        symbolSize: 6,
        itemStyle: { color: ACCENT_COLOR },
        lineStyle: { width: 2, color: ACCENT_COLOR, type: "dashed" },
      },
    ],
  };
}

export function buildSparklineOption(values: Array<number | null>): EChartsOption {
  return {
    grid: { top: 4, right: 4, bottom: 4, left: 4 },
    xAxis: {
      type: "category",
      show: false,
      data: values.map((_, index) => `${index + 1}`),
    },
    yAxis: { type: "value", show: false, scale: true },
    series: [
      {
        type: "line",
        smooth: true,
        data: values,
        connectNulls: true,
        showSymbol: false,
        lineStyle: { color: PRIMARY_COLOR, width: 1.8 },
        areaStyle: { color: "rgba(31, 108, 152, 0.15)" },
      },
    ],
  };
}

export interface RadarAxis {
  name: string;
  max: number;
}

export interface RadarSeries {
  name: string;
  values: Array<number | null>;
  color?: string;
}

export function buildRadarOption(axes: RadarAxis[], series: RadarSeries[]): EChartsOption {
  return {
    tooltip: { confine: true },
    legend: { top: 6, right: 8, textStyle: { color: "#5b6a76", fontSize: 12 } },
    radar: {
      indicator: axes.map((axis) => ({ name: axis.name, max: axis.max })),
      splitArea: { areaStyle: { color: ["rgba(31,108,152,0.04)", "rgba(31,108,152,0.08)"] } },
      axisName: { color: "#1d3147", fontSize: 12 },
    },
    series: [
      {
        type: "radar",
        data: series.map((entry, index) => ({
          name: entry.name,
          value: entry.values,
          areaStyle: {
            color:
              entry.color
              ?? (index === 0 ? "rgba(31, 108, 152, 0.30)" : "rgba(209, 141, 72, 0.18)"),
          },
          lineStyle: {
            color: entry.color ?? (index === 0 ? PRIMARY_COLOR : ACCENT_COLOR),
            width: 2,
          },
          itemStyle: {
            color: entry.color ?? (index === 0 ? PRIMARY_COLOR : ACCENT_COLOR),
          },
        })),
      },
    ],
  };
}

export interface PeerCompareRow {
  subjectName: string;
  studentScore: number | null;
  peerAverage: number | null;
}

export function buildPeerCompareOption(rows: PeerCompareRow[]): EChartsOption {
  return {
    grid: { top: 30, right: 24, bottom: 24, left: 80 },
    tooltip: { trigger: "axis", confine: true, axisPointer: { type: "shadow" } },
    legend: { data: ["本人", "同分段平均"], top: 4, right: 8 },
    xAxis: { type: "value", scale: true },
    yAxis: { type: "category", data: rows.map((row) => row.subjectName) },
    series: [
      {
        name: "本人",
        type: "bar",
        data: rows.map((row) => row.studentScore ?? null),
        itemStyle: { color: PRIMARY_COLOR },
        barGap: 0,
      },
      {
        name: "同分段平均",
        type: "bar",
        data: rows.map((row) => row.peerAverage ?? null),
        itemStyle: { color: MUTED_COLOR },
      },
    ],
  };
}

export interface HeatmapMatrix {
  rowLabels: string[];
  columnLabels: string[];
  cells: Array<[number, number, number | null]>;
}

export function buildHeatmapOption(matrix: HeatmapMatrix): EChartsOption {
  return {
    grid: { top: 28, right: 24, bottom: 60, left: 100 },
    tooltip: {
      position: "top",
      confine: true,
      formatter: (params) => {
        const value = (params as unknown as { value: [number, number, number | null] }).value;
        const x = matrix.columnLabels[value[0]] ?? "-";
        const y = matrix.rowLabels[value[1]] ?? "-";
        const v = value[2];
        return `${y} / ${x}<br/>得分率 ${v == null ? "-" : (v * 100).toFixed(1) + "%"}`;
      },
    },
    xAxis: {
      type: "category",
      data: matrix.columnLabels,
      axisLabel: { color: "#5b6a76", fontSize: 10, rotate: 30, interval: 0 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: matrix.rowLabels,
      axisLabel: { color: "#5b6a76", fontSize: 11 },
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max: 1,
      bottom: 8,
      left: "center",
      orient: "horizontal",
      itemHeight: 80,
      inRange: { color: ["#c0392b", "#e9b97e", "#f5f5f5", "#7ba9c8", "#1f6c98"] },
      text: ["1.0", "0"],
      calculable: false,
    },
    series: [
      {
        type: "heatmap",
        data: matrix.cells,
        label: { show: false },
        emphasis: { itemStyle: { borderColor: "#1d3147", borderWidth: 1.5 } },
      },
    ],
  };
}
