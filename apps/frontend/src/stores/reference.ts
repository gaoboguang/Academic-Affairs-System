import { defineStore } from "pinia";

import { apiRequest } from "../api/client";

export interface OptionItem {
  id: number;
  code?: string;
  name: string;
  [key: string]: any;
}

function deferredPromise<T>(): {
  promise: Promise<T>;
  resolve: (value: T | PromiseLike<T>) => void;
  reject: (reason?: unknown) => void;
} {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

interface ReferenceLoadOptions {
  force?: boolean;
}

interface ReferenceState {
  academicYears: OptionItem[];
  semesters: OptionItem[];
  grades: OptionItem[];
  classes: OptionItem[];
  subjects: OptionItem[];
  dicts: Record<string, OptionItem[]>;
  loading: boolean;
  coreLoaded: boolean;
  coreLoadPromise: Promise<void> | null;
  dictLoadPromises: Record<string, Promise<void> | undefined>;
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
    coreLoaded: false,
    coreLoadPromise: null,
    dictLoadPromises: {},
  }),
  actions: {
    async loadCore(options: ReferenceLoadOptions = {}): Promise<void> {
      if (this.coreLoaded && !options.force) return;
      if (this.coreLoadPromise && !options.force) return this.coreLoadPromise;

      this.loading = true;
      const { promise, resolve, reject } = deferredPromise<void>();
      this.coreLoadPromise = promise;
      void (async () => {
        try {
          const [academicYears, semesters, grades, classes, subjects] = await Promise.all([
            apiRequest<OptionItem[]>("/api/base/academic-years"),
            apiRequest<OptionItem[]>("/api/base/semesters"),
            apiRequest<OptionItem[]>("/api/base/grades"),
            apiRequest<OptionItem[]>("/api/base/classes"),
            apiRequest<OptionItem[]>("/api/base/subjects"),
          ]);
          if (this.coreLoadPromise !== promise) {
            resolve();
            return;
          }
          this.academicYears = academicYears;
          this.semesters = semesters;
          this.grades = grades;
          this.classes = classes;
          this.subjects = subjects;
          this.coreLoaded = true;
          resolve();
        } catch (error) {
          reject(error);
        } finally {
          if (this.coreLoadPromise === promise) {
            this.loading = false;
            this.coreLoadPromise = null;
          }
        }
      })();
      return promise;
    },
    async loadDict(dictCode: string, options: ReferenceLoadOptions = {}): Promise<void> {
      if (this.dicts[dictCode] && !options.force) return;
      const existingPromise = this.dictLoadPromises[dictCode];
      if (existingPromise && !options.force) return existingPromise;

      const { promise, resolve, reject } = deferredPromise<void>();
      this.dictLoadPromises[dictCode] = promise;
      void (async () => {
        try {
          const items = await apiRequest<OptionItem[]>(`/api/base/dict-types/${dictCode}/items`);
          if (this.dictLoadPromises[dictCode] !== promise) {
            resolve();
            return;
          }
          this.dicts[dictCode] = items;
          resolve();
        } catch (error) {
          reject(error);
        } finally {
          if (this.dictLoadPromises[dictCode] === promise) {
            this.dictLoadPromises[dictCode] = undefined;
          }
        }
      })();
      return promise;
    },
    async loadAll(options: ReferenceLoadOptions = {}): Promise<void> {
      await this.loadCore(options);
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
        ].map((dictCode) => this.loadDict(dictCode, options)),
      );
    },
  },
});
