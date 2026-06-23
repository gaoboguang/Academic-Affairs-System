import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";
import { canAccessPermission } from "../layouts/navigation";
import { useAuthStore } from "../stores/auth";

const LoginPage = () => import("../pages/LoginPage.vue");
const ChangePasswordPage = () => import("../pages/ChangePasswordPage.vue");
const ForbiddenPage = () => import("../pages/ForbiddenPage.vue");
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
const CollegesPage = () => import("../pages/CollegesPage.vue");
const CollegeDetailPage = () => import("../pages/CollegeDetailPage.vue");
const MajorDetailPage = () => import("../pages/MajorDetailPage.vue");
const SystemToolsPage = () => import("../pages/SystemToolsPage.vue");
const AccountManagementPage = () => import("../pages/AccountManagementPage.vue");
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
      path: "/login",
      name: "login",
      component: LoginPage,
      meta: { public: true },
    },
    {
      path: "/change-password",
      name: "change-password",
      component: ChangePasswordPage,
    },
    {
      path: "/forbidden",
      name: "forbidden",
      component: ForbiddenPage,
    },
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
          meta: { permission: "dashboard:read" },
        },
        {
          path: "base-data",
          name: "base-data",
          component: BaseDataPage,
          meta: { permission: "base:manage" },
        },
        {
          path: "classes",
          name: "classes",
          component: ClassesOverviewPage,
          meta: { permission: "base:manage" },
        },
        {
          path: "classes/:classId",
          name: "class-detail",
          component: ClassDetailPage,
          meta: { permission: "base:manage" },
        },
        {
          path: "grades/:gradeId",
          name: "grade-detail",
          component: GradeDetailPage,
          meta: { permission: "base:manage" },
        },
        {
          path: "students",
          name: "students",
          component: StudentsPage,
          meta: { permission: "students:read" },
        },
        {
          path: "students/:studentId",
          name: "student-detail",
          component: StudentDetailPage,
          meta: { permission: "students:read" },
        },
        {
          path: "growth-archive",
          name: "growth-archive",
          component: GrowthArchivePage,
          meta: { permission: "students:write" },
        },
        {
          path: "teachers",
          name: "teachers",
          component: TeachersPage,
          meta: { permission: "teachers:manage" },
        },
        {
          path: "teachers/:teacherId",
          name: "teacher-detail",
          component: TeacherDetailPage,
          meta: { permission: "teachers:manage" },
        },
        {
          path: "exams",
          name: "exams",
          component: ExamsPage,
          meta: { permission: "scores:import" },
        },
        {
          path: "analytics",
          name: "analytics",
          component: AnalyticsPage,
          meta: { permission: "analytics:read" },
        },
        {
          path: "knowledge-base",
          name: "knowledge-base",
          component: KnowledgeBasePage,
          meta: { permission: "base:manage" },
        },
        {
          path: "import-center",
          name: "import-center",
          component: ImportCenterPage,
          meta: { permission: "scores:import" },
        },
        {
          path: "gaokao-data",
          name: "gaokao-data",
          component: GaokaoDataPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "gaokao-pathways",
          name: "gaokao-pathways",
          component: GaokaoPathwaysPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "workload",
          name: "workload",
          component: TimetableWorkloadPage,
          meta: { permission: "teachers:manage" },
        },
        {
          path: "evaluation-quant",
          name: "evaluation-quant",
          component: EvaluationQuantPage,
          meta: { permission: "teachers:manage" },
        },
        {
          path: "reports",
          name: "reports",
          component: ReportsPage,
          meta: { permission: "reports:read" },
        },
        {
          path: "recommendations",
          name: "recommendations",
          component: RecommendationsPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "colleges",
          name: "colleges",
          component: CollegesPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "colleges/:collegeId",
          name: "college-detail",
          component: CollegeDetailPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "majors/:majorId",
          name: "major-detail",
          component: MajorDetailPage,
          meta: { permission: "admin:*" },
        },
        {
          path: "admin/users",
          name: "admin-users",
          component: AccountManagementPage,
          meta: { permission: "accounts:manage" },
        },
        {
          path: "system-tools",
          name: "system-tools",
          component: SystemToolsPage,
          meta: { permission: "system:manage" },
        },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.initialized) {
    await auth.fetchCurrentUser();
  }

  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === "login") {
      return "/";
    }
    return true;
  }

  if (!auth.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (auth.mustChangePassword && to.name !== "change-password") {
    return { name: "change-password" };
  }

  const permission = typeof to.meta.permission === "string" ? to.meta.permission : undefined;
  if (!canAccessPermission(auth.permissions, permission) && to.name !== "forbidden") {
    return { name: "forbidden" };
  }

  return true;
});

export default router;
