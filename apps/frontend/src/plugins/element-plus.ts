import type { App, Component } from "vue";
import ElAlert from "element-plus/es/components/alert/index";
import ElAutocomplete from "element-plus/es/components/autocomplete/index";
import ElButton from "element-plus/es/components/button/index";
import ElDatePicker from "element-plus/es/components/date-picker/index";
import ElDialog from "element-plus/es/components/dialog/index";
import ElDrawer from "element-plus/es/components/drawer/index";
import ElEmpty from "element-plus/es/components/empty/index";
import { ElForm, ElFormItem } from "element-plus/es/components/form/index";
import ElInput from "element-plus/es/components/input/index";
import ElInputNumber from "element-plus/es/components/input-number/index";
import { ElMenu, ElMenuItem } from "element-plus/es/components/menu/index";
import ElPagination from "element-plus/es/components/pagination/index";
import { ElRadioButton, ElRadioGroup } from "element-plus/es/components/radio/index";
import { ElOption, ElSelect } from "element-plus/es/components/select/index";
import ElSwitch from "element-plus/es/components/switch/index";
import { ElTabPane, ElTabs } from "element-plus/es/components/tabs/index";
import { ElTable, ElTableColumn } from "element-plus/es/components/table/index";
import ElTag from "element-plus/es/components/tag/index";
import ElUpload from "element-plus/es/components/upload/index";

const components: Component[] = [
  ElAlert,
  ElAutocomplete,
  ElButton,
  ElDatePicker,
  ElDialog,
  ElDrawer,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElRadioButton,
  ElRadioGroup,
  ElSelect,
  ElSwitch,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag,
  ElUpload,
];

export function installElementPlus(app: App): void {
  for (const component of components) {
    app.component((component as { name: string }).name, component);
  }
}
