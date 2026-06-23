import { describe, expect, it } from "vitest";

import {
  buildTeacherCommentMeta,
  buildTeacherCommentRequest,
} from "../src/components/students/teacherComments";

describe("student teacher comment helpers", () => {
  it("trims comment content before submitting", () => {
    expect(buildTeacherCommentRequest({ subjectId: 1, content: "  课堂发言积极  " })).toEqual({
      subject_id: 1,
      content: "课堂发言积极",
    });
  });

  it("blocks empty comment content", () => {
    expect(buildTeacherCommentRequest({ subjectId: 1, content: "   " })).toBeNull();
  });

  it("builds compact metadata for comment cards", () => {
    expect(
      buildTeacherCommentMeta({
        teacher_name: "李语文",
        subject_name: "语文",
        class_name: "1班",
        semester_name: "下学期",
        commented_at: "2026-06-01T08:30:00",
      }),
    ).toEqual(["李语文", "语文", "1班", "下学期", "2026-06-01 08:30"]);
  });
});
