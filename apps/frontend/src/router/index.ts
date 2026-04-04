import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";

const DashboardPage = () => import("../pages/DashboardPage.vue");
const BaseDataPage = () => import("../pages/BaseDataPage.vue");
const StudentsPage = () => import("../pages/StudentsPage.vue");
const StudentDetailPage = () => import("../pages/StudentDetailPage.vue");
const GrowthArchivePage = () => import("../pages/GrowthArchivePage.vue");
const TeachersPage = () => import("../pages/TeachersPage.vue");
const TeacherDetailPage = () => import("../pages/TeacherDetailPage.vue");
const ExamsPage = () => import("../pages/ExamsPage.vue");
const AnalyticsPage = () => import("../pages/AnalyticsPage.vue");
const TimetableWorkloadPage = () => import("../pages/TimetableWorkloadPage.vue");
const EvaluationQuantPage = () => import("../pages/EvaluationQuantPage.vue");
const ReportsPage = () => import("../pages/ReportsPage.vue");
const RecommendationsPage = () => import("../pages/RecommendationsPage.vue");
const SystemToolsPage = () => import("../pages/SystemToolsPage.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
          path: "system-tools",
          name: "system-tools",
          component: SystemToolsPage,
        },
      ],
    },
  ],
});

export default router;
