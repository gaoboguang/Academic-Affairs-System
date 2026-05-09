import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";

const DashboardPage = () => import("../pages/DashboardPage.vue");
const BaseDataPage = () => import("../pages/BaseDataPage.vue");
const ClassesOverviewPage = () => import("../pages/ClassesOverviewPage.vue");
const ClassDetailPage = () => import("../pages/ClassDetailPage.vue");
const GradeDetailPage = () => import("../pages/GradeDetailPage.vue");
const StudentsPage = () => import("../pages/StudentsPage.vue");
const StudentDetailPage = () => import("../pages/StudentDetailPage.vue");
const GrowthArchivePage = () => import("../pages/GrowthArchivePage.vue");
const TeachersPage = () => import("../pages/TeachersPage.vue");
const TeacherDetailPage = () => import("../pages/TeacherDetailPage.vue");
const ExamsPage = () => import("../pages/ExamsPage.vue");
const AnalyticsPage = () => import("../pages/AnalyticsPage.vue");
const KnowledgeBasePage = () => import("../pages/KnowledgeBasePage.vue");
const ImportCenterPage = () => import("../pages/ImportCenterPage.vue");
const GaokaoDataPage = () => import("../pages/GaokaoDataPage.vue");
const GaokaoPathwaysPage = () => import("../pages/GaokaoPathwaysPage.vue");
const TimetableWorkloadPage = () => import("../pages/TimetableWorkloadPage.vue");
const EvaluationQuantPage = () => import("../pages/EvaluationQuantPage.vue");
const ReportsPage = () => import("../pages/ReportsPage.vue");
const RecommendationsPage = () => import("../pages/RecommendationsPage.vue");
const CollegeDetailPage = () => import("../pages/CollegeDetailPage.vue");
const MajorDetailPage = () => import("../pages/MajorDetailPage.vue");
const SystemToolsPage = () => import("../pages/SystemToolsPage.vue");
const RecommendationPrintPage = () => import("../pages/RecommendationPrintPage.vue");
const ShandongRecommendationPrintPage = () => import("../pages/ShandongRecommendationPrintPage.vue");
const GaokaoPathwayReportPrintPage = () => import("../pages/GaokaoPathwayReportPrintPage.vue");
const GaokaoDataCoveragePrintPage = () => import("../pages/GaokaoDataCoveragePrintPage.vue");
const GrowthSummaryPrintPage = () => import("../pages/GrowthSummaryPrintPage.vue");
const StudentAnalysisPrintPage = () => import("../pages/StudentAnalysisPrintPage.vue");
const StudentKnowledgePrintPage = () => import("../pages/StudentKnowledgePrintPage.vue");
const ClassAnalysisPrintPage = () => import("../pages/ClassAnalysisPrintPage.vue");
const ClassKnowledgeBriefingPrintPage = () => import("../pages/ClassKnowledgeBriefingPrintPage.vue");
const GradeSummaryPrintPage = () => import("../pages/GradeSummaryPrintPage.vue");
const TeacherAnalysisPrintPage = () => import("../pages/TeacherAnalysisPrintPage.vue");
const WorkloadPrintPage = () => import("../pages/WorkloadPrintPage.vue");
const EvaluationSummaryPrintPage = () => import("../pages/EvaluationSummaryPrintPage.vue");
const AdviserQuantPrintPage = () => import("../pages/AdviserQuantPrintPage.vue");
const AdviserWeeklySummaryPrintPage = () => import("../pages/AdviserWeeklySummaryPrintPage.vue");
const StudentFollowupPackagePrintPage = () => import("../pages/StudentFollowupPackagePrintPage.vue");
const PlanningFollowupPrintPage = () => import("../pages/PlanningFollowupPrintPage.vue");
const VolunteerDraftPrintPage = () => import("../pages/VolunteerDraftPrintPage.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/print/recommendations/:studentId/:schemeId",
      name: "recommendation-print",
      component: RecommendationPrintPage,
    },
    {
      path: "/print/shandong-recommendation/:storageKey",
      name: "shandong-recommendation-print",
      component: ShandongRecommendationPrintPage,
    },
    {
      path: "/print/gaokao-pathway-report/:storageKey",
      name: "gaokao-pathway-report-print",
      component: GaokaoPathwayReportPrintPage,
    },
    {
      path: "/print/gaokao-data-coverage/:storageKey",
      name: "gaokao-data-coverage-print",
      component: GaokaoDataCoveragePrintPage,
    },
    {
      path: "/print/student-analysis/:studentId/:examId",
      name: "student-analysis-print",
      component: StudentAnalysisPrintPage,
    },
    {
      path: "/print/student-knowledge/:studentId/:examId",
      name: "student-knowledge-print",
      component: StudentKnowledgePrintPage,
    },
    {
      path: "/print/class-analysis/:classId/:examId",
      name: "class-analysis-print",
      component: ClassAnalysisPrintPage,
    },
    {
      path: "/print/class-knowledge-briefing/:classId/:examId",
      name: "class-knowledge-briefing-print",
      component: ClassKnowledgeBriefingPrintPage,
    },
    {
      path: "/print/grade-summary/:gradeId/:examId",
      name: "grade-summary-print",
      component: GradeSummaryPrintPage,
    },
    {
      path: "/print/teacher-analysis/:teacherId/:examId",
      name: "teacher-analysis-print",
      component: TeacherAnalysisPrintPage,
    },
    {
      path: "/print/workload/:semesterId",
      name: "workload-print",
      component: WorkloadPrintPage,
    },
    {
      path: "/print/evaluation-summary/:batchId",
      name: "evaluation-summary-print",
      component: EvaluationSummaryPrintPage,
    },
    {
      path: "/print/adviser-quant/:semesterId",
      name: "adviser-quant-print",
      component: AdviserQuantPrintPage,
    },
    {
      path: "/print/adviser-weekly-summary/:classId",
      name: "adviser-weekly-summary-print",
      component: AdviserWeeklySummaryPrintPage,
    },
    {
      path: "/print/student-followup-package/:studentId",
      name: "student-followup-package-print",
      component: StudentFollowupPackagePrintPage,
    },
    {
      path: "/print/planning-followup/:studentId",
      name: "planning-followup-print",
      component: PlanningFollowupPrintPage,
    },
    {
      path: "/print/growth-summary/:studentId",
      name: "growth-summary-print",
      component: GrowthSummaryPrintPage,
    },
    {
      path: "/print/volunteer-drafts/:draftId",
      name: "volunteer-draft-print",
      component: VolunteerDraftPrintPage,
    },
    {
      path: "/",
      component: AppLayout,
      children: [
        {
          path: "",
          name: "dashboard",
          component: DashboardPage,
        },
        {
          path: "base-data",
          name: "base-data",
          component: BaseDataPage,
        },
        {
          path: "classes",
          name: "classes",
          component: ClassesOverviewPage,
        },
        {
          path: "classes/:classId",
          name: "class-detail",
          component: ClassDetailPage,
        },
        {
          path: "grades/:gradeId",
          name: "grade-detail",
          component: GradeDetailPage,
        },
        {
          path: "students",
          name: "students",
          component: StudentsPage,
        },
        {
          path: "students/:studentId",
          name: "student-detail",
          component: StudentDetailPage,
        },
        {
          path: "growth-archive",
          name: "growth-archive",
          component: GrowthArchivePage,
        },
        {
          path: "teachers",
          name: "teachers",
          component: TeachersPage,
        },
        {
          path: "teachers/:teacherId",
          name: "teacher-detail",
          component: TeacherDetailPage,
        },
        {
          path: "exams",
          name: "exams",
          component: ExamsPage,
        },
        {
          path: "analytics",
          name: "analytics",
          component: AnalyticsPage,
        },
        {
          path: "knowledge-base",
          name: "knowledge-base",
          component: KnowledgeBasePage,
        },
        {
          path: "import-center",
          name: "import-center",
          component: ImportCenterPage,
        },
        {
          path: "gaokao-data",
          name: "gaokao-data",
          component: GaokaoDataPage,
        },
        {
          path: "gaokao-pathways",
          name: "gaokao-pathways",
          component: GaokaoPathwaysPage,
        },
        {
          path: "workload",
          name: "workload",
          component: TimetableWorkloadPage,
        },
        {
          path: "evaluation-quant",
          name: "evaluation-quant",
          component: EvaluationQuantPage,
        },
        {
          path: "reports",
          name: "reports",
          component: ReportsPage,
        },
        {
          path: "recommendations",
          name: "recommendations",
          component: RecommendationsPage,
        },
        {
          path: "colleges/:collegeId",
          name: "college-detail",
          component: CollegeDetailPage,
        },
        {
          path: "majors/:majorId",
          name: "major-detail",
          component: MajorDetailPage,
        },
        {
          path: "system-tools",
          name: "system-tools",
          component: SystemToolsPage,
        },
      ],
    },
  ],
});

export default router;
