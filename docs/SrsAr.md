# وثيقة المتطلبات الشاملة SRS

## نظام إدارة المعاملات والمراسلات الإدارية على Frappe 16 وERPNext 16

**اسم التطبيق المقترح:** `aamali_correspondence`  
**اسم الوحدة داخل النظام:** `Aamali Correspondence`  
**الاسم العربي:** نظام المعاملات والمراسلات الإدارية  
**إصدار الوثيقة:** 1.0  
**حالة الوثيقة:** خط أساس تنفيذي Baseline  
**المنصة المستهدفة:** Frappe Framework v16 + ERPNext v16

> أظهرت صفحات الإصدارات وقت إعداد هذه الوثيقة إصدار Frappe v16.33.0 وإصدار ERPNext v16.34.1، لكن يجب تثبيت زوج إصدارات متوافق واختباره في بيئة تجريبية قبل الإنتاج، بدل تحديث كل منتج مستقلًا بصورة تلقائية.  
> [Frappe Releases](https://github.com/frappe/frappe/releases) — [ERPNext Releases](https://github.com/frappe/erpnext/releases)

---

# 1. الغرض من النظام

إنشاء تطبيق مخصص يعمل فوق Frappe وERPNext لإدارة:

- المعاملات الداخلية.
- المعاملات الواردة الخارجية.
- المعاملات الصادرة الخارجية.
- الخطابات الإلكترونية.
- المسودات.
- الإحالات الفردية والمتعددة.
- الاستلام والرفض والإعادة والسحب.
- التوجيهات والتأشيرات.
- الموافقات والتوقيعات.
- الردود.
- الوثائق والمرفقات العادية والسرية.
- المسح الضوئي.
- الباركود وQR.
- المعاملات الورقية.
- بيانات التسليم.
- التتبع الكامل.
- البحث المتقدم.
- المجلدات الشخصية.
- التفويضات.
- الإحصائيات والتقارير.
- المهام واللجان والاجتماعات.

النظام الجديد سيحاكي **المنطق الوظيفي** المستخلص من صور نظام أعمالي، لكنه سيُبنى بطريقة أصلية ومتوافقة مع بنية Frappe، ولن يكون نسخًا برمجيًا أو تقنيًا للنظام الأصلي.

---

# 2. أهداف المشروع

1. رقمنة دورة المعاملة من الإنشاء حتى الإغلاق والأرشفة.
2. توحيد الوارد والصادر والداخلي ضمن سجل مركزي.
3. تقليل تداول الملفات الورقية.
4. معرفة الجهة الحائزة للمعاملة في أي وقت.
5. تسجيل جميع الإحالات والإجراءات في سجل غير قابل للتلاعب العادي.
6. دعم السرية على مستوى المعاملة والمستند والإحالة.
7. مراقبة مواعيد الاستحقاق والتأخير.
8. دعم التقويم الميلادي والهجري في الواجهة.
9. ربط المعاملات ببعضها.
10. استخراج مؤشرات إنتاجية الموظفين والإدارات.
11. التكامل مع بيانات الموظفين والإدارات في ERPNext.
12. توفير REST API للتكاملات المصرح بها.
13. توفير واجهة عربية RTL متجاوبة.
14. دعم تعدد الشركات أو الجهات عند الحاجة.

---

# 3. حدود النظام

## 3.1 داخل النطاق

- التسجيل الداخلي والوارد والصادر.
- معالج تسجيل من ثلاث خطوات:
    1. البيانات.
    2. المرفقات.
    3. الإحالة.
- صندوق المعاملات.
- البحث.
- التتبع.
- المجلدات.
- التفويضات.
- التقارير.
- بيانات التسليم.
- الإحصائيات.
- إدارة المهام.
- اللجان والاجتماعات.
- الإشعارات.
- الباركود وQR.
- صلاحيات حسب المستخدم والإدارة والسرية.
- API للتكامل.
- الأرشفة وسياسة الاحتفاظ.
- التدقيق Audit.

## 3.2 خارج النطاق الأساسي

لا تُعد العناصر التالية جزءًا إلزاميًا من الإصدار الأول، لكنها قابلة للإضافة:

- توقيع رقمي وطني موثّق قانونيًا ما لم يتوفر مزود معتمد.
- الربط مع مراسلات حكومية خارجية قبل توفر API رسمي.
- التعرف الضوئي OCR المتقدم.
- تطبيق جوال Native مستقل.
- إرسال ورقي فعلي عبر شركة شحن.
- ذكاء اصطناعي لتصنيف الخطابات.
- تحويل البريد الإلكتروني الوارد إلى معاملة تلقائيًا.
- تكامل Active Directory أو Entra ID ما لم تتوفر بياناته.

---

# 4. الأساس التقني على Frappe

سيستفيد التطبيق من مكونات Frappe التالية:

- DocTypes والنماذج والقوائم.
- Role Permissions.
- User Permissions.
- Workflow.
- Notifications.
- Assignments وToDo عند الحاجة.
- File وPrivate File.
- Print Formats.
- Query Reports وScript Reports.
- Background Jobs.
- REST API.
- Realtime Events.
- Version Tracking.
- Workspace.
- Translation وRTL.

يوفّر Frappe واجهات REST تلقائية للـDocTypes، ويدعم المصادقة بالرمز أو الجلسة، كما يدعم الأحداث الفورية عبر [Socket.IO](http://socket.io/). لكنه لا يحقق تلقائيًا كل قواعد السرية المطلوبة؛ لذلك يجب إضافة منطق صلاحيات مخصص للمعاملات والمرفقات السرية.  
[REST API](https://docs.frappe.io/framework/user/en/api/rest) — [Realtime API](https://docs.frappe.io/framework/user/en/api/realtime) — [Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions)

---

# 5. المصطلحات

|المصطلح|التعريف|
|---|---|
|المعاملة|السجل الإداري الرئيسي الذي يجمع البيانات والوثائق والإحالات|
|معاملة داخلية|مراسلة بين إدارات أو مستخدمي الجهة|
|واردة خارجية|خطاب وصل من جهة خارجية|
|صادرة خارجية|خطاب صادر من الجهة إلى طرف خارجي|
|الخطاب الرئيسي|المستند الأساسي للمعاملة|
|الرد|خطاب أُنشئ ردًا على معاملة سابقة|
|الإحالة|توجيه المعاملة من مستخدم أو إدارة إلى مستلم آخر|
|الأصل|الإحالة الأساسية التي تمنح مسؤولية الإجراء|
|صورة|نسخة للاطلاع لا تنقل ملكية الإجراء الأساسية|
|للمتابعة|إحالة لمراقبة التنفيذ|
|خاص|إحالة مقيدة بالمستلم المحدد|
|مراسلة ورقية|وجود نسخة أو أصل ورقي يحتاج إلى متابعة|
|التأشيرة|توجيه أو تعليمات إدارية مرتبطة بالإحالة|
|الاستحقاق|التاريخ المطلوب لإكمال الإجراء|
|الاستلام|إقرار المستلم باستلام الإحالة|
|السحب|استرجاع إحالة مرسلة وفق شروط محددة|
|إعادة التشغيل|إعادة فتح معاملة مغلقة|
|التسديد|إنهاء الإجراء على الإحالة مع توثيق النتيجة|
|الإغلاق|إنهاء دورة المعاملة|
|الجهة الحائزة|الإدارة أو المستخدم المسؤول حاليًا عن المعاملة|

---

# 6. الأدوار Roles

## 6.1 أدوار النظام

|Role|الوظيفة|
|---|---|
|`ACM User`|مستخدم معاملات عادي|
|`ACM Correspondence Clerk`|موظف اتصالات إدارية|
|`ACM Incoming Clerk`|تسجيل الوارد|
|`ACM Outgoing Clerk`|تسجيل الصادر|
|`ACM Scanner Operator`|المسح والرفع|
|`ACM Department Coordinator`|منسق معاملات الإدارة|
|`ACM Department Manager`|مدير الإدارة|
|`ACM Approver`|اعتماد الخطابات|
|`ACM Signatory`|توقيع الخطابات|
|`ACM Follow Up Officer`|متابعة المعاملات|
|`ACM Delivery Officer`|إدارة التسليم|
|`ACM Confidential User`|الاطلاع على السرية المصرح بها|
|`ACM Records Manager`|الأرشفة والاحتفاظ|
|`ACM Reports User`|التقارير المسموح بها|
|`ACM Auditor`|قراءة السجلات والتدقيق دون تعديل|
|`ACM Administrator`|إدارة إعدادات التطبيق|
|`System Manager`|إدارة منصة Frappe|

## 6.2 قاعدة الفصل بين المهام

يجب دعم الفصل بين:

- منشئ الخطاب.
- مراجع الخطاب.
- المعتمد.
- الموقّع.
- موظف الصادر.
- مسؤول التسليم.
- مسؤول الإغلاق.

ويجب منع المستخدم من اعتماد خطابه بنفسه إذا فُعّل خيار الفصل بين المهام.

---

# 7. استخدام DocTypes القياسية

يجب إعادة استخدام DocTypes القياسية بدل تكرارها:

|DocType قياسي|الاستخدام|
|---|---|
|`User`|حساب المستخدم|
|`Role`|الأدوار|
|`Company`|الجهة القانونية|
|`Department`|الإدارات والوحدات التنظيمية|
|`Employee`|بيانات الموظف|
|`Contact`|جهات الاتصال|
|`Address`|عناوين الجهات|
|`File`|تخزين الملفات|
|`Communication`|البريد أو التواصل المرتبط|
|`ToDo`|الإسنادات الاختيارية|
|`Comment`|التعليقات غير الرسمية|
|`Version`|تتبع التعديلات|
|`Notification`|إشعارات النظام|
|`Email Account`|البريد الصادر والوارد|
|`Print Format`|الخطابات والباركود والتقارير|

---

# 8. الحقول المخصصة على DocTypes القياسية

## 8.1 حقول `Department`

|Fieldname|التسمية|النوع|إلزامي|
|---|---|---|---|
|`acm_unit_code`|رمز وحدة المراسلات|Data|نعم عند التفعيل|
|`acm_unit_type`|نوع الوحدة|Select|لا|
|`acm_accepts_incoming`|تستقبل وارد|Check|لا|
|`acm_issues_outgoing`|تصدر معاملات|Check|لا|
|`acm_allow_internal`|تسمح بمعاملات داخلية|Check|لا|
|`acm_manager_user`|مدير الإدارة|Link/User|لا|
|`acm_coordinator_user`|منسق المعاملات|Link/User|لا|
|`acm_correspondence_email`|بريد المراسلات|Data|لا|
|`acm_default_sla_policy`|سياسة الاستحقاق|Link/ACM SLA Policy|لا|
|`acm_is_correspondence_office`|مكتب اتصالات إدارية|Check|لا|
|`acm_active`|مفعلة في المعاملات|Check|نعم|

## 8.2 حقول `Employee`

|Fieldname|التسمية|النوع|
|---|---|---|
|`acm_can_receive_directly`|يمكن الإحالة إليه مباشرة|Check|
|`acm_job_correspondence_code`|رمز الموظف بالمراسلات|Data|
|`acm_max_confidentiality`|أعلى سرية مسموحة|Link/ACM Confidentiality Level|
|`acm_default_delegation_user`|المفوض إليه الافتراضي|Link/User|
|`acm_signature_profile`|ملف التوقيع|Link/ACM Signature Profile|

---

# 9. كتالوج الـDocTypes المخصصة

## 9.1 ملخص الـDocTypes

### إعدادات وبيانات مرجعية

1. ACM Settings
2. ACM External Party
3. ACM Correspondence Type
4. ACM Confidentiality Level
5. ACM Priority Level
6. ACM Routing Purpose
7. ACM Subject Classification
8. ACM Document Category
9. ACM Correspondence Reason
10. ACM Delivery Method
11. ACM SLA Policy
12. ACM Numbering Rule
13. ACM Retention Policy
14. ACM Signature Profile

### المعاملات

15. ACM Correspondence
16. ACM Correspondence Link
17. ACM Concerned Person
18. ACM Correspondence Document
19. ACM Referral
20. ACM Referral Recipient
21. ACM Correspondence Action
22. ACM Approval Step
23. ACM Approval Action

### التنظيم والمتابعة

24. ACM Delegation
25. ACM Personal Folder
26. ACM Folder Item
27. ACM Follow Up Entry

### التسليم

28. ACM Dispatch
29. ACM Dispatch Item
30. ACM Delivery Event

### المهام

31. ACM Work Task
32. ACM Task Assignee
33. ACM Task Update

### اللجان والاجتماعات

34. ACM Committee
35. ACM Committee Member
36. ACM Meeting
37. ACM Meeting Attendee
38. ACM Agenda Item
39. ACM Meeting Decision

---

# 10. تعريف الـDocTypes والحقول

## 10.1 `ACM Settings`

**النوع:** Single  
**الغرض:** الإعدادات العامة.

|Fieldname|التسمية|النوع|الافتراضي|
|---|---|---|---|
|`default_company`|الشركة الافتراضية|Link/Company|—|
|`default_confidentiality`|السرية الافتراضية|Link|عادي|
|`default_priority`|الأهمية الافتراضية|Link|عادي|
|`default_internal_type`|نوع المعاملة الداخلية|Link|خطاب|
|`default_incoming_type`|نوع الوارد|Link|خطاب|
|`default_outgoing_type`|نوع الصادر|Link|خطاب|
|`display_hijri_dates`|عرض التاريخ الهجري|Check|1|
|`hijri_adjustment`|تصحيح التاريخ الهجري|Int|0|
|`require_due_date_on_referral`|إلزام استحقاق الإحالة|Check|1|
|`require_main_document`|إلزام الخطاب الرئيسي|Check|1|
|`allow_multiple_referrals`|السماح بإحالة متعددة|Check|1|
|`allow_direct_employee_referral`|الإحالة المباشرة للموظف|Check|1|
|`allow_withdraw_after_receipt`|السماح بالسحب بعد الاستلام|Check|0|
|`require_rejection_reason`|إلزام سبب الرفض|Check|1|
|`require_close_reason`|إلزام سبب الإغلاق|Check|1|
|`allow_self_approval`|السماح بالاعتماد الذاتي|Check|0|
|`barcode_type`|نوع الباركود|Select|QR Code|
|`barcode_prefix`|بادئة الباركود|Data|ACM|
|`max_file_size_mb`|أقصى حجم للملف|Int|25|
|`allowed_file_extensions`|الامتدادات المسموحة|Small Text|pdf,docx,xlsx,png,jpg|
|`enable_ocr`|تفعيل OCR|Check|0|
|`enable_email_gateway`|تفعيل البريد|Check|0|
|`enable_sms`|تفعيل الرسائل|Check|0|
|`enable_digital_signature`|تفعيل التوقيع الرقمي|Check|0|
|`enable_paper_tracking`|تتبع النسخ الورقية|Check|1|
|`warning_before_due_days`|تنبيه قبل الاستحقاق|Int|2|
|`auto_close_days`|الإغلاق التلقائي بعد الإنجاز|Int|0|
|`retention_policy`|سياسة الاحتفاظ الافتراضية|Link|—|
|`audit_log_retention_days`|مدة الاحتفاظ بسجل التدقيق|Int|3650|

---

## 10.2 `ACM External Party`

**الغرض:** الجهات الخارجية الوارد منها أو الصادر إليها.

|Fieldname|التسمية|النوع|إلزامي|
|---|---|---|---|
|`party_name`|اسم الجهة|Data|نعم|
|`party_name_en`|الاسم الإنجليزي|Data|لا|
|`party_code`|رمز الجهة|Data/Unique|نعم|
|`party_type`|نوع الجهة|Select|نعم|
|`parent_party`|الجهة الأعلى|Link/Self|لا|
|`is_group`|مجموعة|Check|لا|
|`government_id`|الرقم الرسمي|Data|لا|
|`country`|الدولة|Link/Country|لا|
|`city`|المدينة|Data|لا|
|`address`|العنوان|Link/Address|لا|
|`primary_contact`|جهة الاتصال|Link/Contact|لا|
|`email`|البريد|Data|لا|
|`phone`|الهاتف|Data|لا|
|`preferred_delivery_method`|وسيلة التسليم|Link|لا|
|`is_active`|نشطة|Check|نعم|
|`notes`|ملاحظات|Small Text|لا|

قيم `party_type`:

- وزارة.
- جهة حكومية.
- مؤسسة عامة.
- شركة.
- بنك.
- جامعة.
- مدرسة.
- فرد.
- جهة دولية.
- أخرى.

---

## 10.3 `ACM Correspondence Type`

|Fieldname|التسمية|النوع|
|---|---|---|
|`type_name`|اسم النوع|Data|
|`type_code`|الرمز|Data/Unique|
|`allowed_direction`|الاتجاه المسموح|Select|
|`requires_letter_number`|يتطلب رقم خطاب|Check|
|`requires_letter_date`|يتطلب تاريخ خطاب|Check|
|`requires_main_document`|يتطلب خطابًا رئيسيًا|Check|
|`default_confidentiality`|السرية الافتراضية|Link|
|`default_priority`|الأهمية الافتراضية|Link|
|`default_sla_policy`|سياسة الاستحقاق|Link|
|`is_active`|نشط|Check|

قيم الاتجاه:

- جميع الاتجاهات.
- داخلي.
- وارد خارجي.
- صادر خارجي.

أمثلة الأنواع:

- خطاب.
- تعميم.
- قرار.
- مذكرة.
- طلب.
- شكوى.
- دعوة.
- محضر.
- تقرير.
- بريد إلكتروني.

---

## 10.4 `ACM Confidentiality Level`

|Fieldname|التسمية|النوع|
|---|---|---|
|`level_name`|اسم الدرجة|Data|
|`level_code`|الرمز|Data/Unique|
|`rank`|الترتيب الأمني|Int|
|`color`|اللون|Color|
|`requires_explicit_access`|يتطلب تصريحًا مباشرًا|Check|
|`hide_subject`|إخفاء الموضوع عن غير المخول|Check|
|`prevent_download`|منع التنزيل|Check|
|`prevent_print`|منع الطباعة|Check|
|`watermark_required`|إلزام العلامة المائية|Check|
|`allow_delegation`|السماح بالتفويض|Check|
|`is_active`|نشط|Check|

قيم أولية:

1. عادي.
2. محدود.
3. سري.
4. سري جدًا.

---

## 10.5 `ACM Priority Level`

|Fieldname|التسمية|النوع|
|---|---|---|
|`priority_name`|اسم الأهمية|Data|
|`priority_code`|الرمز|Data/Unique|
|`rank`|الترتيب|Int|
|`color`|اللون|Color|
|`default_due_days`|أيام الاستحقاق|Int|
|`escalation_hours`|ساعات التصعيد|Int|
|`is_active`|نشط|Check|

القيم الأولية المستخرجة من الواجهة:

- عادي.
- عاجل.
- عاجل جدًا.
- حالًا.

---

## 10.6 `ACM Routing Purpose`

|Fieldname|التسمية|النوع|
|---|---|---|
|`purpose_name`|التوجيه|Data|
|`purpose_code`|الرمز|Data/Unique|
|`requires_completion`|يتطلب إنجازًا|Check|
|`requires_approval`|يتطلب موافقة|Check|
|`requires_signature`|يتطلب توقيعًا|Check|
|`allows_copy`|يسمح بصورة|Check|
|`default_due_days`|أيام الاستحقاق|Int|
|`is_active`|نشط|Check|

القيم المثبتة من الصور:

- للتوقيع.
- لإكمال اللازم.
- للمشاهدة.
- للموافقة.
- للتعميم.
- للدراسة وإبداء الرأي.

قيم إضافية قابلة للتهيئة:

- للإفادة.
- للاطلاع.
- للحفظ.
- للمتابعة.
- للإجراء.
- للإجابة.
- للمراجعة.

---

## 10.7 `ACM Subject Classification`

|Fieldname|التسمية|النوع|
|---|---|---|
|`classification_name`|التصنيف|Data|
|`classification_code`|الرمز|Data|
|`parent_classification`|التصنيف الأعلى|Link/Self|
|`is_group`|مجموعة|Check|
|`retention_policy`|سياسة الاحتفاظ|Link|
|`default_confidentiality`|السرية الافتراضية|Link|
|`is_active`|نشط|Check|

---

## 10.8 `ACM Document Category`

|Fieldname|التسمية|النوع|
|---|---|---|
|`category_name`|اسم الفئة|Data|
|`category_code`|الرمز|Data|
|`is_main_document`|خطاب رئيسي|Check|
|`is_reply`|رد|Check|
|`is_secret`|مرفق سري|Check|
|`allowed_extensions`|الامتدادات|Small Text|
|`max_size_mb`|أقصى حجم|Int|
|`is_active`|نشط|Check|

قيم أولية:

- الخطاب الرئيسي.
- المرفقات.
- الرد.
- المرفقات السرية.
- إثبات التسليم.
- نسخة ممسوحة.
- محضر.
- توقيع إلكتروني.

---

## 10.9 `ACM Correspondence Reason`

|Fieldname|التسمية|النوع|
|---|---|---|
|`reason_name`|السبب|Data|
|`reason_type`|نوع السبب|Select|
|`requires_note`|يتطلب شرحًا|Check|
|`is_active`|نشط|Check|

أنواع السبب:

- رفض.
- إعادة.
- سحب.
- إغلاق.
- إلغاء.
- إعادة تشغيل.

---

## 10.10 `ACM Delivery Method`

|Fieldname|التسمية|النوع|
|---|---|---|
|`method_name`|وسيلة التسليم|Data|
|`method_code`|الرمز|Data|
|`requires_tracking_number`|يتطلب رقم تتبع|Check|
|`requires_receiver_name`|يتطلب اسم مستلم|Check|
|`requires_proof`|يتطلب إثباتًا|Check|
|`is_electronic`|إلكترونية|Check|
|`is_active`|نشطة|Check|

أمثلة:

- تسليم يدوي.
- بريد رسمي.
- بريد سريع.
- بريد إلكتروني.
- تكامل إلكتروني.
- مندوب.
- فاكس.

---

## 10.11 `ACM SLA Policy`

|Fieldname|التسمية|النوع|
|---|---|---|
|`policy_name`|اسم السياسة|Data|
|`company`|الشركة|Link/Company|
|`department`|الإدارة|Link/Department|
|`correspondence_type`|نوع المعاملة|Link|
|`priority`|الأهمية|Link|
|`routing_purpose`|التوجيه|Link|
|`due_days`|أيام الإنجاز|Int|
|`use_working_days`|أيام عمل|Check|
|`warning_days`|تنبيه قبل الاستحقاق|Int|
|`first_escalation_hours`|التصعيد الأول|Int|
|`second_escalation_hours`|التصعيد الثاني|Int|
|`escalate_to_manager`|تصعيد للمدير|Check|
|`is_active`|نشطة|Check|

---

## 10.12 `ACM Numbering Rule`

|Fieldname|التسمية|النوع|
|---|---|---|
|`rule_name`|اسم القاعدة|Data|
|`company`|الشركة|Link|
|`department`|الإدارة|Link|
|`direction`|الاتجاه|Select|
|`correspondence_type`|النوع|Link|
|`fiscal_or_hijri_year`|نوع السنة|Select|
|`prefix`|البادئة|Data|
|`digits`|عدد الخانات|Int|
|`reset_frequency`|إعادة العداد|Select|
|`current_counter`|العداد الحالي|Int|
|`is_active`|نشطة|Check|

مثال:

```text
IN-1448-000001
OUT-1448-000001
INT-1448-000001
```

---

## 10.13 `ACM Retention Policy`

|Fieldname|التسمية|النوع|
|---|---|---|
|`policy_name`|السياسة|Data|
|`retention_years`|سنوات الاحتفاظ|Int|
|`archive_after_days`|الأرشفة بعد|Int|
|`disposal_action`|إجراء نهاية المدة|Select|
|`requires_approval`|يتطلب اعتمادًا|Check|
|`legal_hold_allowed`|يسمح بالحجز القانوني|Check|
|`is_active`|نشطة|Check|

---

## 10.14 `ACM Signature Profile`

|Fieldname|التسمية|النوع|
|---|---|---|
|`user`|المستخدم|Link/User|
|`employee`|الموظف|Link/Employee|
|`signature_image`|صورة التوقيع|Attach Image|
|`certificate_reference`|مرجع الشهادة|Data|
|`valid_from`|صالح من|Datetime|
|`valid_to`|صالح إلى|Datetime|
|`maximum_confidentiality`|أقصى سرية|Link|
|`is_active`|نشط|Check|

> صورة التوقيع وحدها ليست توقيعًا رقميًا قانونيًا. التوقيع المشفر يتطلب مزود شهادات وآلية تحقق مستقلة.

---

# 11. DocType الرئيسي: `ACM Correspondence`

## 11.1 الإعدادات

- `is_submittable = 0`، لأن المعاملة تحتاج إلى تعديلات محكومة عبر Workflow.
- `track_changes = 1`.
- التسمية من `ACM Numbering Rule`.
- منع الحذف بعد التسجيل.
- المسودة فقط يمكن حذفها وفق الصلاحية.

## 11.2 الحقول

### الهوية

|Fieldname|التسمية|النوع|إلزامي|
|---|---|---|---|
|`correspondence_number`|رقم المعاملة|Data/Read Only/Unique|بعد التسجيل|
|`direction`|اتجاه المعاملة|Select|نعم|
|`correspondence_type`|نوع المعاملة|Link|نعم|
|`workflow_state`|حالة سير العمل|Link/Workflow State|تلقائي|
|`record_status`|حالة السجل|Select|تلقائي|
|`company`|الشركة|Link/Company|نعم|
|`owning_department`|الإدارة المالكة|Link/Department|نعم|
|`current_department`|الإدارة الحالية|Link/Department|تلقائي|
|`current_user`|المستخدم الحالي|Link/User|تلقائي|
|`registration_datetime`|تاريخ التسجيل|Datetime|تلقائي|
|`registration_hijri`|تاريخ التسجيل الهجري|Data|تلقائي|
|`registered_by`|المسجل|Link/User|تلقائي|

قيم `direction`:

- Internal.
- Incoming External.
- Outgoing External.

قيم `record_status`:

- Draft.
- Registered.
- Active.
- Awaiting Approval.
- Approved.
- Ready for Dispatch.
- Dispatched.
- Delivered.
- Closed.
- Reopened.
- Cancelled.

### الموضوع والتصنيف

|Fieldname|التسمية|النوع|إلزامي|
|---|---|---|---|
|`subject`|الموضوع|Data|نعم|
|`subject_classification`|تصنيف الموضوع|Link|لا|
|`confidentiality_level`|درجة السرية|Link|نعم|
|`priority_level`|الأهمية|Link|نعم|
|`general_due_date`|تاريخ الاستحقاق|Date|حسب السياسة|
|`general_due_date_hijri`|الاستحقاق الهجري|Data/Read Only|تلقائي|
|`page_count`|عدد الصفحات|Int|لا|
|`notes`|ملاحظات|Long Text|لا|
|`keywords`|كلمات مفتاحية|Small Text|لا|

### الوارد الخارجي

|Fieldname|التسمية|النوع|
|---|---|---|
|`incoming_party`|الجهة الوارد منها|Link/ACM External Party|
|`incoming_letter_number`|رقم الخطاب|Data|
|`incoming_letter_date`|تاريخ الخطاب الميلادي|Date|
|`incoming_letter_date_hijri`|تاريخ الخطاب الهجري|Data|
|`receiving_department`|الجهة المرسل إليها|Link/Department|
|`incoming_method`|وسيلة الورود|Link/ACM Delivery Method|
|`received_datetime`|تاريخ ووقت الورود|Datetime|
|`physical_received_by`|مستلم الأصل الورقي|Link/User|

### الصادر الخارجي

|Fieldname|التسمية|النوع|
|---|---|---|
|`outgoing_party`|الجهة الصادر إليها|Link/ACM External Party|
|`outgoing_letter_number`|رقم الصادر|Data|
|`outgoing_letter_date`|تاريخ الصادر|Date|
|`outgoing_letter_date_hijri`|تاريخ الصادر الهجري|Data|
|`issuing_department`|الإدارة المنشئة|Link/Department|
|`delivery_method`|وسيلة الإرسال|Link|
|`dispatch_reference`|مرجع التسليم|Link/ACM Dispatch|

### الربط والتجميع

|Fieldname|التسمية|النوع|
|---|---|---|
|`link_to_other_correspondence`|اربط بمعاملة أخرى|Check|
|`primary_linked_correspondence`|المعاملة المرتبطة الرئيسية|Link/Self|
|`links`|روابط المعاملات|Table/ACM Correspondence Link|
|`concerned_persons`|بيانات الشخص المعني|Table/ACM Concerned Person|
|`parent_correspondence`|المعاملة الأم|Link/Self|
|`reply_to`|رد على|Link/Self|

### مؤشرات الوثائق

|Fieldname|التسمية|النوع|
|---|---|---|
|`main_document_count`|الخطاب الرئيسي|Int/Read Only|
|`attachment_count`|عدد المرفقات|Int/Read Only|
|`reply_count`|عدد الردود|Int/Read Only|
|`secret_attachment_count`|المرفقات السرية|Int/Read Only|
|`has_physical_copy`|توجد مراسلة ورقية|Check|
|`physical_copy_location`|موقع النسخة الورقية|Data|

### المؤشرات الزمنية

|Fieldname|التسمية|النوع|
|---|---|---|
|`first_referral_datetime`|أول إحالة|Datetime|
|`last_action_datetime`|آخر إجراء|Datetime|
|`closed_datetime`|تاريخ الإغلاق|Datetime|
|`closed_by`|أغلق بواسطة|Link/User|
|`close_reason`|سبب الإغلاق|Link/ACM Correspondence Reason|
|`is_overdue`|متأخرة|Check/Read Only|
|`overdue_days`|أيام التأخير|Int/Read Only|
|`is_on_hold`|معلقة|Check|
|`legal_hold`|حجز قانوني|Check|

### الباركود

|Fieldname|التسمية|النوع|
|---|---|---|
|`barcode_value`|قيمة الباركود|Barcode/Read Only|
|`qr_payload`|بيانات QR|Small Text/Read Only|
|`barcode_printed`|تمت الطباعة|Check|
|`barcode_print_count`|عدد مرات الطباعة|Int|
|`last_barcode_printed_by`|آخر طباعة بواسطة|Link/User|
|`last_barcode_printed_on`|تاريخ آخر طباعة|Datetime|

### حقول تقنية

|Fieldname|التسمية|النوع|
|---|---|---|
|`source_channel`|قناة الإنشاء|Select|
|`external_reference`|مرجع النظام الخارجي|Data|
|`integration_status`|حالة التكامل|Select|
|`retention_policy`|سياسة الاحتفاظ|Link|
|`archive_status`|حالة الأرشفة|Select|
|`archived_on`|تاريخ الأرشفة|Datetime|

---

# 12. `ACM Correspondence Link` — Child Table

|Fieldname|التسمية|النوع|
|---|---|---|
|`linked_correspondence`|المعاملة المرتبطة|Link/ACM Correspondence|
|`link_type`|نوع العلاقة|Select|
|`is_primary`|العلاقة الرئيسية|Check|
|`sequence`|الترتيب|Int|
|`notes`|ملاحظات|Small Text|

قيم العلاقة:

- مرتبط بـ.
- رد على.
- أصل لـ.
- تابع لـ.
- سابق.
- لاحق.
- مكرر.
- مرفق بمعاملة.
- وارد مرتبط بصادر.

قاعدة العمل:

> عند ربط أكثر من معاملة يمكن اعتماد أول معاملة كمرجع رئيسي، مع الاحتفاظ ببقية الروابط.

---

# 13. `ACM Concerned Person` — Child Table

|Fieldname|التسمية|النوع|
|---|---|---|
|`person_type`|نوع الشخص|Select|
|`full_name`|الاسم|Data|
|`national_id`|رقم الهوية|Data|
|`employee`|الموظف|Link/Employee|
|`external_contact`|جهة الاتصال|Link/Contact|
|`mobile`|الجوال|Data|
|`email`|البريد|Data|
|`relationship`|صفته في المعاملة|Data|
|`notes`|ملاحظات|Small Text|
|`mask_identity`|إخفاء الهوية|Check|

يجب تشفير أو إخفاء بيانات الهوية في العرض والتقارير بحسب الصلاحية.

---

# 14. `ACM Correspondence Document`

هذا الـDocType يمثل كل ملف على حدة بدل الاكتفاء بإرفاق الملفات مباشرة بالمعاملة.

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`document_category`|النوع|Link/ACM Document Category|
|`folder_section`|المجلد|Select|
|`document_title`|عنوان المستند|Data|
|`file`|الملف|Attach|
|`file_name`|اسم الملف|Data/Read Only|
|`file_extension`|الامتداد|Data/Read Only|
|`file_size`|الحجم|Int/Read Only|
|`is_private`|ملف خاص|Check|
|`is_secret`|مرفق سري|Check|
|`confidentiality_level`|سرية المستند|Link|
|`version_number`|رقم النسخة|Int|
|`replaces_document`|يحل محل|Link/Self|
|`is_current_version`|النسخة الحالية|Check|
|`is_main_document`|الخطاب الرئيسي|Check|
|`is_reply`|رد|Check|
|`uploaded_by`|رفع بواسطة|Link/User|
|`uploaded_on`|تاريخ الرفع|Datetime|
|`source`|مصدر الملف|Select|
|`scan_device`|جهاز المسح|Data|
|`page_count`|الصفحات|Int|
|`checksum_sha256`|بصمة الملف|Data/Read Only|
|`ocr_status`|حالة OCR|Select|
|`ocr_text`|النص المستخرج|Long Text|
|`digitally_signed`|موقع رقميًا|Check|
|`signature_status`|حالة التحقق|Select|
|`watermark_required`|علامة مائية|Check|
|`download_count`|مرات التنزيل|Int/Read Only|

قيم `folder_section`:

- Main Letter.
- Attachments.
- Reply.
- Secret Attachments.
- Delivery Proof.
- Other.

قيم المصدر:

- Upload.
- Scanner.
- Email.
- API.
- Generated.
- Mobile Camera.

يجب أن تُحفظ الملفات Private. وتوضح وثائق Frappe أن من يملك Read على المستند يستطيع الوصول عادةً إلى مرفقاته؛ لذلك يجب ربط المرفقات السرية بهذا الـDocType المستقل وتطبيق `has_permission` و`permission_query_conditions` عليه، بدل الاعتماد على مرفقات المعاملة العامة فقط.  
[Attachments](https://docs.frappe.io/framework/user/en/desk/attachments) — [Permission Query Conditions](https://docs.frappe.io/framework/user/en/python-api/hooks)

---

# 15. `ACM Referral`

كل مستلم يجب أن ينتج إحالة مستقلة حتى يمكن تتبع حالته واستحقاقه.

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`referral_number`|رقم الإحالة|Data/Unique|
|`referral_batch_id`|مجموعة الإحالة المتعددة|Data|
|`from_department`|من إدارة|Link/Department|
|`from_user`|من مستخدم|Link/User|
|`to_type`|نوع المستلم|Select|
|`to_department`|إلى إدارة|Link/Department|
|`to_user`|إلى موظف|Link/User|
|`routing_purpose`|التوجيه|Link|
|`priority_level`|درجة الأهمية|Link|
|`due_date`|تاريخ الاستحقاق|Date|
|`due_date_hijri`|الاستحقاق الهجري|Data|
|`recipient_instructions`|تعليمات للمستقبل|Small Text|
|`is_private`|خاص|Check|
|`is_paper_correspondence`|مراسلة ورقية|Check|
|`is_copy`|صورة|Check|
|`for_follow_up`|للمتابعة|Check|
|`referral_status`|حالة الإحالة|Select|
|`sent_on`|تاريخ الإرسال|Datetime|
|`received_on`|تاريخ الاستلام|Datetime|
|`received_by`|استلم بواسطة|Link/User|
|`rejected_on`|تاريخ الرفض|Datetime|
|`rejected_by`|رفض بواسطة|Link/User|
|`rejection_reason`|سبب الرفض|Link|
|`rejection_notes`|ملاحظات الرفض|Small Text|
|`completed_on`|تاريخ الإنجاز|Datetime|
|`completed_by`|أنجز بواسطة|Link/User|
|`completion_notes`|نتيجة الإجراء|Long Text|
|`withdrawn_on`|تاريخ السحب|Datetime|
|`withdrawn_by`|سحب بواسطة|Link/User|
|`withdrawal_reason`|سبب السحب|Link|
|`parent_referral`|الإحالة السابقة|Link/Self|
|`delegation`|التفويض المستخدم|Link/ACM Delegation|
|`is_overdue`|متأخرة|Check/Read Only|
|`overdue_days`|أيام التأخير|Int/Read Only|

حالات الإحالة:

```text
Draft
Sent
Pending Receipt
Received
In Progress
Completed
Rejected
Returned
Withdrawn
Cancelled
```

---

# 16. `ACM Referral Recipient`

يستخدم فقط في واجهة إنشاء الإحالة المتعددة قبل تحويل الصفوف إلى سجلات `ACM Referral`.

|Fieldname|التسمية|النوع|
|---|---|---|
|`recipient_type`|نوع المستلم|Select|
|`department`|الإدارة|Link|
|`user`|الموظف|Link|
|`routing_purpose`|التوجيه|Link|
|`priority_level`|درجة الأهمية|Link|
|`due_date`|تاريخ الاستحقاق|Date|
|`instructions`|تعليمات للمستقبل|Small Text|
|`is_private`|خاص|Check|
|`is_paper`|مراسلة ورقية|Check|
|`is_copy`|صورة|Check|
|`for_follow_up`|للمتابعة|Check|

---

# 17. `ACM Correspondence Action`

سجل أحداث غير قابل للتعديل من المستخدم العادي.

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`referral`|الإحالة|Link|
|`action_type`|نوع العملية|Select|
|`action_datetime`|التاريخ والوقت|Datetime|
|`performed_by`|المنفذ الفعلي|Link/User|
|`acting_for`|يعمل نيابة عن|Link/User|
|`delegation`|التفويض|Link|
|`from_status`|الحالة السابقة|Data|
|`to_status`|الحالة الجديدة|Data|
|`from_department`|من إدارة|Link|
|`to_department`|إلى إدارة|Link|
|`notes`|الملاحظات|Long Text|
|`ip_address`|عنوان IP|Data|
|`user_agent`|معلومات الجهاز|Small Text|
|`source`|مصدر العملية|Select|
|`request_id`|معرف الطلب|Data|
|`payload_hash`|بصمة الحدث|Data|
|`previous_hash`|بصمة الحدث السابق|Data|

أنواع العمليات:

- إنشاء.
- حفظ مسودة.
- تسجيل.
- تعديل.
- ربط.
- رفع مرفق.
- حذف مرفق قبل التسجيل.
- إحالة.
- استلام.
- رفض.
- إعادة.
- سحب.
- إكمال.
- إضافة رد.
- طلب اعتماد.
- موافقة.
- توقيع.
- رفض اعتماد.
- إرسال.
- تسليم.
- إغلاق.
- إعادة تشغيل.
- طباعة.
- تنزيل.
- أرشفة.
- إلغاء.

---

# 18. الاعتمادات

## 18.1 `ACM Approval Step`

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`document`|المستند|Link|
|`sequence`|ترتيب الاعتماد|Int|
|`approval_type`|نوع الاعتماد|Select|
|`approver_type`|نوع المعتمد|Select|
|`approver_role`|الدور|Link/Role|
|`approver_user`|المستخدم|Link/User|
|`approver_department`|الإدارة|Link|
|`status`|الحالة|Select|
|`requested_on`|تاريخ الطلب|Datetime|
|`due_date`|الاستحقاق|Datetime|
|`acted_on`|تاريخ الإجراء|Datetime|
|`comments`|الملاحظات|Small Text|

أنواع الاعتماد:

- Review.
- Approval.
- Signature.
- Visa/Endorsement.
- Final Release.

## 18.2 `ACM Approval Action`

|Fieldname|التسمية|النوع|
|---|---|---|
|`approval_step`|خطوة الاعتماد|Link|
|`action`|الإجراء|Select|
|`action_by`|بواسطة|Link/User|
|`action_on`|التاريخ|Datetime|
|`comments`|الملاحظات|Long Text|
|`signed_document`|المستند الموقع|Link/ACM Correspondence Document|
|`signature_hash`|بصمة التوقيع|Data|
|`delegation`|التفويض|Link|

الإجراءات:

- Approve.
- Sign.
- Endorse.
- Return for Revision.
- Reject.
- Forward.

---

# 19. `ACM Delegation`

|Fieldname|التسمية|النوع|
|---|---|---|
|`delegator`|المفوِّض|Link/User|
|`delegate`|المفوَّض إليه|Link/User|
|`company`|الشركة|Link|
|`department`|الإدارة|Link|
|`valid_from`|من تاريخ|Datetime|
|`valid_to`|إلى تاريخ|Datetime|
|`scope`|نطاق التفويض|Select|
|`allowed_actions`|الإجراءات|Table MultiSelect أو Child|
|`maximum_confidentiality`|أقصى سرية|Link|
|`exclude_private_referrals`|استثناء الإحالات الخاصة|Check|
|`reason`|السبب|Small Text|
|`status`|الحالة|Select|
|`approved_by`|اعتمد بواسطة|Link/User|
|`approved_on`|تاريخ الاعتماد|Datetime|
|`revoked_by`|أُلغي بواسطة|Link/User|
|`revoked_on`|تاريخ الإلغاء|Datetime|

ضوابط:

- لا تفويض خارج الفترة.
- لا يمكن تفويض صلاحية أعلى من صلاحية المفوِّض.
- السرية العالية يمكن منع تفويضها.
- كل إجراء يسجل المنفذ والمستخدم الأصلي.

---

# 20. المجلدات

## 20.1 `ACM Personal Folder`

|Fieldname|التسمية|النوع|
|---|---|---|
|`folder_name`|اسم المجلد|Data|
|`owner_user`|المالك|Link/User|
|`parent_folder`|المجلد الأعلى|Link/Self|
|`color`|اللون|Color|
|`is_shared`|مشترك|Check|
|`shared_department`|الإدارة المشتركة|Link|
|`is_active`|نشط|Check|

## 20.2 `ACM Folder Item`

|Fieldname|التسمية|النوع|
|---|---|---|
|`folder`|المجلد|Link|
|`correspondence`|المعاملة|Link|
|`added_by`|أضيف بواسطة|Link/User|
|`added_on`|تاريخ الإضافة|Datetime|
|`notes`|ملاحظات شخصية|Small Text|

المجلد لا يغير حالة المعاملة أو ملكيتها.

---

# 21. `ACM Follow Up Entry`

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`referral`|الإحالة|Link|
|`follow_up_owner`|مسؤول المتابعة|Link/User|
|`department`|الإدارة|Link|
|`follow_up_date`|تاريخ المتابعة|Date|
|`status`|الحالة|Select|
|`reminder_datetime`|التذكير|Datetime|
|`notes`|الملاحظات|Long Text|
|`result`|النتيجة|Long Text|
|`closed_on`|تاريخ الإغلاق|Datetime|

---

# 22. التسليم

## 22.1 `ACM Dispatch`

|Fieldname|التسمية|النوع|
|---|---|---|
|`dispatch_number`|رقم بيان التسليم|Data/Unique|
|`dispatch_date`|التاريخ|Date|
|`company`|الشركة|Link|
|`dispatch_department`|إدارة الصادر|Link|
|`delivery_method`|وسيلة التسليم|Link|
|`courier_name`|المندوب/الناقل|Data|
|`tracking_number`|رقم التتبع|Data|
|`status`|الحالة|Select|
|`prepared_by`|أعد بواسطة|Link/User|
|`handed_over_on`|تاريخ التسليم للناقل|Datetime|
|`notes`|ملاحظات|Long Text|
|`items`|المعاملات|Table/ACM Dispatch Item|

الحالات:

- Draft.
- Prepared.
- Handed Over.
- In Transit.
- Partially Delivered.
- Delivered.
- Returned.
- Cancelled.

## 22.2 `ACM Dispatch Item`

|Fieldname|التسمية|النوع|
|---|---|---|
|`correspondence`|المعاملة|Link|
|`external_party`|الجهة المستلمة|Link|
|`recipient_name`|اسم المستلم|Data|
|`address`|العنوان|Link/Address|
|`package_number`|رقم الطرد|Data|
|`status`|الحالة|Select|
|`delivered_on`|تاريخ التسليم|Datetime|
|`delivery_event`|آخر حدث|Link|
|`proof_document`|إثبات التسليم|Link/ACM Correspondence Document|

## 22.3 `ACM Delivery Event`

|Fieldname|التسمية|النوع|
|---|---|---|
|`dispatch`|بيان التسليم|Link|
|`dispatch_item`|البند|Link|
|`event_type`|نوع الحدث|Select|
|`event_datetime`|التاريخ والوقت|Datetime|
|`location`|الموقع|Data|
|`receiver_name`|اسم المستلم|Data|
|`receiver_id`|هوية المستلم|Data|
|`tracking_number`|رقم التتبع|Data|
|`proof_file`|الإثبات|Attach|
|`recorded_by`|سجل بواسطة|Link/User|
|`notes`|ملاحظات|Small Text|

---

# 23. إدارة المهام

## 23.1 `ACM Work Task`

|Fieldname|التسمية|النوع|
|---|---|---|
|`task_title`|عنوان المهمة|Data|
|`description`|الوصف|Text Editor|
|`correspondence`|المعاملة|Link|
|`project`|المشروع|Link/Project|
|`committee`|اللجنة|Link|
|`meeting`|الاجتماع|Link|
|`task_pattern`|النمط|Data|
|`priority`|الأولوية|Link/ACM Priority Level|
|`status`|الحالة|Select|
|`start_date`|تاريخ البداية|Date|
|`due_date`|تاريخ الاستحقاق|Date|
|`progress`|نسبة الإنجاز|Percent|
|`owner_user`|مالك المهمة|Link/User|
|`department`|الإدارة|Link|
|`remind_before`|التذكير قبل|Duration|
|`parent_task`|المهمة الأعلى|Link/Self|
|`copied_from`|منسوخة من|Link/Self|
|`is_recurring`|متكررة|Check|
|`completion_notes`|ملاحظات الإنجاز|Long Text|
|`completed_on`|تاريخ الإنجاز|Datetime|
|`assignees`|المكلفون|Table/ACM Task Assignee|

## 23.2 `ACM Task Assignee`

|Fieldname|التسمية|النوع|
|---|---|---|
|`user`|المستخدم|Link/User|
|`employee`|الموظف|Link/Employee|
|`department`|الإدارة|Link|
|`assignment_role`|دوره في المهمة|Select|
|`individual_due_date`|استحقاقه|Date|
|`progress`|الإنجاز|Percent|
|`status`|الحالة|Select|

## 23.3 `ACM Task Update`

|Fieldname|التسمية|النوع|
|---|---|---|
|`task`|المهمة|Link|
|`update_by`|بواسطة|Link/User|
|`update_on`|التاريخ|Datetime|
|`old_progress`|الإنجاز السابق|Percent|
|`new_progress`|الإنجاز الجديد|Percent|
|`status`|الحالة|Select|
|`update_text`|التحديث|Long Text|
|`attachment`|مرفق|Attach|

---

# 24. اللجان والاجتماعات

## 24.1 `ACM Committee`

|Fieldname|التسمية|النوع|
|---|---|---|
|`committee_name`|اسم اللجنة|Data|
|`committee_number`|رقم اللجنة|Data|
|`formation_date`|تاريخ التشكيل|Date|
|`formation_correspondence`|قرار التشكيل|Link/ACM Correspondence|
|`chairperson`|الرئيس|Link/User|
|`secretary`|المقرر|Link/User|
|`department`|الإدارة|Link|
|`valid_from`|من تاريخ|Date|
|`valid_to`|إلى تاريخ|Date|
|`status`|الحالة|Select|
|`purpose`|الهدف|Long Text|
|`members`|الأعضاء|Table/ACM Committee Member|

## 24.2 `ACM Committee Member`

|Fieldname|التسمية|النوع|
|---|---|---|
|`member_type`|نوع العضو|Select|
|`user`|المستخدم|Link/User|
|`employee`|الموظف|Link/Employee|
|`external_name`|اسم عضو خارجي|Data|
|`external_party`|الجهة الخارجية|Link|
|`member_role`|الصفة|Select|
|`start_date`|من تاريخ|Date|
|`end_date`|إلى تاريخ|Date|
|`is_active`|نشط|Check|

## 24.3 `ACM Meeting`

|Fieldname|التسمية|النوع|
|---|---|---|
|`meeting_title`|عنوان الاجتماع|Data|
|`committee`|اللجنة|Link|
|`meeting_number`|رقم الاجتماع|Data|
|`start_datetime`|البداية|Datetime|
|`end_datetime`|النهاية|Datetime|
|`location`|المكان|Data|
|`online_meeting_url`|رابط الاجتماع|Data|
|`chairperson`|الرئيس|Link/User|
|`secretary`|المقرر|Link/User|
|`status`|الحالة|Select|
|`related_correspondence`|المعاملة المرتبطة|Link|
|`attendees`|الحضور|Table|
|`agenda_items`|جدول الأعمال|Table|
|`minutes_document`|المحضر|Link/ACM Correspondence Document|

## 24.4 `ACM Meeting Attendee`

|Fieldname|التسمية|النوع|
|---|---|---|
|`user`|المستخدم|Link|
|`external_name`|الاسم الخارجي|Data|
|`attendance_status`|حالة الحضور|Select|
|`invitation_sent`|أرسلت الدعوة|Check|
|`response_on`|تاريخ الرد|Datetime|
|`notes`|ملاحظات|Small Text|

## 24.5 `ACM Agenda Item`

|Fieldname|التسمية|النوع|
|---|---|---|
|`sequence`|الترتيب|Int|
|`subject`|الموضوع|Data|
|`presenter`|مقدم الموضوع|Link/User|
|`correspondence`|المعاملة المرتبطة|Link|
|`planned_duration`|المدة|Duration|
|`notes`|ملاحظات|Long Text|

## 24.6 `ACM Meeting Decision`

|Fieldname|التسمية|النوع|
|---|---|---|
|`meeting`|الاجتماع|Link|
|`agenda_item`|بند الجدول|Data|
|`decision_number`|رقم القرار|Data|
|`decision_text`|نص القرار|Long Text|
|`responsible_user`|المسؤول|Link/User|
|`responsible_department`|الإدارة|Link|
|`due_date`|الاستحقاق|Date|
|`work_task`|المهمة الناتجة|Link/ACM Work Task|
|`status`|الحالة|Select|

---

# 25. مسارات العمل Workflows

## 25.1 المعاملة الواردة

```text
Draft
→ Registered
→ Routed
→ Pending Receipt
→ Received
→ In Progress
→ Awaiting Response
→ Response Prepared
→ Completed
→ Closed
```

مسارات بديلة:

```text
Pending Receipt → Rejected → Returned to Sender
Received → Returned for Clarification
Closed → Reopened → In Progress
```

## 25.2 المعاملة الداخلية

```text
Draft
→ Registered
→ Routed
→ Received
→ In Progress
→ Completed
→ Closed
```

إذا احتوت خطابًا يحتاج اعتمادًا:

```text
In Progress
→ Awaiting Review
→ Awaiting Approval
→ Awaiting Signature
→ Approved
→ Completed
→ Closed
```

## 25.3 المعاملة الصادرة

```text
Draft
→ Under Review
→ Awaiting Approval
→ Awaiting Signature
→ Approved
→ Registered Outgoing
→ Ready for Dispatch
→ Dispatched
→ Delivered
→ Closed
```

## 25.4 سحب الإحالة

يسمح بالسحب إذا:

- المرسل لديه صلاحية السحب.
- الإحالة غير مستلمة؛ أو تسمح الإعدادات بالسحب بعد الاستلام.
- لا توجد إحالة لاحقة مبنية عليها.
- يُسجل سبب السحب.

## 25.5 رفض الإحالة

يتطلب:

- سبب رفض.
- ملاحظة عند إعداد السبب لذلك.
- تسجيل التاريخ والمستخدم.
- إعادة المسؤولية للجهة المرسلة.
- إرسال إشعار فوري.

## 25.6 إعادة تشغيل المراسلة

- للمعاملات المغلقة فقط.
- يتطلب سببًا.
- لا يمحو دورة العمل القديمة.
- ينشئ حدث Reopened.
- يعيد الحالة إلى Active أو In Progress.
- يحدد إدارة ومستخدمًا مسؤولًا جديدًا.

---

# 26. قواعد العمل Business Rules

## BR-001

رقم المعاملة فريد ولا يمكن تغييره بعد التسجيل.

## BR-002

يجب ألا يحصل السجل على رقم نهائي أثناء كونه مسودة، إلا إذا كانت سياسة الجهة تحجز الرقم مسبقًا.

## BR-003

الوارد الخارجي يتطلب:

- الجهة الوارد منها.
- رقم الخطاب إذا كان النوع يتطلبه.
- تاريخ الخطاب.
- الموضوع.
- نوع المعاملة.
- السرية.
- الأهمية.
- الجهة المستقبلة.

## BR-004

الصادر الخارجي يتطلب جهة صادرة إليها وخطابًا معتمدًا قبل التسجيل النهائي.

## BR-005

لا يجوز وجود أكثر من مستند حالي مصنف «الخطاب الرئيسي» للنسخة نفسها.

## BR-006

كل تعديل على مستند معتمد ينشئ نسخة جديدة ويلغي اعتماد النسخة السابقة.

## BR-007

كل مستلم في الإحالة المتعددة ينتج سجل `ACM Referral` مستقلًا.

## BR-008

إحالة «صورة» لا تنقل مسؤولية المعاملة الأساسية.

## BR-009

إحالة «خاص» لا تظهر لمنسق الإدارة العام إلا بصلاحية خاصة أو عند إعداد النظام بذلك.

## BR-010

تاريخ الاستحقاق الخاص بالإحالة مستقل عن تاريخ الاستحقاق العام للمعاملة.

## BR-011

لا يجوز تحديد تاريخ استحقاق سابق لتاريخ الإحالة.

## BR-012

التاريخ الهجري للعرض، بينما يُحفظ التاريخ الأساسي في قاعدة البيانات كـDate/Datetime ميلادي موحد.

## BR-013

حالة التأخير تحسب وفق سياسة SLA وأيام العمل والعطلات.

## BR-014

المرفق السري لا يرث تلقائيًا كل قارئي المعاملة؛ بل يخضع لصلاحية مستقلة.

## BR-015

لا يجوز حذف المعاملة بعد التسجيل. تستخدم حالة Cancelled مع سبب وسجل تدقيق.

## BR-016

تنزيل وطباعة المعاملات السرية يسجلان في `ACM Correspondence Action`.

## BR-017

عند طباعة مستند سري تضاف علامة مائية تحتوي على:

- اسم المستخدم.
- التاريخ والوقت.
- رقم المعاملة.
- عبارة سرية المستند.

## BR-018

التفويض لا يرفع صلاحيات المفوض إليه فوق صلاحيات المفوض.

## BR-019

عند ربط أكثر من معاملة، يُحفظ ترتيب الروابط وتحدد واحدة كرئيسية.

## BR-020

الباركود لا يحتوي بيانات سرية مباشرة؛ يحتوي معرفًا أو رمز تحقق فقط.

---

# 27. نموذج الصلاحيات

## 27.1 صلاحية القراءة

يسمح بقراءة المعاملة إذا تحقق أحد الشروط:

- المستخدم منشئها.
- المستخدم مسجلها.
- المستخدم مستلم إحالة فعالة.
- المستخدم ضمن الإدارة المستلمة ومخول بالوصول الجماعي.
- المستخدم مدير الإدارة بحسب التسلسل.
- المستخدم مستلم صورة.
- المستخدم مسؤول متابعة.
- المستخدم مفوض رسميًا.
- المستخدم مدقق معتمد.
- المستخدم لديه تصريح صريح لمستوى السرية.

## 27.2 صلاحية التعديل

- المسودة: المنشئ أو من يملك صلاحية تحرير المسودات.
- المسجلة: تعديلات محدودة عبر إجراءات مخصصة.
- تحت الاعتماد: يمنع تعديل النص والمرفق الرئيسي.
- المعتمدة: لا تعدل؛ تنشأ نسخة جديدة.
- المغلقة: قراءة فقط حتى إعادة التشغيل.

## 27.3 تنفيذ الصلاحيات في Frappe

يلزم استخدام:

- Role Permissions.
- User Permissions على Company وDepartment.
- `permission_query_conditions`.
- `has_permission`.
- التحقق داخل كل Whitelisted Method.
- منع الاعتماد على إخفاء الأزرار في الواجهة فقط.
- التحقق من صلاحية الملف عند التنزيل.
- منع الوصول المباشر إلى الملفات السرية.

---

# 28. واجهات النظام

## 28.1 Workspace

```text
أعمالي
├── إنشاء جديد
│   ├── معاملة داخلية
│   ├── واردة خارجية
│   └── صادرة خارجية
├── صندوق المعاملات
│   ├── الوارد إليّ
│   ├── غير المستلم
│   ├── قيد الإجراء
│   ├── للمتابعة
│   ├── صور المعاملات
│   └── المتأخر
├── المرسلة
├── المسودات
├── المغلقة
├── البحث المتقدم
├── المجلدات
├── بيانات التسليم
├── المهام
├── اللجان والاجتماعات
├── التقارير
└── الإعدادات
```

## 28.2 شاشة التسجيل

واجهة Wizard مخصصة:

```text
1. البيانات
2. المرفقات
3. الإحالة
```

### البيانات

- ربط بمعاملة أخرى.
- البيانات الرئيسية.
- بيانات الشخص المعني.
- المرفقات السرية.
- تفريغ الحقول.
- حفظ كمسودة.
- طباعة باركود.
- التالي.

### المرفقات

- مسح ضوئي.
- إرفاق من جهازك.
- النوع.
- المجلد.
- إرفاق ملف.
- تحميل.
- الخطاب الرئيسي.
- المرفقات.
- الرد.
- الأحدث.
- الأقدم.
- عرض شبكي.
- عرض قائمة.

### الإحالة

- إحالة متعددة.
- الجهات الخارجية عند انطباقها.
- إلى.
- التوجيه.
- الأهمية.
- الاستحقاق.
- تعليمات للمستقبل.
- خاص.
- مراسلة ورقية.
- صورة.
- للمتابعة.
- عمليات.
- إرسال.

---

# 29. صندوق المعاملات

## الأعمدة

- رقم المعاملة.
- النوع.
- الاتجاه.
- الموضوع.
- الجهة المرسلة.
- الجهة الحالية.
- التوجيه.
- السرية.
- الأهمية.
- تاريخ الإرسال.
- تاريخ الاستحقاق.
- الأيام المتبقية.
- الحالة.
- وجود مرفقات.
- خاص.
- صورة.
- للمتابعة.

## الألوان

- طبيعي: اللون الافتراضي.
- مستحق قريبًا: أصفر.
- مستحق اليوم: برتقالي.
- متأخر: أحمر.
- مكتمل: أخضر.
- مرفوض/معاد: لون تحذيري منفصل.

## الإجراءات

- فتح.
- استلام.
- رفض.
- إحالة.
- إعادة.
- إكمال.
- إضافة رد.
- طلب اعتماد.
- إضافة إلى مجلد.
- متابعة.
- طباعة.
- تتبع.

---

# 30. البحث المتقدم

## الحقول

- رقم المعاملة.
- السنة الهجرية.
- السنة الميلادية.
- الاتجاه: وارد/داخلي/صادر.
- أصل/نسخة.
- الموضوع.
- رقم الخطاب.
- الجهة الوارد منها.
- الجهة الصادر إليها.
- الإدارة.
- المستخدم.
- النوع.
- السرية.
- الأهمية.
- التوجيه.
- الحالة.
- تاريخ التسجيل من/إلى.
- تاريخ الخطاب من/إلى.
- تاريخ الاستحقاق من/إلى.
- متأخر فقط.
- يحتوي مرفقات.
- يحتوي مرفقات سرية.
- معاملات مرتبطة.
- بحث شامل.
- بحث محدد برقم المعاملة.

البحث في نص OCR يجب أن يكون اختياريًا ويخضع للسرية.

---

# 31. التقارير

1. المراسلات الواردة.
2. المراسلات الصادرة.
3. المعاملات الداخلية.
4. المعاملات المرسلة من المستخدم.
5. المعاملات المحالة من مدير الإدارة.
6. إنتاجية الموظفين.
7. إحصائية المعاملات لكل إدارة.
8. المعاملات المستحقة اليوم.
9. المعاملات المتأخرة.
10. متوسط زمن الاستلام.
11. متوسط زمن الإنجاز.
12. الإحالات المرفوضة.
13. الإحالات المسحوبة.
14. المعاملات المعاد تشغيلها.
15. المعاملات حسب السرية.
16. المعاملات حسب الأهمية.
17. المعاملات دون خطاب رئيسي.
18. الصادر غير المسلّم.
19. بيانات التسليم.
20. نشاط المستخدمين.
21. تنزيل وطباعة المستندات السرية.
22. استخدام التفويضات.
23. المرفقات حسب الحجم والنوع.
24. المعاملات حسب تصنيف الموضوع.
25. الالتزام باتفاقيات SLA.

---

# 32. الإشعارات

## إشعارات فورية وبريدية

- إحالة جديدة.
- إحالة خاصة.
- معاملة بانتظار الاستلام.
- رفض الإحالة.
- إعادة المعاملة.
- قرب الاستحقاق.
- استحقاق اليوم.
- تجاوز الاستحقاق.
- طلب اعتماد.
- اعتماد الخطاب.
- رفض الاعتماد.
- طلب توقيع.
- اكتمال التوقيع.
- سحب الإحالة.
- إعادة تشغيل المعاملة.
- تسليم الصادر.
- تعثر التكامل.
- انتهاء التفويض.
- اقتراب اجتماع أو مهمة.

## التصعيد

```text
قبل الاستحقاق
→ المستلم

عند الاستحقاق
→ المستلم + منسق الإدارة

بعد التأخير الأول
→ المستلم + المدير

بعد التأخير الثاني
→ المدير الأعلى أو مسؤول المتابعة
```

---

# 33. التكاملات

## 33.1 ERPNext

- User وEmployee.
- Department.
- Company.
- Contact وAddress.
- Project عند ربط المهام بالمشروعات.
- Holiday List لحساب أيام العمل.
- Email Account.
- File.

## 33.2 البريد الإلكتروني

- تحويل بريد إلى مسودة واردة.
- حفظ المرسل والموضوع والتاريخ.
- حفظ المرفقات.
- عدم التسجيل النهائي دون مراجعة.
- ربط الرد بالبريد الأصلي.
- منع إرسال الملفات السرية دون سياسة.

## 33.3 Active Directory/SSO

متطلبات اختيارية:

- OIDC أو OAuth/SAML عبر موفر الهوية.
- مزامنة المستخدم والاسم والبريد.
- تعطيل حساب النظام عند تعطيل الحساب المؤسسي.
- MFA لدى موفر الهوية.

## 33.4 الماسح الضوئي

خيارات التنفيذ:

1. رفع ملف PDF من جهاز المسح.
2. خدمة محلية Scanner Agent تتواصل مع الجهاز.
3. TWAIN/WIA Connector على أجهزة Windows.
4. تطبيق جوال للالتقاط إذا اعتُمد لاحقًا.

متصفح الويب لا يستطيع التحكم بجميع الماسحات مباشرة دون وسيط محلي.

## 33.5 الباركود

- QR افتراضي.
- Code 128 اختياري.
- طباعة ملصق.
- مسح الباركود لفتح المعاملة بعد التحقق من الصلاحية.
- عدم تضمين الموضوع أو السرية داخل الرمز.

يدعم Frappe حقول Barcode وواجهات مسح باستخدام كاميرا الجهاز.  
[Scanner API](https://docs.frappe.io/framework/user/en/api/scanner) — [Field Types](https://docs.frappe.io/framework/user/en/basics/doctypes/fieldtypes)

---

# 34. REST API المقترحة

## معاملات

```text
POST   /api/method/aamali_correspondence.api.create_draft
POST   /api/method/aamali_correspondence.api.register
GET    /api/method/aamali_correspondence.api.get_correspondence
POST   /api/method/aamali_correspondence.api.link_correspondence
POST   /api/method/aamali_correspondence.api.close
POST   /api/method/aamali_correspondence.api.reopen
POST   /api/method/aamali_correspondence.api.cancel
```

## إحالات

```text
POST /api/method/aamali_correspondence.api.refer
POST /api/method/aamali_correspondence.api.receive
POST /api/method/aamali_correspondence.api.reject
POST /api/method/aamali_correspondence.api.return_referral
POST /api/method/aamali_correspondence.api.complete_referral
POST /api/method/aamali_correspondence.api.withdraw_referral
```

## مستندات

```text
POST /api/method/aamali_correspondence.api.upload_document
GET  /api/method/aamali_correspondence.api.download_document
POST /api/method/aamali_correspondence.api.create_document_version
POST /api/method/aamali_correspondence.api.verify_document_hash
```

## اعتماد

```text
POST /api/method/aamali_correspondence.api.request_approval
POST /api/method/aamali_correspondence.api.approve
POST /api/method/aamali_correspondence.api.sign
POST /api/method/aamali_correspondence.api.return_for_revision
POST /api/method/aamali_correspondence.api.reject_approval
```

## بحث وتتبع

```text
GET /api/method/aamali_correspondence.api.search
GET /api/method/aamali_correspondence.api.timeline
GET /api/method/aamali_correspondence.api.inbox
GET /api/method/aamali_correspondence.api.statistics
```

كل API يجب أن:

- يتحقق من الجلسة أو API Token.
- يطبق الصلاحيات نفسها المطبقة في Desk.
- يمنع تمرير أسماء مستخدمين أو إدارات غير مسموحة.
- يسجل العمليات الحساسة.
- يستخدم Rate Limiting.
- يعيد معرف طلب للتتبع.

---

# 35. المتطلبات غير الوظيفية

## 35.1 الأداء

- فتح صندوق يحوي النتائج الأولى خلال 3 ثوانٍ في الظروف الطبيعية.
- البحث برقم المعاملة خلال ثانيتين.
- تحميل القوائم باستخدام Pagination.
- عدم تحميل المرفقات داخل List View.
- تنفيذ التقارير الثقيلة في Background Job.
- استخدام فهارس على:
    - رقم المعاملة.
    - الاتجاه.
    - الحالة.
    - الإدارة الحالية.
    - المستلم.
    - تاريخ الاستحقاق.
    - رقم الخطاب.
    - الجهة الخارجية.
    - السرية.
    - الأهمية.

## 35.2 السعة

خط أساس مقترح قابل للتعديل:

- مليون معاملة.
- 10 ملايين إحالة.
- 20 مليون ملف.
- 5,000 مستخدم.
- 500 مستخدم متزامن.
- ملفات حتى 25 MB افتراضيًا.

## 35.3 التوافر

- الهدف: 99.9% شهريًا، باستثناء الصيانة المخطط لها.
- مراقبة Web وWorkers وScheduler وRedis وقاعدة البيانات والتخزين.
- تنبيه عند فشل الوظائف الخلفية.

## 35.4 النسخ الاحتياطي

- نسخة قاعدة بيانات يومية على الأقل.
- نسخ ملفات Private وPublic.
- نسخ مشفر خارج الخادم.
- اختبار استعادة ربع سنوي.
- تحديد RPO وRTO تعاقديًا.

خط أساس مقترح:

- RPO: ساعة.
- RTO: أربع ساعات.

## 35.5 الأمن

- HTTPS فقط.
- MFA للمستخدمين ذوي الصلاحيات الحساسة.
- ملفات Private.
- تشفير التخزين أو القرص.
- إدارة أسرار خارج المستودع.
- التحقق من نوع وحجم الملف.
- فحص برمجيات خبيثة.
- منع الملفات التنفيذية.
- CSRF للحسابات المعتمدة على الجلسة.
- Rate Limiting.
- تسجيل التنزيل والطباعة للسرية.
- Content Security Policy.
- جلسات محدودة المدة.
- إلغاء الجلسات عند تعطيل المستخدم.
- مراجعة دورية للصلاحيات.
- اختبار اختراق قبل الإنتاج.

## 35.6 سهولة الاستخدام

- العربية RTL أساسية.
- الإنجليزية اختيارية.
- دعم سطح المكتب واللوحي.
- اختصارات لوحة مفاتيح.
- رسائل تحقق عربية واضحة.
- حفظ تلقائي للمسودة اختياري.
- منع فقدان البيانات عند مغادرة النموذج.
- إمكانية الوصول WCAG 2.1 AA قدر الإمكان.

---

# 36. سجل التدقيق

يجب تسجيل:

- الإنشاء والتسجيل.
- تعديل الحقول الحساسة.
- تغيير السرية.
- تغيير الأهمية.
- الإحالة.
- الاستلام.
- الرفض والإعادة.
- السحب.
- الاعتماد والتوقيع.
- إضافة أو استبدال ملف.
- التنزيل والطباعة للسرية.
- فتح معاملة سرية عند تفعيل التدقيق الموسع.
- الإغلاق وإعادة التشغيل.
- استخدام التفويض.
- محاولات الوصول المرفوضة.
- عمليات API الحساسة.

يجب منع تعديل `ACM Correspondence Action` من الواجهة، ولا يعتمد النظام على `Version` وحده لأن سجل Version ليس بديلًا كاملًا لسجل أمني مخصص.

---

# 37. الوظائف المجدولة

## كل خمس دقائق

- تحديث الإحالات المتأخرة.
- إرسال إشعارات الاستحقاق.
- معالجة طوابير التكامل.

## يوميًا

- حساب مؤشرات SLA.
- تنبيه التفويضات المنتهية.
- إحصائيات الإدارات.
- فحص معاملات بلا إجراء.
- أرشفة السجلات المؤهلة.

## أسبوعيًا

- تقرير المعاملات المتأخرة للمديرين.
- فحص المرفقات المفقودة.
- تقرير الصادر غير المسلّم.

## شهريًا

- مؤشرات إنتاجية الإدارات.
- تقرير الوصول للمعاملات السرية.
- تقرير استخدام التخزين.
- مراجعة التفويضات والصلاحيات المؤقتة.

---

# 38. Print Formats

1. بطاقة معاملة.
2. ملصق باركود.
3. خطاب داخلي.
4. خطاب صادر.
5. غلاف معاملة.
6. كشف إحالات.
7. بيان تسليم.
8. إيصال استلام.
9. تقرير تتبع المعاملة.
10. محضر اجتماع.
11. قرار لجنة.
12. تقرير معاملات متأخرة.
13. تقرير إنتاجية.
14. نسخة بعلامة مائية.

---

# 39. حالات الاستخدام الرئيسية

## UC-01 تسجيل وارد خارجي

1. يفتح الموظف «تسجيل معاملة واردة خارجية».
2. يدخل بيانات الجهة والخطاب.
3. يحدد السرية والأهمية.
4. يضيف المستند الرئيسي.
5. يضيف المرفقات.
6. يربط معاملات سابقة.
7. يحدد المستلمين.
8. يرسل.
9. يولد النظام رقم المعاملة والإحالات.
10. يرسل الإشعارات.

## UC-02 استلام إحالة

1. تظهر المعاملة في «غير المستلم».
2. يفتح المستخدم الملخص المسموح.
3. يختار «استلام».
4. يسجل النظام الوقت والمستخدم.
5. تتحول إلى In Progress.

## UC-03 رفض إحالة

1. يختار المستخدم «رفض».
2. يحدد السبب.
3. يكتب الملاحظة عند الحاجة.
4. تعاد إلى المرسل.
5. يرسل النظام إشعارًا.
6. يسجل الحدث.

## UC-04 إعداد رد صادر

1. يفتح المختص المعاملة الواردة.
2. يختار «إضافة رد».
3. ينشئ خطابًا إلكترونيًا.
4. يرفع المسودة.
5. يرسل للمراجعة والاعتماد.
6. يعتمد ويوقع الخطاب.
7. يسجله موظف الصادر.
8. يجهزه للتسليم.
9. يسجل إثبات التسليم.
10. يغلق المعاملة.

## UC-05 إحالة متعددة

1. يختار المستخدم «إحالة متعددة».
2. يضيف عدة مستلمين.
3. يحدد توجيهًا واستحقاقًا لكل مستلم.
4. يرسل.
5. ينشئ النظام إحالة مستقلة لكل صف.
6. تبقى حالة كل إحالة مستقلة.

---

# 40. معايير القبول العامة

يُعد النظام مقبولًا عندما:

1. يمكن تسجيل الداخلي والوارد والصادر.
2. يعمل المعالج الثلاثي دون فقد بيانات.
3. تُولد أرقام فريدة.
4. يمكن حفظ المسودة واستكمالها.
5. تعمل الإحالة الفردية والمتعددة.
6. تعمل حالات الاستلام والرفض والإكمال والسحب.
7. لا تظهر المعاملة لغير المخولين.
8. لا يمكن الوصول إلى مرفق سري برابط مباشر دون صلاحية.
9. يسجل التتبع كل انتقال.
10. يظهر تاريخ الاستحقاق الهجري والميلادي بصورة صحيحة.
11. تعمل إشعارات التأخير.
12. يمكن طباعة الباركود ومسحه.
13. يمكن ربط المعاملات.
14. يعمل مسار الاعتماد والتوقيع.
15. ينتج الصادر بيان تسليم.
16. تعمل التفويضات ضمن الفترة فقط.
17. تعرض التقارير البيانات وفق صلاحية المستخدم.
18. لا يمكن حذف معاملة مسجلة.
19. يحتفظ النظام بالنسخ السابقة للمستندات.
20. تنجح استعادة نسخة احتياطية في بيئة الاختبار.

---

# 41. مراحل التنفيذ المقترحة

## المرحلة الأولى: الأساس

- التطبيق والوحدة.
- البيانات المرجعية.
- الإدارات والمستخدمون.
- المعاملة الرئيسية.
- الوارد والداخلي والصادر.
- المرفقات.
- الإحالات.
- صندوق المعاملات.
- الصلاحيات.
- التتبع.

## المرحلة الثانية: الإجراءات المتقدمة

- الاعتماد.
- التوقيع.
- الردود.
- السحب والإعادة.
- الإغلاق وإعادة التشغيل.
- التفويضات.
- المجلدات.
- المتابعة.

## المرحلة الثالثة: التسليم والتقارير

- الباركود.
- النسخ الورقية.
- بيانات التسليم.
- مؤشرات SLA.
- التقارير.
- لوحات المعلومات.

## المرحلة الرابعة: المهام واللجان

- إدارة المهام.
- الاجتماعات.
- اللجان.
- القرارات.
- ربط القرارات بالمهام والمعاملات.

## المرحلة الخامسة: التكامل والأمن المتقدم

- SSO.
- البريد.
- OCR.
- الماسح المحلي.
- التوقيع الرقمي الخارجي.
- التخزين الخارجي.
- التكاملات الحكومية.

---

# 42. قرارات معمارية نهائية

1. **المعاملة ليست Frappe Workflow فقط**؛ بل DocType رئيسي مع Referral مستقل.
2. كل مستلم ينتج Referral مستقلًا.
3. المرفقات الحساسة تحفظ كسجلات مستقلة مرتبطة بملفات Private.
4. لا تستخدم Child Table للإحالات المنفذة؛ يستخدم Child Table فقط قبل الإرسال.
5. Department هو المرجع التنظيمي الأساسي.
6. User هو الهوية الأمنية، وEmployee هو الملف الوظيفي.
7. التاريخ الميلادي هو قيمة التخزين الأساسية، والهجري قيمة عرض أو قيمة مشتقة.
8. السجلات المسجلة لا تُحذف.
9. كل اعتماد يرتبط بنسخة محددة من المستند.
10. الباركود لا يحمل معلومات سرية.
11. الصلاحية تطبق في الخادم وليس الواجهة فقط.
12. يجب أن يكون التطبيق Custom App في Git، لا مجرد Customizations داخل قاعدة البيانات.
13. يجب تضمين Custom Fields وRoles وWorkflows وPrint Formats وReports في Fixtures أو ملفات التطبيق.
14. يجب تثبيت إصدارات Frappe وERPNext في الإنتاج وعدم التحديث دون اختبار Migration وRegression.
15. جميع التسميات العربية تحفظ في ملفات الترجمة، بينما تستخدم أسماء DocTypes وfieldnames الإنجليزية المستقرة برمجيًا.

هذه الوثيقة تمثل **SRS تنفيذية كاملة للإصدار الأول من النظام**، وتشمل نموذج البيانات، الـDocTypes، الحقول، الأدوار، دورات العمل، الأمن، التقارير، التكاملات، الاختبارات ومعايير القبول. وهي مصممة بحيث يستطيع فريق Frappe البدء منها مباشرة في إعداد التطبيق والـDocTypes والـWorkflows دون الاعتماد على التخمينات العامة حول نظام المراسلات.