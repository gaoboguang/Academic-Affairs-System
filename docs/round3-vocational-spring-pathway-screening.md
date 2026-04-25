# 第三轮 D6 单招、综评、春考路径初筛

- 日期：2026-04-25
- 范围：窗口 D6，高职单招、高职综合评价、春季高考本科/专科路径初筛
- 后端入口：`apps/backend/app/services/gaokao_pathways.py`
- 前端入口：学生详情页“升学画像”、`/gaokao-pathways`
- 本地装载命令：`npm run backend:bootstrap-pathways -- --target-year 2026`

## 目标

D6 在 D1-D5 已有路径表、官方来源、学生画像、方案中心和普通类推荐加固基础上，细化高职单招、高职综合评价招生、春季高考本科/专科的资格初筛。

本轮继续保持边界：这些路径只输出资格初筛、材料缺口和人工复核清单，不输出录取概率，不把 2026 未导入的分专业计划、分数线或高校章程当成已确认数据。

## 本轮完成

- 后端规则引擎新增 `material_present_when` 条件，用于“只有社会人员才要求高中阶段毕业证书或同等学力材料”等条件式材料规则，避免中职学生被误提示社会人员材料。
- 高职单招路径补充：
  - 中职应届、社会人员等身份确认。
  - 社会人员同等学力材料按条件提示。
  - 目标专业类别、职业技能测试或适应性测试匹配材料。
  - 退役士兵测试方式人工复核提示。
  - 院校章程和分专业计划缺失时的人工核验材料项。
- 高职综合评价路径补充：
  - 高考报名确认。
  - 普通高中应届身份。
  - 综合素质评价材料。
  - 素质测试或面试安排。
  - 院校章程和分专业计划缺失时的人工核验材料项。
- 春季高考本科/专科路径补充：
  - 春季高考报名和考生类型确认。
  - 春考专业类别一致性。
  - 知识与技能考试成绩。
  - 对应专业类别分数线。
  - 春考分专业计划和院校章程缺失时的人工核验材料项。
- 前端学生画像材料清单新增 D6 材料项；方案中心路径卡新增 D6 关键要求提示，明确报名、身份、材料、类别匹配和人工复核边界。
- 真实 `data/app.db` 已运行 D6 bootstrap，写入前备份为 `data/backups/app_before_pathway_bootstrap_2026_20260425_02.db`；本次新增规则 `14` 条，已有规则 `48` 条被跳过/更新。

## 官方来源口径

D6 继续复用 D2 已登记的官方来源：

- 山东省教育厅《2026年高职（专科）单独考试招生和综合评价招生工作的通知》。
- 山东省教育招生考试院《山东省春季高考统一考试招生专业类别考试标准（2026年版）》。
- 山东省教育招生考试院 2026 普通高校招生考试报名通知。

这些来源只用于路径规则、材料提醒和人工复核清单，不代表目标院校 2026 分专业计划、测试细则或招生章程已全部结构化导入。

## 页面读法

- `高职单独招生`：先看学生是否为中职应届或社会人员等可关注对象，再核对高考报名、专业类别/技能测试、院校章程、分专业计划和退役士兵专项规则。
- `高职综合评价招生`：先看是否为普通高中应届并已完成高考报名，再核对综合素质评价、素质测试或面试安排、院校章程和分专业计划。
- `春季高考本科/专科`：先看是否为春季高考考生，并补齐专业类别、知识与技能考试成绩、类别分数线、分专业计划和院校章程。
- 这些路径出现 `信息不足` 或 `需人工复核` 是正常状态，表示还要补事实或查章程，不表示学生一定不能走该路径。

## 验证

本轮推荐验证：

```bash
npm run backend:test -- apps/backend/tests/test_gaokao_pathways.py -q
npm run frontend:test -- tests/pathway-center.test.ts tests/student-pathway-profile.test.ts
npm run frontend:test
npm run frontend:build
git diff --check
```

当前已完成验证：

- `npm run backend:test -- apps/backend/tests/test_gaokao_pathways.py -q`：`5 passed`
- `npm run frontend:test -- tests/pathway-center.test.ts tests/student-pathway-profile.test.ts`：`11 passed`
- `npm run backend:test -- apps/backend/tests -q`：`92 passed`
- `npm run frontend:test`：`25 files / 145 tests passed`
- `npm run frontend:build`：通过
- `git diff --check`：通过
