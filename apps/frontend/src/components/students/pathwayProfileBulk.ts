export const pathwayProfileBulkEndpoints = {
  template: "/api/gaokao/pathway-profiles/template",
  export: "/api/gaokao/pathway-profiles/export",
  import: "/api/gaokao/pathway-profiles/import",
} as const;

export interface PathwayProfileBulkAction {
  label: string;
  endpoint: string;
}

export function buildPathwayProfileBulkActions(): PathwayProfileBulkAction[] {
  return [
    { label: "升学画像模板", endpoint: pathwayProfileBulkEndpoints.template },
    { label: "下载画像数据", endpoint: pathwayProfileBulkEndpoints.export },
    { label: "上传画像", endpoint: pathwayProfileBulkEndpoints.import },
  ];
}
