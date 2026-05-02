import type { Component } from "vue";

export type UiTone = "primary" | "success" | "warning" | "danger" | "info" | "neutral";

export interface StatCardItem {
  label: string;
  value: string | number;
  help?: string;
  suffix?: string;
  tone?: UiTone;
  loading?: boolean;
}

export interface FilterAction {
  label: string;
  type?: "primary" | "success" | "warning" | "danger" | "info";
  plain?: boolean;
  disabled?: boolean;
  loading?: boolean;
  handler: () => void | Promise<void>;
}

export interface TableAction {
  label: string;
  tone?: UiTone;
  route?: string;
  disabled?: boolean;
  onClick?: () => void | Promise<void>;
}

export interface PrintSummaryCard {
  title: string;
  value: string | number;
  description?: string;
  tone?: UiTone;
}

export interface PageMetaItem {
  label: string;
  value: string | number;
  icon?: Component;
}
