import { defineStore } from "pinia";

import { apiRequest } from "../api/client";

export interface OptionItem {
  id: number;
  code?: string;
  name: string;
  [key: string]: any;
}

interface ReferenceState {
  academicYears: OptionItem[];
  semesters: OptionItem[];
  grades: OptionItem[];
  classes: OptionItem[];
  subjects: OptionItem[];
  dicts: Record<string, OptionItem[]>;
  loading: boolean;
}

export const useReferenceStore = defineStore("reference", {
  state: (): ReferenceState => ({
    academicYears: [],
    semesters: [],
    grades: [],
    classes: [],
    subjects: [],
    dicts: {},
    loading: false,
  }),
  actions: {
    async loadCore(): Promise<void> {
      this.loading = true;
      try {
        const [academicYears, semesters, grades, classes, subjects] = await Promise.all([
          apiRequest<OptionItem[]>("/api/base/academic-years"),
          apiRequest<OptionItem[]>("/api/base/semesters"),
          apiRequest<OptionItem[]>("/api/base/grades"),
          apiRequest<OptionItem[]>("/api/base/classes"),
          apiRequest<OptionItem[]>("/api/base/subjects"),
        ]);
        this.academicYears = academicYears;
        this.semesters = semesters;
        this.grades = grades;
        this.classes = classes;
        this.subjects = subjects;
      } finally {
        this.loading = false;
      }
    },
    async loadDict(dictCode: string): Promise<void> {
      const items = await apiRequest<OptionItem[]>(`/api/base/dict-types/${dictCode}/items`);
      this.dicts[dictCode] = items;
    },
    async loadAll(): Promise<void> {
      await this.loadCore();
      await Promise.all(
        [
          "student_status",
          "student_type",
          "art_track",
          "teacher_title",
          "teacher_position",
          "teacher_status",
          "course_type",
          "class_type",
        ].map((dictCode) => this.loadDict(dictCode)),
      );
    },
  },
});
