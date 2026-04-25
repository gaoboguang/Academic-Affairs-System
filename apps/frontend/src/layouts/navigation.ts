import type { Component } from "vue";
import {
  DataAnalysis,
  Document,
  EditPen,
  Files,
  Histogram,
  HomeFilled,
  Notebook,
  Reading,
  School,
  Setting,
  Tickets,
  UploadFilled,
  UserFilled,
} from "@element-plus/icons-vue";

export interface AppNavItem {
  path: string;
  label: string;
  description: string;
  helper: string;
  icon: Component;
  tags: string[];
  matchPrefixes?: string[];
}

export interface AppNavSection {
  id: string;
  title: string;
  summary: string;
  items: AppNavItem[];
}

export interface ResolvedAppNavItem extends AppNavItem {
  sectionId: string;
  sectionTitle: string;
  sectionSummary: string;
}

export const navSections: AppNavSection[] = [
  {
    id: "home",
    title: "总览",
    summary: "先看全局状态，再进入具体业务页面。",
    items: [
      {
        path: "/",
        label: "工作台",
        description: "查看最近考试、导入记录、备份状态和数据质量提醒。",
        helper: "建议先确认全局状态，再进入考试、分析、推荐或系统设置。",
        icon: HomeFilled,
        tags: ["全局状态", "最近考试", "导入记录"],
      },
    ],
  },
  {
    id: "base",
    title: "基础数据",
    summary: "维护学校基础台账与人员档案。",
    items: [
      {
        path: "/base-data",
        label: "基础数据",
        description: "维护学年学期、年级班级、学科和字典等主数据。",
        helper: "多数业务页面依赖这里的数据，修改前请确认影响范围。",
        icon: Files,
        tags: ["学年学期", "字典", "班级结构"],
      },
      {
        path: "/students",
        label: "学生中心",
        description: "维护学生主档、导入导出和学生详情。",
        helper: "学生数据准确后，成绩分析、成长档案和升学推荐结果才可靠。",
        icon: UserFilled,
        tags: ["学生档案", "导入导出", "学生详情"],
        matchPrefixes: ["/students/"],
      },
      {
        path: "/growth-archive",
        label: "成长档案",
        description: "记录成长事件、附件和阶段性摘要。",
        helper: "适合在学生主档稳定后补录，避免和基础录入混在一起。",
        icon: Notebook,
        tags: ["成长记录", "附件", "时间线"],
      },
      {
        path: "/teachers",
        label: "教师中心",
        description: "维护教师台账、任教关系和教师画像。",
        helper: "教师与任教关系会影响工作量、评教和教师分析结果。",
        icon: Reading,
        tags: ["教师档案", "任教关系", "教师画像"],
        matchPrefixes: ["/teachers/"],
      },
    ],
  },
  {
    id: "teaching",
    title: "教学业务",
    summary: "处理考试、分析、课表和量化业务。",
    items: [
      {
        path: "/exams",
        label: "考试成绩",
        description: "创建考试、配置科目并导入成绩批次。",
        helper: "完成考试与成绩导入后，再进入分析中心查看结果。",
        icon: EditPen,
        tags: ["考试配置", "成绩导入", "快照"],
      },
      {
        path: "/analytics",
        label: "分析中心",
        description: "查看学生、班级、年级和教师分析结果。",
        helper: "分析结果依赖考试快照与基础数据，请先确认源数据准确。",
        icon: DataAnalysis,
        tags: ["学生分析", "班级分析", "教师分析"],
      },
      {
        path: "/import-center",
        label: "导入中心",
        description: "统一查看导入模板、批次、错误报告和撤销说明。",
        helper: "导入完成后先看这里确认是否成功，再进入对应业务页面修正。",
        icon: UploadFilled,
        tags: ["模板下载", "批次记录", "错误报告"],
      },
      {
        path: "/workload",
        label: "课表工作量",
        description: "完成课表导入、修正、规则配置和工作量计算。",
        helper: "遇到未匹配项时先修正，再执行计算和导出。",
        icon: Histogram,
        tags: ["课表导入", "映射修正", "工作量"],
      },
      {
        path: "/evaluation-quant",
        label: "评教量化",
        description: "维护评教模板、批次导入和班主任量化汇总。",
        helper: "先确认学期、模板和规则版本，再导入批次或录入量化数据。",
        icon: Tickets,
        tags: ["评教模板", "量化规则", "批次汇总"],
      },
    ],
  },
  {
    id: "decision",
    title: "决策输出",
    summary: "基于已有数据输出推荐和报表。",
    items: [
      {
        path: "/gaokao-data",
        label: "高考数据",
        description: "查看高考数据来源、缺口、审阅队列、证据链和山东覆盖情况。",
        helper: "这里是只读看板，用来判断当前数据能支持哪些使用场景，不直接修改底层数据。",
        icon: DataAnalysis,
        tags: ["数据来源", "只读看板", "山东覆盖"],
      },
      {
        path: "/gaokao-pathways",
        label: "升学方案",
        description: "按学生画像查看山东多路径初筛、材料缺口和人工复核事项。",
        helper: "先补齐学生画像和资格材料，再进入普通类推荐或逐校核对。",
        icon: School,
        tags: ["山东路径", "材料缺口", "人工复核"],
      },
      {
        path: "/recommendations",
        label: "高考志愿",
        description: "维护招生计划、录取库和省份规则，生成志愿推荐方案。",
        helper: "志愿推荐前请先确认考试、位次、招生计划和省份规则是否完整。",
        icon: School,
        tags: ["招生计划", "录取库", "志愿规则"],
      },
      {
        path: "/reports",
        label: "报表中心",
        description: "统一导出学生、分析、工作量、推荐和评教报表。",
        helper: "报表导出前建议回源页面复核关键数据。",
        icon: Document,
        tags: ["统一导出", "汇总材料", "结果复核"],
      },
      {
        path: "/system-tools",
        label: "系统设置",
        description: "管理参数、模板、修复工具、备份和恢复。",
        helper: "执行修复、恢复或批量调整前，建议先创建备份。",
        icon: Setting,
        tags: ["参数配置", "修复工具", "备份恢复"],
      },
    ],
  },
];

export const flatNavItems: ResolvedAppNavItem[] = navSections.flatMap((section) =>
  section.items.map((item) => ({
    ...item,
    sectionId: section.id,
    sectionTitle: section.title,
    sectionSummary: section.summary,
  })),
);

export function resolveNavItem(path: string): ResolvedAppNavItem {
  const exactMatch = flatNavItems.find((item) => item.path === path);
  if (exactMatch) return exactMatch;

  const prefixMatch = flatNavItems.find((item) =>
    item.matchPrefixes?.some((prefix) => path.startsWith(prefix)),
  );
  return prefixMatch ?? flatNavItems[0];
}
