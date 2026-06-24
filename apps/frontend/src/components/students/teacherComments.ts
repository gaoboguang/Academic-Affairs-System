export interface TeacherCommentDraft {
  subjectId?: number | null;
  content: string;
}

export interface TeacherCommentRequest {
  subject_id: number | null;
  content: string;
}

export interface TeacherCommentMetaSource {
  teacher_name?: string | null;
  subject_name?: string | null;
  class_name?: string | null;
  semester_name?: string | null;
  commented_at?: string | null;
}

export function buildTeacherCommentRequest(
  draft: TeacherCommentDraft,
): TeacherCommentRequest | null {
  const content = draft.content.trim();
  if (!content) return null;
  return {
    subject_id: draft.subjectId ?? null,
    content,
  };
}

export function formatTeacherCommentDate(value?: string | null): string | null {
  if (!value) return null;
  const normalized = value.replace("T", " ");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

export function buildTeacherCommentMeta(comment: TeacherCommentMetaSource): string[] {
  return [
    comment.teacher_name,
    comment.subject_name,
    comment.class_name,
    comment.semester_name,
    formatTeacherCommentDate(comment.commented_at),
  ].flatMap((item) => (item ? [item] : []));
}
