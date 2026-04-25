export function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }
  if (typeof error === "string" && error.trim()) {
    return error.trim();
  }
  return "系统暂时没有返回具体原因";
}

export function formatUserActionError(action: string, error: unknown, nextStep: string): string {
  const reason = getErrorMessage(error).replace(/^请求失败:\s*/u, "本地服务返回异常：");
  return `${action}失败。原因：${reason}。建议：${nextStep}`;
}
