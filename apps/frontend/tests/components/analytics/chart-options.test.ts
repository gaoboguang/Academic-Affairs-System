import { describe, expect, it } from "vitest";

import {
  buildHeatmapOption,
  buildPeerCompareOption,
  buildRadarOption,
  buildSparklineOption,
  buildTotalTrendOption,
  type RadarAxis,
  type RadarSeries,
  type TrendPoint,
} from "../../../src/components/analytics/chartOptions";

describe("buildTotalTrendOption", () => {
  it("emits dual-axis line chart with both series", () => {
    const points: TrendPoint[] = [
      { label: "考1", score: 580, rank: 200 },
      { label: "考2", score: 590, rank: 180 },
      { label: "考3", score: null, rank: null },
    ];
    const option = buildTotalTrendOption(points);
    expect(Array.isArray(option.series)).toBe(true);
    const series = option.series as Array<{ name: string; data: unknown[] }>;
    expect(series).toHaveLength(2);
    expect(series[0].name).toBe("总分");
    expect(series[1].name).toBe("校内名次");
    expect(series[0].data).toEqual([580, 590, null]);
    expect(series[1].data).toEqual([200, 180, null]);
  });
});

describe("buildSparklineOption", () => {
  it("hides axes for an inline sparkline", () => {
    const option = buildSparklineOption([10, 20, 15, null, 25]);
    expect((option.xAxis as { show: boolean }).show).toBe(false);
    expect((option.yAxis as { show: boolean }).show).toBe(false);
  });
});

describe("buildRadarOption", () => {
  it("emits one radar series per input layer with axes intact", () => {
    const axes: RadarAxis[] = [
      { name: "语文", max: 80 },
      { name: "数学", max: 80 },
      { name: "英语", max: 80 },
    ];
    const series: RadarSeries[] = [
      { name: "本人", values: [62, 55, null] },
      { name: "班级平均", values: [50, 50, 50] },
    ];
    const option = buildRadarOption(axes, series);
    const radarSeries = option.series as Array<{ data: Array<{ name: string; value: unknown[] }> }>;
    expect(radarSeries).toHaveLength(1);
    expect(radarSeries[0].data).toHaveLength(2);
    expect(radarSeries[0].data[0].name).toBe("本人");
    expect(radarSeries[0].data[0].value).toEqual([62, 55, null]);
  });
});

describe("buildPeerCompareOption", () => {
  it("aligns rows in the y-axis with student/peer bars", () => {
    const rows = [
      { subjectName: "语文", studentScore: 70, peerAverage: 80 },
      { subjectName: "数学", studentScore: null, peerAverage: 65 },
    ];
    const option = buildPeerCompareOption(rows);
    expect((option.yAxis as { data: string[] }).data).toEqual(["语文", "数学"]);
    const series = option.series as Array<{ name: string; data: Array<number | null> }>;
    expect(series[0].name).toBe("本人");
    expect(series[0].data).toEqual([70, null]);
    expect(series[1].name).toBe("同分段平均");
    expect(series[1].data).toEqual([80, 65]);
  });
});

describe("buildHeatmapOption", () => {
  it("forwards the cell matrix and shows visualMap legend", () => {
    const matrix = {
      rowLabels: ["阅读", "作文"],
      columnLabels: ["张三", "李四"],
      cells: [
        [0, 0, 0.7],
        [0, 1, 0.5],
        [1, 0, 0.4],
        [1, 1, 0.6],
      ] as Array<[number, number, number | null]>,
    };
    const option = buildHeatmapOption(matrix);
    expect((option.xAxis as { data: string[] }).data).toEqual(["张三", "李四"]);
    expect((option.yAxis as { data: string[] }).data).toEqual(["阅读", "作文"]);
    const series = option.series as Array<{ data: unknown[] }>;
    expect(series[0].data).toHaveLength(4);
    expect(option.visualMap).toBeDefined();
  });
});
