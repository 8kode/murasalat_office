# المرحلة الأولى — Murasalat Office

## 1. الهوية النهائية للتطبيق

```ini
app_name=murasalat_office
app_title=Murasalat Office
module=Murasalat Office
doctype_prefix=Murasalat
```

جميع أسماء النظام وحقوله الأساسية ستكون بالإنجليزية، وتُعرض بالعربية من خلال:

```text
murasalat_office/translations/ar.csv
```

الاستبدال المعتمد:

```text
ACM Correspondence     → Murasalat Correspondence
ACM Settings           → Murasalat Settings
ACM External Party     → Murasalat External Party
ACM Referral           → Murasalat Referral
```

---

# 2. نطاق المرحلة الأولى

المرحلة الأولى تنتج نظامًا تشغيليًا يشمل:

1. إنشاء تطبيق `murasalat_office`.
2. إعداد Module باسم `Murasalat Office`.
3. إعداد Workspace.
4. إنشاء الأدوار والصلاحيات.
5. إنشاء جداول الإعدادات والقواميس.
6. تسجيل:
    - Internal Correspondence.
    - External Incoming Correspondence.
    - External Outgoing Correspondence.
7. ربط المعاملات.
8. بيانات الشخص المعني.
9. المرفقات العادية والسرية.
10. إنشاء الإحالات وإرسالها.
11. صندوق الوارد والصادر والإحالات المنجزة.
12. حفظ المسودات.
13. ترقيم المعاملات.
14. البحث الأساسي والمتقدم.
15. التفويضات.
16. سجل تدقيق أولي.
17. واجهة إنجليزية مع ترجمة عربية RTL.

اعتمادًا على الصور، ستكون شاشة تسجيل المعاملة مكوّنة من:

```text
Step 1: Data
Step 2: Attachments
Step 3: Referral
```

---

# 3. القرارات المعمارية للمرحلة الأولى

## 3.1 المعاملة الرئيسة

ستُخزن جميع أنواع المعاملات في:

```text
Murasalat Correspondence
```

ويحدد الحقل التالي نوعها:

```text
direction:
- Internal
- Incoming
- Outgoing
```

## 3.2 الإحالة

ستكون الإحالة DocType مستقلًا:

```text
Murasalat Referral
```

كل صف ظاهر في خطوة Referral ينشئ سجل إحالة مستقلًا. هذا يسمح بأن تكون لكل إحالة:

- مستلم مستقل.
- تاريخ استحقاق مستقل.
- توجيه مستقل.
- حالة مستقلة.
- متابعة مستقلة.
- وقت إرسال واستلام وإنجاز مستقل.

## 3.3 المرفقات

سيكون المستند DocType مستقلًا:

```text
Murasalat Correspondence Document
```

وليس مجرد Attach field داخل Child Table، وذلك لتطبيق صلاحيات مستقلة على المرفقات السرية. توثيق Frappe يوضح أن المستخدم الذي يستطيع قراءة المستند المرتبط يستطيع عادة الوصول إلى ملفاته؛ لذلك يجب فرض صلاحية إضافية على المستندات السرية وعدم الاعتماد على إخفاء الحقل فقط:  
[https://docs.frappe.io/framework/user/en/desk/attachments](https://docs.frappe.io/framework/user/en/desk/attachments)

## 3.4 التواريخ الهجرية

يُخزن التاريخ الميلادي في حقول من نوع `Date`، أما التاريخ الهجري فيُخزن كقيمة عرض محسوبة:

```text
letter_date          → Date
letter_date_hijri    → Data, read-only

due_date             → Date
due_date_hijri       → Data, read-only
```

## 3.5 الجداول الفرعية

تُستخدم Child DocTypes للبيانات التي لا يكون لها وجود مستقل، مثل:

- روابط المعاملات.
- الأشخاص المعنيين.

Frappe يربط Child DocType بالأب من خلال `parent`, `parenttype`, `parentfield`, و`idx`:  
[https://docs.frappe.io/framework/user/en/basics/doctypes/child-doctype](https://docs.frappe.io/framework/user/en/basics/doctypes/child-doctype)

---

# 4. إنشاء التطبيق

## 4.1 إنشاء التطبيق

من داخل مجلد Bench:

```bash
cd ~/frappe-bench
bench new-app murasalat_office
```

الإجابات المقترحة:

```text
App Title: Murasalat Office
App Description: Electronic correspondence and administrative transaction management system
App Publisher: Your Company Name
App Email: development@example.com
App License: MIT
```

إنشاء التطبيق باستخدام `bench new-app` هو الأسلوب الرسمي في Frappe:  
[https://docs.frappe.io/framework/user/en/tutorial/create-an-app](https://docs.frappe.io/framework/user/en/tutorial/create-an-app)

## 4.2 إنشاء الموقع أو استخدام موقع موجود

```bash
bench new-site murasalat.local
```

ثم تثبيت ERPNext والتطبيق:

```bash
bench --site murasalat.local install-app erpnext
bench --site murasalat.local install-app murasalat_office
```

## 4.3 تفعيل Developer Mode

```bash
bench set-config -g developer_mode 1
bench --site murasalat.local clear-cache
```

Developer Mode مطلوب حتى تُكتب تغييرات DocTypes إلى ملفات JSON داخل التطبيق:  
[https://docs.frappe.io/framework/user/en/guides/app-development/how-enable-developer-mode-in-frappe](https://docs.frappe.io/framework/user/en/guides/app-development/how-enable-developer-mode-in-frappe)

## 4.4 ملف Module

المسار:

```text
apps/murasalat_office/murasalat_office/modules.txt
```

المحتوى:

```text
Murasalat Office
```

## 4.5 هيكل الملفات

```text
apps/murasalat_office/
└── murasalat_office/
    ├── hooks.py
    ├── modules.txt
    ├── patches.txt
    ├── translations/
    │   └── ar.csv
    └── murasalat_office/
        ├── doctype/
        │   ├── murasalat_settings/
        │   ├── murasalat_correspondence_type/
        │   ├── murasalat_external_party/
        │   ├── murasalat_confidentiality_level/
        │   ├── murasalat_priority_level/
        │   ├── murasalat_routing_purpose/
        │   ├── murasalat_document_category/
        │   ├── murasalat_numbering_rule/
        │   ├── murasalat_correspondence/
        │   ├── murasalat_correspondence_link/
        │   ├── murasalat_concerned_person/
        │   ├── murasalat_correspondence_document/
        │   ├── murasalat_referral/
        │   └── murasalat_delegation/
        ├── report/
        └── workspace/
```

---

# 5. أدوار المرحلة الأولى

|Role|التسمية|الاستخدام|
|---|---|---|
|Murasalat User|مستخدم المراسلات|الاطلاع على معاملاته وإحالاته|
|Murasalat Clerk|موظف تسجيل المراسلات|تسجيل المعاملات وحفظ المسودات|
|Murasalat Manager|مدير المراسلات|الإحالة والإغلاق والإشراف|
|Murasalat Auditor|مدقق المراسلات|القراءة والتقارير والتدقيق|
|Murasalat System Manager|مدير نظام المراسلات|الإعدادات والقواميس والصلاحيات|

> صلاحيات السرية، الإدارة، المستلم، والتفويض تحتاج أيضًا إلى Permission Query برمجي؛ Role Permissions وحدها لا تكفي لعزل كل سجل.

---

# 6. قائمة DocTypes في المرحلة الأولى

|#|DocType|النوع|
|---|---|---|
|1|Murasalat Settings|Single|
|2|Murasalat Correspondence Type|Master|
|3|Murasalat External Party|Master|
|4|Murasalat Confidentiality Level|Master|
|5|Murasalat Priority Level|Master|
|6|Murasalat Routing Purpose|Master|
|7|Murasalat Document Category|Master|
|8|Murasalat Numbering Rule|Master|
|9|Murasalat Correspondence|Transaction|
|10|Murasalat Correspondence Link|Child Table|
|11|Murasalat Concerned Person|Child Table|
|12|Murasalat Correspondence Document|Transaction|
|13|Murasalat Referral|Transaction|
|14|Murasalat Delegation|Transaction|

---

# 7. DocType: Murasalat Settings

## الإعدادات

| Setting       | Value                                              |
| ------------- | -------------------------------------------------- |
| Name          | Murasalat Settings                                 |
| Module        | Murasalat Office                                   |
| Is Single     | Yes                                                |
| Track Changes | Yes                                                |
| Editable By   | Murasalat System Manager                           |
| Description   | Global configuration for correspondence management |

## جدول الحقول

| Fieldname                   | English Label                              | التسمية                             | Type          | Required | Options/Default                 |
| --------------------------- | ------------------------------------------ | ----------------------------------- | ------------- | -------- | ------------------------------- |
| organization_section        | Organization                               | المؤسسة                             | Section Break | No       |                                 |
| company                     | Company                                    | الشركة                              | Link          | Yes      | Company                         |
| default_department          | Default Department                         | الإدارة الافتراضية                  | Link          | No       | Department                      |
| defaults_section            | Defaults                                   | القيم الافتراضية                    | Section Break | No       |                                 |
| default_confidentiality     | Default Confidentiality                    | السرية الافتراضية                   | Link          | Yes      | Murasalat Confidentiality Level |
| default_priority            | Default Priority                           | الأهمية الافتراضية                  | Link          | Yes      | Murasalat Priority Level        |
| default_routing_purpose     | Default Routing Purpose                    | غرض التوجيه الافتراضي               | Link          | No       | Murasalat Routing Purpose       |
| dates_section               | Dates                                      | التواريخ                            | Section Break | No       |                                 |
| hijri_date_enabled          | Enable Hijri Dates                         | تفعيل التواريخ الهجرية              | Check         | No       | 1                               |
| default_due_days            | Default Due Days                           | أيام الاستحقاق الافتراضية           | Int           | No       | 5                               |
| attachments_section         | Attachments                                | المرفقات                            | Section Break | No       |                                 |
| maximum_attachment_size_mb  | Maximum Attachment Size MB                 | الحد الأقصى لحجم المرفق بالميجابايت | Int           | Yes      | 10                              |
| allow_secret_attachments    | Allow Secret Attachments                   | السماح بالمرفقات السرية             | Check         | No       | 1                               |
| allowed_file_extensions     | Allowed File Extensions                    | امتدادات الملفات المسموحة           | Small Text    | No       | pdf,jpg,jpeg,png,docx,xlsx      |
| controls_section            | Controls                                   | الضوابط                             | Section Break | No       |                                 |
| prevent_registered_deletion | Prevent Registered Correspondence Deletion | منع حذف المعاملات المسجلة           | Check         | No       | 1                               |
| enable_barcode              | Enable Barcode                             | تفعيل الباركود                      | Check         | No       | 1                               |
| enable_audit_log            | Enable Audit Log                           | تفعيل سجل التدقيق                   | Check         | No       | 1                               |

## JSON

المسار:

```text
murasalat_office/murasalat_office/doctype/murasalat_settings/murasalat_settings.json
```

```json
{
  "actions": [],
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "organization_section",
    "company",
    "default_department",
    "defaults_section",
    "default_confidentiality",
    "default_priority",
    "default_routing_purpose",
    "dates_section",
    "hijri_date_enabled",
    "default_due_days",
    "attachments_section",
    "maximum_attachment_size_mb",
    "allow_secret_attachments",
    "allowed_file_extensions",
    "controls_section",
    "prevent_registered_deletion",
    "enable_barcode",
    "enable_audit_log"
  ],
  "fields": [
    {"fieldname":"organization_section","fieldtype":"Section Break","label":"Organization"},
    {"fieldname":"company","fieldtype":"Link","label":"Company","options":"Company","reqd":1},
    {"fieldname":"default_department","fieldtype":"Link","label":"Default Department","options":"Department"},
    {"fieldname":"defaults_section","fieldtype":"Section Break","label":"Defaults"},
    {"fieldname":"default_confidentiality","fieldtype":"Link","label":"Default Confidentiality","options":"Murasalat Confidentiality Level","reqd":1},
    {"fieldname":"default_priority","fieldtype":"Link","label":"Default Priority","options":"Murasalat Priority Level","reqd":1},
    {"fieldname":"default_routing_purpose","fieldtype":"Link","label":"Default Routing Purpose","options":"Murasalat Routing Purpose"},
    {"fieldname":"dates_section","fieldtype":"Section Break","label":"Dates"},
    {"default":"1","fieldname":"hijri_date_enabled","fieldtype":"Check","label":"Enable Hijri Dates"},
    {"default":"5","fieldname":"default_due_days","fieldtype":"Int","label":"Default Due Days"},
    {"fieldname":"attachments_section","fieldtype":"Section Break","label":"Attachments"},
    {"default":"10","fieldname":"maximum_attachment_size_mb","fieldtype":"Int","label":"Maximum Attachment Size MB","reqd":1},
    {"default":"1","fieldname":"allow_secret_attachments","fieldtype":"Check","label":"Allow Secret Attachments"},
    {"default":"pdf,jpg,jpeg,png,docx,xlsx","fieldname":"allowed_file_extensions","fieldtype":"Small Text","label":"Allowed File Extensions"},
    {"fieldname":"controls_section","fieldtype":"Section Break","label":"Controls"},
    {"default":"1","fieldname":"prevent_registered_deletion","fieldtype":"Check","label":"Prevent Registered Correspondence Deletion"},
    {"default":"1","fieldname":"enable_barcode","fieldtype":"Check","label":"Enable Barcode"},
    {"default":"1","fieldname":"enable_audit_log","fieldtype":"Check","label":"Enable Audit Log"}
  ],
  "issingle": 1,
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Settings",
  "permissions": [
    {
      "role": "Murasalat System Manager",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1
    },
    {
      "role": "System Manager",
      "read": 1,
      "write": 1,
      "create": 1,
      "delete": 1
    }
  ],
  "sort_field": "modified",
  "sort_order": "DESC",
  "track_changes": 1
}
```

---

# 8. DocType: Murasalat Correspondence Type

## الإعدادات

|Setting|Value|
|---|---|
|Type|Master|
|Auto Name|field:type_name|
|Title Field|type_name|
|Search Fields|type_name,code,direction|
|Track Changes|Yes|

## الحقول

|Fieldname|English Label|التسمية|Type|Required|Options|
|---|---|---|---|---|---|
|type_name|Type Name|اسم النوع|Data|Yes|Unique|
|code|Code|الرمز|Data|Yes|Unique|
|direction|Direction|اتجاه المعاملة|Select|Yes|Internal/Incoming/Outgoing|
|requires_external_party|Requires External Party|يتطلب جهة خارجية|Check|No||
|requires_letter_number|Requires Letter Number|يتطلب رقم خطاب|Check|No||
|requires_letter_date|Requires Letter Date|يتطلب تاريخ خطاب|Check|No||
|is_active|Is Active|نشط|Check|No|Default 1|
|description|Description|الوصف|Small Text|No||

## JSON

```json
{
  "actions": [],
  "autoname": "field:type_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "type_name",
    "code",
    "direction",
    "requires_external_party",
    "requires_letter_number",
    "requires_letter_date",
    "is_active",
    "description"
  ],
  "fields": [
    {"fieldname":"type_name","fieldtype":"Data","label":"Type Name","reqd":1,"unique":1},
    {"fieldname":"code","fieldtype":"Data","label":"Code","reqd":1,"unique":1},
    {"fieldname":"direction","fieldtype":"Select","label":"Direction","options":"Internal\nIncoming\nOutgoing","reqd":1},
    {"fieldname":"requires_external_party","fieldtype":"Check","label":"Requires External Party"},
    {"fieldname":"requires_letter_number","fieldtype":"Check","label":"Requires Letter Number"},
    {"fieldname":"requires_letter_date","fieldtype":"Check","label":"Requires Letter Date"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"},
    {"fieldname":"description","fieldtype":"Small Text","label":"Description"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Correspondence Type",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "search_fields": "type_name,code,direction",
  "show_name_in_global_search": 1,
  "sort_field": "type_name",
  "sort_order": "ASC",
  "title_field": "type_name",
  "track_changes": 1
}
```

---

# 9. DocType: Murasalat External Party

## الإعدادات

|Setting|Value|
|---|---|
|Type|Master|
|Auto Name|field:party_name|
|Title Field|party_name|
|Search Fields|party_name,short_name,party_type,city|
|Tree|No|

## الحقول

|Fieldname|English Label|التسمية|Type|Required|Options|
|---|---|---|---|---|---|
|party_name|Party Name|اسم الجهة|Data|Yes|Unique|
|short_name|Short Name|الاسم المختصر|Data|No||
|party_type|Party Type|نوع الجهة|Select|Yes|Government/Private/Individual/Other|
|parent_party|Parent Party|الجهة الأم|Link|No|Murasalat External Party|
|city|City|المدينة|Data|No||
|country|Country|الدولة|Link|No|Country|
|email|Email|البريد الإلكتروني|Data|No|Email|
|phone|Phone|الهاتف|Data|No||
|address|Address|العنوان|Small Text|No||
|is_active|Is Active|نشط|Check|No|Default 1|
|notes|Notes|ملاحظات|Small Text|No||

## JSON

```json
{
  "actions": [],
  "autoname": "field:party_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "party_name",
    "short_name",
    "party_type",
    "parent_party",
    "city",
    "country",
    "contact_section",
    "email",
    "phone",
    "address",
    "is_active",
    "notes"
  ],
  "fields": [
    {"fieldname":"party_name","fieldtype":"Data","label":"Party Name","reqd":1,"unique":1},
    {"fieldname":"short_name","fieldtype":"Data","label":"Short Name"},
    {"fieldname":"party_type","fieldtype":"Select","label":"Party Type","options":"Government\nPrivate\nIndividual\nOther","reqd":1},
    {"fieldname":"parent_party","fieldtype":"Link","label":"Parent Party","options":"Murasalat External Party"},
    {"fieldname":"city","fieldtype":"Data","label":"City"},
    {"fieldname":"country","fieldtype":"Link","label":"Country","options":"Country"},
    {"fieldname":"contact_section","fieldtype":"Section Break","label":"Contact Information"},
    {"fieldname":"email","fieldtype":"Data","label":"Email","options":"Email"},
    {"fieldname":"phone","fieldtype":"Data","label":"Phone"},
    {"fieldname":"address","fieldtype":"Small Text","label":"Address"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"},
    {"fieldname":"notes","fieldtype":"Small Text","label":"Notes"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat External Party",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1,"write":1,"create":1},
    {"role":"Murasalat Manager","read":1,"write":1,"create":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "search_fields": "party_name,short_name,party_type,city",
  "show_name_in_global_search": 1,
  "sort_field": "party_name",
  "sort_order": "ASC",
  "title_field": "party_name",
  "track_changes": 1
}
```

---

# 10. DocType: Murasalat Confidentiality Level

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|level_name|Level Name|اسم مستوى السرية|Data|Yes|
|code|Code|الرمز|Data|Yes|
|rank|Rank|ترتيب السرية|Int|Yes|
|color|Color|اللون|Color|No|
|restrict_access|Restrict Access|تقييد الوصول|Check|No|
|is_active|Is Active|نشط|Check|No|
|description|Description|الوصف|Small Text|No|

## JSON

```json
{
  "actions": [],
  "autoname": "field:level_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "level_name",
    "code",
    "rank",
    "color",
    "restrict_access",
    "is_active",
    "description"
  ],
  "fields": [
    {"fieldname":"level_name","fieldtype":"Data","label":"Level Name","reqd":1,"unique":1},
    {"fieldname":"code","fieldtype":"Data","label":"Code","reqd":1,"unique":1},
    {"fieldname":"rank","fieldtype":"Int","label":"Rank","reqd":1},
    {"fieldname":"color","fieldtype":"Color","label":"Color"},
    {"fieldname":"restrict_access","fieldtype":"Check","label":"Restrict Access"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"},
    {"fieldname":"description","fieldtype":"Small Text","label":"Description"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Confidentiality Level",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "rank",
  "sort_order": "ASC",
  "title_field": "level_name",
  "track_changes": 1
}
```

### السجلات الأولية

|Level Name|Code|Rank|Color|
|---|---|---|---|
|Normal|NORMAL|10|Green|
|Confidential|CONFIDENTIAL|20|Orange|
|Secret|SECRET|30|Red|
|Top Secret|TOP-SECRET|40|Dark Red|

---

# 11. DocType: Murasalat Priority Level

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|priority_name|Priority Name|اسم درجة الأهمية|Data|Yes|
|code|Code|الرمز|Data|Yes|
|rank|Rank|الترتيب|Int|Yes|
|color|Color|اللون|Color|No|
|default_due_days|Default Due Days|أيام الاستحقاق الافتراضية|Int|No|
|is_active|Is Active|نشط|Check|No|

## JSON

```json
{
  "actions": [],
  "autoname": "field:priority_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "priority_name",
    "code",
    "rank",
    "color",
    "default_due_days",
    "is_active"
  ],
  "fields": [
    {"fieldname":"priority_name","fieldtype":"Data","label":"Priority Name","reqd":1,"unique":1},
    {"fieldname":"code","fieldtype":"Data","label":"Code","reqd":1,"unique":1},
    {"fieldname":"rank","fieldtype":"Int","label":"Rank","reqd":1},
    {"fieldname":"color","fieldtype":"Color","label":"Color"},
    {"fieldname":"default_due_days","fieldtype":"Int","label":"Default Due Days"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Priority Level",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "rank",
  "sort_order": "ASC",
  "title_field": "priority_name",
  "track_changes": 1
}
```

### السجلات الأولية من مفتاح الألوان الظاهر في الصور

```text
Normal
Urgent
Very Urgent
Immediate
```

---

# 12. DocType: Murasalat Routing Purpose

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|purpose_name|Purpose Name|غرض التوجيه|Data|Yes|
|code|Code|الرمز|Data|Yes|
|requires_response|Requires Response|يتطلب ردًا|Check|No|
|closes_on_completion|Closes on Completion|يغلق عند الإنجاز|Check|No|
|is_active|Is Active|نشط|Check|No|
|description|Description|الوصف|Small Text|No|

## JSON

```json
{
  "actions": [],
  "autoname": "field:purpose_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "purpose_name",
    "code",
    "requires_response",
    "closes_on_completion",
    "is_active",
    "description"
  ],
  "fields": [
    {"fieldname":"purpose_name","fieldtype":"Data","label":"Purpose Name","reqd":1,"unique":1},
    {"fieldname":"code","fieldtype":"Data","label":"Code","reqd":1,"unique":1},
    {"fieldname":"requires_response","fieldtype":"Check","label":"Requires Response"},
    {"fieldname":"closes_on_completion","fieldtype":"Check","label":"Closes on Completion"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"},
    {"fieldname":"description","fieldtype":"Small Text","label":"Description"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Routing Purpose",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "purpose_name",
  "sort_order": "ASC",
  "title_field": "purpose_name",
  "track_changes": 1
}
```

### السجلات الأولية المطابقة للصور

```text
For Signature
For Necessary Action
For Review
For Approval
For Circulation
For Study and Opinion
```

---

# 13. DocType: Murasalat Document Category

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|category_name|Category Name|اسم تصنيف المستند|Data|Yes|
|code|Code|الرمز|Data|Yes|
|display_order|Display Order|ترتيب العرض|Int|No|
|allow_multiple|Allow Multiple|السماح بأكثر من ملف|Check|No|
|is_active|Is Active|نشط|Check|No|
|description|Description|الوصف|Small Text|No|

## JSON

```json
{
  "actions": [],
  "autoname": "field:category_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "category_name",
    "code",
    "display_order",
    "allow_multiple",
    "is_active",
    "description"
  ],
  "fields": [
    {"fieldname":"category_name","fieldtype":"Data","label":"Category Name","reqd":1,"unique":1},
    {"fieldname":"code","fieldtype":"Data","label":"Code","reqd":1,"unique":1},
    {"fieldname":"display_order","fieldtype":"Int","label":"Display Order"},
    {"default":"1","fieldname":"allow_multiple","fieldtype":"Check","label":"Allow Multiple"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"},
    {"fieldname":"description","fieldtype":"Small Text","label":"Description"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Document Category",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "display_order",
  "sort_order": "ASC",
  "title_field": "category_name",
  "track_changes": 1
}
```

### السجلات الأولية المطابقة للصور

```text
Main Letter
Attachments
Reply
```

---

# 14. DocType: Murasalat Numbering Rule

## الإعدادات

هذا DocType يدير الترقيم حسب اتجاه المعاملة ونوعها.

مثال:

```text
Incoming:  IN-.YYYY.-.######
Outgoing:  OUT-.YYYY.-.######
Internal:  INT-.YYYY.-.######
```

Frappe يدعم Naming Series وExpression naming، ويوصي بعدم استخدام صيغة Expression القديمة المهملة في الإصدار 16:  
[https://docs.frappe.io/framework/user/en/basics/doctypes/naming](https://docs.frappe.io/framework/user/en/basics/doctypes/naming)

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|rule_name|Rule Name|اسم قاعدة الترقيم|Data|Yes|
|direction|Direction|اتجاه المعاملة|Select|Yes|
|correspondence_type|Correspondence Type|نوع المعاملة|Link|No|
|prefix|Prefix|بادئة الرقم|Data|Yes|
|digits|Number of Digits|عدد الخانات|Int|Yes|
|include_year|Include Year|تضمين السنة|Check|No|
|year_type|Year Type|نوع السنة|Select|No|
|is_default|Is Default|افتراضي|Check|No|
|is_active|Is Active|نشط|Check|No|

## JSON

```json
{
  "actions": [],
  "autoname": "field:rule_name",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "rule_name",
    "direction",
    "correspondence_type",
    "prefix",
    "digits",
    "include_year",
    "year_type",
    "is_default",
    "is_active"
  ],
  "fields": [
    {"fieldname":"rule_name","fieldtype":"Data","label":"Rule Name","reqd":1,"unique":1},
    {"fieldname":"direction","fieldtype":"Select","label":"Direction","options":"Internal\nIncoming\nOutgoing","reqd":1},
    {"fieldname":"correspondence_type","fieldtype":"Link","label":"Correspondence Type","options":"Murasalat Correspondence Type"},
    {"fieldname":"prefix","fieldtype":"Data","label":"Prefix","reqd":1},
    {"default":"6","fieldname":"digits","fieldtype":"Int","label":"Number of Digits","reqd":1},
    {"default":"1","fieldname":"include_year","fieldtype":"Check","label":"Include Year"},
    {"default":"Gregorian","depends_on":"include_year","fieldname":"year_type","fieldtype":"Select","label":"Year Type","options":"Gregorian\nHijri"},
    {"fieldname":"is_default","fieldtype":"Check","label":"Is Default"},
    {"default":"1","fieldname":"is_active","fieldtype":"Check","label":"Is Active"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Numbering Rule",
  "permissions": [
    {"role":"Murasalat User","read":1},
    {"role":"Murasalat Clerk","read":1},
    {"role":"Murasalat Manager","read":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "rule_name",
  "sort_order": "ASC",
  "title_field": "rule_name",
  "track_changes": 1
}
```

---

# 15. DocType: Murasalat Correspondence Link

## الإعدادات

|Setting|Value|
|---|---|
|Is Child Table|Yes|
|Editable Grid|Yes|
|Independent Permissions|No|
|Parent|Murasalat Correspondence|

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|linked_correspondence|Linked Correspondence|المعاملة المرتبطة|Link|Yes|
|relationship_type|Relationship Type|نوع العلاقة|Select|Yes|
|is_primary_reference|Primary Reference|المرجع الرئيسي|Check|No|
|notes|Notes|ملاحظات|Small Text|No|

## JSON

```json
{
  "actions": [],
  "doctype": "DocType",
  "editable_grid": 1,
  "engine": "InnoDB",
  "field_order": [
    "linked_correspondence",
    "relationship_type",
    "is_primary_reference",
    "notes"
  ],
  "fields": [
    {"fieldname":"linked_correspondence","fieldtype":"Link","in_list_view":1,"label":"Linked Correspondence","options":"Murasalat Correspondence","reqd":1},
    {"default":"Related","fieldname":"relationship_type","fieldtype":"Select","in_list_view":1,"label":"Relationship Type","options":"Related\nReply To\nFollow-up To\nReference\nSupersedes","reqd":1},
    {"fieldname":"is_primary_reference","fieldtype":"Check","in_list_view":1,"label":"Primary Reference"},
    {"fieldname":"notes","fieldtype":"Small Text","label":"Notes"}
  ],
  "istable": 1,
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Correspondence Link",
  "permissions": []
}
```

### قاعدة العمل

إذا أُضيف أكثر من رابط ولم يُحدد المرجع الرئيسي:

```text
The first linked correspondence becomes the primary reference.
```

---

# 16. DocType: Murasalat Concerned Person

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|person_type|Person Type|نوع الشخص|Select|Yes|
|employee|Employee|الموظف|Link|Conditional|
|full_name|Full Name|الاسم الكامل|Data|Conditional|
|national_id|National ID|رقم الهوية|Data|No|
|mobile_number|Mobile Number|رقم الجوال|Data|No|
|email|Email|البريد الإلكتروني|Data|No|
|relationship|Relationship|الصفة أو العلاقة|Data|No|
|notes|Notes|ملاحظات|Small Text|No|

## JSON

```json
{
  "actions": [],
  "doctype": "DocType",
  "editable_grid": 1,
  "engine": "InnoDB",
  "field_order": [
    "person_type",
    "employee",
    "full_name",
    "national_id",
    "mobile_number",
    "email",
    "relationship",
    "notes"
  ],
  "fields": [
    {"fieldname":"person_type","fieldtype":"Select","in_list_view":1,"label":"Person Type","options":"Employee\nExternal Person","reqd":1},
    {"depends_on":"eval:doc.person_type=='Employee'","fieldname":"employee","fieldtype":"Link","in_list_view":1,"label":"Employee","options":"Employee"},
    {"depends_on":"eval:doc.person_type=='External Person'","fieldname":"full_name","fieldtype":"Data","in_list_view":1,"label":"Full Name"},
    {"fieldname":"national_id","fieldtype":"Data","label":"National ID"},
    {"fieldname":"mobile_number","fieldtype":"Data","label":"Mobile Number"},
    {"fieldname":"email","fieldtype":"Data","label":"Email","options":"Email"},
    {"fieldname":"relationship","fieldtype":"Data","label":"Relationship"},
    {"fieldname":"notes","fieldtype":"Small Text","label":"Notes"}
  ],
  "istable": 1,
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Concerned Person",
  "permissions": []
}
```

---

# 17. DocType: Murasalat Correspondence

## الإعدادات

|Setting|Value|
|---|---|
|Type|Transaction|
|Auto Name|By controller|
|Is Submittable|Yes|
|Track Changes|Yes|
|Track Seen|Yes|
|Title Field|subject|
|Search Fields|correspondence_number,subject,letter_number|
|Allow Rename|No|
|Allow Import|Yes|
|Max Attachments|0 — managed by Document DocType|

## الحقول

### هوية المعاملة

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|correspondence_number|Correspondence Number|رقم المعاملة|Data|Auto|
|direction|Direction|اتجاه المعاملة|Select|Yes|
|correspondence_type|Correspondence Type|نوع المعاملة|Link|Yes|
|workflow_state|Workflow State|حالة سير العمل|Link|Auto|
|status|Status|الحالة|Select|Auto|
|subject|Subject|الموضوع|Small Text|Yes|

### السرية والأهمية

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|confidentiality_level|Confidentiality Level|درجة السرية|Link|Yes|
|priority_level|Priority Level|درجة الأهمية|Link|Yes|
|due_date|Due Date|تاريخ الاستحقاق|Date|No|
|due_date_hijri|Due Date Hijri|تاريخ الاستحقاق الهجري|Data|Auto|

### بيانات الخطاب الخارجي

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|external_party|External Party|الجهة الخارجية|Link|Conditional|
|recipient_department|Recipient Department|الجهة المرسل إليها|Link|Conditional|
|letter_number|Letter Number|رقم الخطاب|Data|Conditional|
|letter_date|Letter Date|تاريخ الخطاب|Date|Conditional|
|letter_date_hijri|Letter Date Hijri|تاريخ الخطاب الهجري|Data|Auto|

### تفاصيل إضافية

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|page_count|Page Count|عدد الصفحات|Int|No|
|notes|Notes|ملاحظات|Long Text|No|
|link_to_other_correspondence|Link to Other Correspondence|اربط بمعاملة أخرى|Check|No|
|correspondence_links|Correspondence Links|روابط المعاملات|Table|No|
|concerned_persons|Concerned Persons|بيانات الشخص المعني|Table|No|
|barcode|Barcode|الباركود|Barcode|Auto|
|qr_code|QR Code|رمز الاستجابة السريعة|Attach Image|Auto|

### معلومات الملكية والتسجيل

| Fieldname          | English Label      | التسمية            | Type     | Required |
| ------------------ | ------------------ | ------------------ | -------- | -------- |
| owner_department   | Owner Department   | الإدارة المالكة    | Link     | Yes      |
| registered_by      | Registered By      | مسجل المعاملة      | Link     | Auto     |
| registered_on      | Registered On      | تاريخ ووقت التسجيل | Datetime | Auto     |
| closed_on          | Closed On          | تاريخ ووقت الإغلاق | Datetime | Auto     |
| current_department | Current Department | الإدارة الحالية    | Link     | Auto     |
| current_user       | Current User       | المستخدم الحالي    | Link     | Auto     |

## JSON

```json
{
  "actions": [],
  "allow_import": 1,
  "allow_rename": 0,
  "autoname": "MUR-.YYYY.-.######",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "identity_section",
    "correspondence_number",
    "direction",
    "correspondence_type",
    "workflow_state",
    "status",
    "subject_section",
    "subject",
    "classification_section",
    "confidentiality_level",
    "priority_level",
    "due_date",
    "due_date_hijri",
    "external_section",
    "external_party",
    "recipient_department",
    "letter_number",
    "letter_date",
    "letter_date_hijri",
    "details_section",
    "page_count",
    "notes",
    "links_section",
    "link_to_other_correspondence",
    "correspondence_links",
    "concerned_persons_section",
    "concerned_persons",
    "system_section",
    "owner_department",
    "registered_by",
    "registered_on",
    "closed_on",
    "current_department",
    "current_user",
    "barcode",
    "qr_code"
  ],
  "fields": [
    {"fieldname":"identity_section","fieldtype":"Section Break","label":"Correspondence Identity"},
    {"fieldname":"correspondence_number","fieldtype":"Data","in_list_view":1,"label":"Correspondence Number","read_only":1,"unique":1},
    {"fieldname":"direction","fieldtype":"Select","in_list_view":1,"label":"Direction","options":"Internal\nIncoming\nOutgoing","reqd":1},
    {"fieldname":"correspondence_type","fieldtype":"Link","in_list_view":1,"label":"Correspondence Type","options":"Murasalat Correspondence Type","reqd":1},
    {"fieldname":"workflow_state","fieldtype":"Link","label":"Workflow State","options":"Workflow State","read_only":1},
    {"default":"Draft","fieldname":"status","fieldtype":"Select","in_list_view":1,"label":"Status","options":"Draft\nRegistered\nIn Progress\nCompleted\nClosed\nCancelled","read_only":1},
    {"fieldname":"subject_section","fieldtype":"Section Break","label":"Subject Information"},
    {"fieldname":"subject","fieldtype":"Small Text","in_global_search":1,"label":"Subject","reqd":1},
    {"fieldname":"classification_section","fieldtype":"Section Break","label":"Classification"},
    {"fieldname":"confidentiality_level","fieldtype":"Link","in_list_view":1,"label":"Confidentiality Level","options":"Murasalat Confidentiality Level","reqd":1},
    {"fieldname":"priority_level","fieldtype":"Link","in_list_view":1,"label":"Priority Level","options":"Murasalat Priority Level","reqd":1},
    {"fieldname":"due_date","fieldtype":"Date","label":"Due Date"},
    {"fieldname":"due_date_hijri","fieldtype":"Data","label":"Due Date Hijri","read_only":1},
    {"depends_on":"eval:doc.direction!='Internal'","fieldname":"external_section","fieldtype":"Section Break","label":"External Correspondence Information"},
    {"depends_on":"eval:doc.direction!='Internal'","fieldname":"external_party","fieldtype":"Link","label":"External Party","options":"Murasalat External Party"},
    {"fieldname":"recipient_department","fieldtype":"Link","label":"Recipient Department","options":"Department"},
    {"depends_on":"eval:doc.direction!='Internal'","fieldname":"letter_number","fieldtype":"Data","in_global_search":1,"label":"Letter Number"},
    {"depends_on":"eval:doc.direction!='Internal'","fieldname":"letter_date","fieldtype":"Date","label":"Letter Date"},
    {"depends_on":"eval:doc.direction!='Internal'","fieldname":"letter_date_hijri","fieldtype":"Data","label":"Letter Date Hijri","read_only":1},
    {"fieldname":"details_section","fieldtype":"Section Break","label":"Additional Details"},
    {"fieldname":"page_count","fieldtype":"Int","label":"Page Count","non_negative":1},
    {"fieldname":"notes","fieldtype":"Long Text","label":"Notes"},
    {"fieldname":"links_section","fieldtype":"Section Break","label":"Links"},
    {"fieldname":"link_to_other_correspondence","fieldtype":"Check","label":"Link to Other Correspondence"},
    {"depends_on":"link_to_other_correspondence","fieldname":"correspondence_links","fieldtype":"Table","label":"Correspondence Links","options":"Murasalat Correspondence Link"},
    {"fieldname":"concerned_persons_section","fieldtype":"Section Break","label":"Concerned Persons","collapsible":1},
    {"fieldname":"concerned_persons","fieldtype":"Table","label":"Concerned Persons","options":"Murasalat Concerned Person"},
    {"fieldname":"system_section","fieldtype":"Section Break","label":"System Information","collapsible":1},
    {"fieldname":"owner_department","fieldtype":"Link","label":"Owner Department","options":"Department","reqd":1},
    {"fieldname":"registered_by","fieldtype":"Link","label":"Registered By","options":"User","read_only":1},
    {"fieldname":"registered_on","fieldtype":"Datetime","label":"Registered On","read_only":1},
    {"fieldname":"closed_on","fieldtype":"Datetime","label":"Closed On","read_only":1},
    {"fieldname":"current_department","fieldtype":"Link","label":"Current Department","options":"Department","read_only":1},
    {"fieldname":"current_user","fieldtype":"Link","label":"Current User","options":"User","read_only":1},
    {"fieldname":"barcode","fieldtype":"Barcode","label":"Barcode","read_only":1},
    {"fieldname":"qr_code","fieldtype":"Attach Image","label":"QR Code","read_only":1}
  ],
  "is_submittable": 1,
  "links": [
    {"group":"Transactions","link_doctype":"Murasalat Referral","link_fieldname":"correspondence"},
    {"group":"Documents","link_doctype":"Murasalat Correspondence Document","link_fieldname":"correspondence"}
  ],
  "module": "Murasalat Office",
  "name": "Murasalat Correspondence",
  "permissions": [
    {"role":"Murasalat User","read":1,"write":1,"create":1,"if_owner":1},
    {"role":"Murasalat Clerk","read":1,"write":1,"create":1,"submit":1,"print":1,"email":1,"export":1},
    {"role":"Murasalat Manager","read":1,"write":1,"create":1,"submit":1,"cancel":1,"print":1,"email":1,"export":1},
    {"role":"Murasalat Auditor","read":1,"print":1,"export":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"submit":1,"cancel":1,"amend":1,"delete":1,"print":1,"email":1,"export":1}
  ],
  "search_fields": "correspondence_number,subject,letter_number",
  "show_name_in_global_search": 1,
  "sort_field": "modified",
  "sort_order": "DESC",
  "title_field": "subject",
  "track_changes": 1,
  "track_seen": 1
}
```

---

# 18. DocType: Murasalat Correspondence Document

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|correspondence|Correspondence|المعاملة|Link|Yes|
|document_category|Document Category|تصنيف المستند|Link|Yes|
|document_type|Document Type|نوع المستند|Data|Yes|
|file|File|الملف|Attach|Yes|
|file_name|File Name|اسم الملف|Data|Auto|
|is_secret|Is Secret|مرفق سري|Check|No|
|confidentiality_level|Confidentiality Level|درجة السرية|Link|Conditional|
|document_version|Document Version|إصدار المستند|Int|No|
|is_main_document|Is Main Document|المستند الرئيسي|Check|No|
|uploaded_by|Uploaded By|أُرفق بواسطة|Link|Auto|
|uploaded_on|Uploaded On|تاريخ ووقت الإرفاق|Datetime|Auto|
|notes|Notes|ملاحظات|Small Text|No|

## JSON

```json
{
  "actions": [],
  "autoname": "MUR-DOC-.YYYY.-.######",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "document_section",
    "correspondence",
    "document_category",
    "document_type",
    "file",
    "file_name",
    "security_section",
    "is_secret",
    "confidentiality_level",
    "version_section",
    "document_version",
    "is_main_document",
    "uploaded_by",
    "uploaded_on",
    "notes"
  ],
  "fields": [
    {"fieldname":"document_section","fieldtype":"Section Break","label":"Document Information"},
    {"fieldname":"correspondence","fieldtype":"Link","in_list_view":1,"label":"Correspondence","options":"Murasalat Correspondence","reqd":1},
    {"fieldname":"document_category","fieldtype":"Link","in_list_view":1,"label":"Document Category","options":"Murasalat Document Category","reqd":1},
    {"fieldname":"document_type","fieldtype":"Data","label":"Document Type","reqd":1},
    {"fieldname":"file","fieldtype":"Attach","label":"File","reqd":1},
    {"fieldname":"file_name","fieldtype":"Data","label":"File Name","read_only":1},
    {"fieldname":"security_section","fieldtype":"Section Break","label":"Document Security"},
    {"fieldname":"is_secret","fieldtype":"Check","in_list_view":1,"label":"Is Secret"},
    {"depends_on":"is_secret","fieldname":"confidentiality_level","fieldtype":"Link","label":"Confidentiality Level","options":"Murasalat Confidentiality Level"},
    {"fieldname":"version_section","fieldtype":"Section Break","label":"Version Information"},
    {"default":"1","fieldname":"document_version","fieldtype":"Int","label":"Document Version","read_only":1},
    {"fieldname":"is_main_document","fieldtype":"Check","label":"Is Main Document"},
    {"fieldname":"uploaded_by","fieldtype":"Link","label":"Uploaded By","options":"User","read_only":1},
    {"fieldname":"uploaded_on","fieldtype":"Datetime","label":"Uploaded On","read_only":1},
    {"fieldname":"notes","fieldtype":"Small Text","label":"Notes"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Correspondence Document",
  "permissions": [
    {"role":"Murasalat User","read":1,"write":1,"create":1,"if_owner":1},
    {"role":"Murasalat Clerk","read":1,"write":1,"create":1},
    {"role":"Murasalat Manager","read":1,"write":1,"create":1,"delete":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "search_fields": "correspondence,file_name,document_type",
  "sort_field": "uploaded_on",
  "sort_order": "DESC",
  "track_changes": 1
}
```

---

# 19. DocType: Murasalat Referral

## الحقول المطابقة لصف الإحالة في الصور

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|correspondence|Correspondence|المعاملة|Link|Yes|
|from_user|From User|من المستخدم|Link|Auto|
|from_department|From Department|من الإدارة|Link|Yes|
|recipient_type|Recipient Type|نوع المستلم|Select|Yes|
|to_user|To User|إلى المستخدم|Link|Conditional|
|to_department|To Department|إلى الإدارة|Link|Conditional|
|routing_purpose|Routing Purpose|التوجيه|Link|Yes|
|priority_level|Priority Level|درجة الأهمية|Link|Yes|
|due_date|Due Date|تاريخ الاستحقاق|Date|No|
|due_date_hijri|Due Date Hijri|تاريخ الاستحقاق الهجري|Data|Auto|
|instructions|Instructions|تعليمات للمستقبل|Small Text|No|
|is_private|Private|خاص|Check|No|
|paper_correspondence|Paper Correspondence|مراسلة ورقية|Check|No|
|send_copy|Send Copy|صورة|Check|No|
|for_follow_up|For Follow Up|للمتابعة|Check|No|
|status|Status|الحالة|Select|Auto|
|sent_on|Sent On|تاريخ الإرسال|Datetime|Auto|
|received_on|Received On|تاريخ الاستلام|Datetime|Auto|
|completed_on|Completed On|تاريخ الإنجاز|Datetime|Auto|
|response_notes|Response Notes|ملاحظات الإجراء|Long Text|No|
|response_document|Response Document|مستند الرد|Link|No|

## JSON

```json
{
  "actions": [],
  "autoname": "MUR-REF-.YYYY.-.######",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "reference_section",
    "correspondence",
    "status",
    "source_section",
    "from_user",
    "from_department",
    "recipient_section",
    "recipient_type",
    "to_user",
    "to_department",
    "routing_section",
    "routing_purpose",
    "priority_level",
    "due_date",
    "due_date_hijri",
    "instructions",
    "options_section",
    "is_private",
    "paper_correspondence",
    "send_copy",
    "for_follow_up",
    "tracking_section",
    "sent_on",
    "received_on",
    "completed_on",
    "response_notes",
    "response_document"
  ],
  "fields": [
    {"fieldname":"reference_section","fieldtype":"Section Break","label":"Referral Reference"},
    {"fieldname":"correspondence","fieldtype":"Link","in_list_view":1,"label":"Correspondence","options":"Murasalat Correspondence","reqd":1},
    {"default":"Draft","fieldname":"status","fieldtype":"Select","in_list_view":1,"label":"Status","options":"Draft\nSent\nReceived\nIn Progress\nCompleted\nReturned\nWithdrawn\nCancelled","read_only":1},
    {"fieldname":"source_section","fieldtype":"Section Break","label":"Referral Source"},
    {"fieldname":"from_user","fieldtype":"Link","label":"From User","options":"User","read_only":1},
    {"fieldname":"from_department","fieldtype":"Link","label":"From Department","options":"Department","reqd":1},
    {"fieldname":"recipient_section","fieldtype":"Section Break","label":"Referral Recipient"},
    {"default":"Department","fieldname":"recipient_type","fieldtype":"Select","label":"Recipient Type","options":"Department\nUser","reqd":1},
    {"depends_on":"eval:doc.recipient_type=='User'","fieldname":"to_user","fieldtype":"Link","in_list_view":1,"label":"To User","options":"User"},
    {"depends_on":"eval:doc.recipient_type=='Department'","fieldname":"to_department","fieldtype":"Link","in_list_view":1,"label":"To Department","options":"Department"},
    {"fieldname":"routing_section","fieldtype":"Section Break","label":"Routing Details"},
    {"fieldname":"routing_purpose","fieldtype":"Link","in_list_view":1,"label":"Routing Purpose","options":"Murasalat Routing Purpose","reqd":1},
    {"fieldname":"priority_level","fieldtype":"Link","label":"Priority Level","options":"Murasalat Priority Level","reqd":1},
    {"fieldname":"due_date","fieldtype":"Date","label":"Due Date"},
    {"fieldname":"due_date_hijri","fieldtype":"Data","label":"Due Date Hijri","read_only":1},
    {"fieldname":"instructions","fieldtype":"Small Text","label":"Instructions"},
    {"fieldname":"options_section","fieldtype":"Section Break","label":"Referral Options"},
    {"fieldname":"is_private","fieldtype":"Check","label":"Private"},
    {"fieldname":"paper_correspondence","fieldtype":"Check","label":"Paper Correspondence"},
    {"fieldname":"send_copy","fieldtype":"Check","label":"Send Copy"},
    {"fieldname":"for_follow_up","fieldtype":"Check","label":"For Follow Up"},
    {"fieldname":"tracking_section","fieldtype":"Section Break","label":"Tracking Information"},
    {"fieldname":"sent_on","fieldtype":"Datetime","label":"Sent On","read_only":1},
    {"fieldname":"received_on","fieldtype":"Datetime","label":"Received On","read_only":1},
    {"fieldname":"completed_on","fieldtype":"Datetime","label":"Completed On","read_only":1},
    {"fieldname":"response_notes","fieldtype":"Long Text","label":"Response Notes"},
    {"fieldname":"response_document","fieldtype":"Link","label":"Response Document","options":"Murasalat Correspondence Document"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Referral",
  "permissions": [
    {"role":"Murasalat User","read":1,"write":1,"create":1},
    {"role":"Murasalat Clerk","read":1,"write":1,"create":1},
    {"role":"Murasalat Manager","read":1,"write":1,"create":1,"delete":1},
    {"role":"Murasalat Auditor","read":1,"export":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1,"export":1}
  ],
  "search_fields": "correspondence,from_user,to_user,to_department",
  "sort_field": "modified",
  "sort_order": "DESC",
  "track_changes": 1,
  "track_seen": 1
}
```

---

# 20. DocType: Murasalat Delegation

## الحقول

|Fieldname|English Label|التسمية|Type|Required|
|---|---|---|---|---|
|delegator|Delegator|المفوِّض|Link|Yes|
|delegate|Delegate|المفوَّض إليه|Link|Yes|
|department|Department|الإدارة|Link|Yes|
|valid_from|Valid From|صالح من|Date|Yes|
|valid_to|Valid To|صالح إلى|Date|Yes|
|allow_read|Allow Read|السماح بالقراءة|Check|No|
|allow_referral|Allow Referral|السماح بالإحالة|Check|No|
|allow_complete|Allow Complete|السماح بالإنجاز|Check|No|
|maximum_confidentiality|Maximum Confidentiality|أعلى درجة سرية|Link|No|
|status|Status|الحالة|Select|Auto|
|reason|Reason|سبب التفويض|Small Text|No|

## JSON

```json
{
  "actions": [],
  "autoname": "MUR-DEL-.YYYY.-.#####",
  "doctype": "DocType",
  "engine": "InnoDB",
  "field_order": [
    "delegation_section",
    "delegator",
    "delegate",
    "department",
    "valid_from",
    "valid_to",
    "status",
    "permissions_section",
    "allow_read",
    "allow_referral",
    "allow_complete",
    "maximum_confidentiality",
    "reason"
  ],
  "fields": [
    {"fieldname":"delegation_section","fieldtype":"Section Break","label":"Delegation Information"},
    {"fieldname":"delegator","fieldtype":"Link","in_list_view":1,"label":"Delegator","options":"User","reqd":1},
    {"fieldname":"delegate","fieldtype":"Link","in_list_view":1,"label":"Delegate","options":"User","reqd":1},
    {"fieldname":"department","fieldtype":"Link","label":"Department","options":"Department","reqd":1},
    {"fieldname":"valid_from","fieldtype":"Date","in_list_view":1,"label":"Valid From","reqd":1},
    {"fieldname":"valid_to","fieldtype":"Date","in_list_view":1,"label":"Valid To","reqd":1},
    {"default":"Draft","fieldname":"status","fieldtype":"Select","label":"Status","options":"Draft\nActive\nExpired\nCancelled","read_only":1},
    {"fieldname":"permissions_section","fieldtype":"Section Break","label":"Delegated Permissions"},
    {"default":"1","fieldname":"allow_read","fieldtype":"Check","label":"Allow Read"},
    {"fieldname":"allow_referral","fieldtype":"Check","label":"Allow Referral"},
    {"fieldname":"allow_complete","fieldtype":"Check","label":"Allow Complete"},
    {"fieldname":"maximum_confidentiality","fieldtype":"Link","label":"Maximum Confidentiality","options":"Murasalat Confidentiality Level"},
    {"fieldname":"reason","fieldtype":"Small Text","label":"Reason"}
  ],
  "links": [],
  "module": "Murasalat Office",
  "name": "Murasalat Delegation",
  "permissions": [
    {"role":"Murasalat User","read":1,"write":1,"create":1,"if_owner":1},
    {"role":"Murasalat Manager","read":1,"write":1,"create":1,"delete":1},
    {"role":"Murasalat Auditor","read":1},
    {"role":"Murasalat System Manager","read":1,"write":1,"create":1,"delete":1}
  ],
  "sort_field": "valid_from",
  "sort_order": "DESC",
  "track_changes": 1
}
```

---

# 21. حالات المعاملة في المرحلة الأولى

## Murasalat Correspondence Workflow

|Current State|Action|Next State|Allowed Role|
|---|---|---|---|
|Draft|Register|Registered|Murasalat Clerk|
|Registered|Start Processing|In Progress|Murasalat User/Manager|
|In Progress|Complete|Completed|Murasalat User/Manager|
|Completed|Reopen|In Progress|Murasalat Manager|
|Completed|Close|Closed|Murasalat Manager|
|Registered|Cancel|Cancelled|Murasalat Manager|
|In Progress|Cancel|Cancelled|Murasalat Manager|

## Murasalat Referral Status

```text
Draft
Sent
Received
In Progress
Completed
Returned
Withdrawn
Cancelled
```

الأزرار التشغيلية:

```text
Send
Mark as Received
Start Processing
Complete
Return
Withdraw
Cancel
```

---

# 22. واجهة التسجيل ذات الخطوات الثلاث

## الخطوة الأولى: Data

تعرض:

```text
Correspondence Number
Direction
Correspondence Type
Subject
Confidentiality Level
Priority Level
Due Date
Page Count
Notes
External Party
Recipient Department
Letter Number
Letter Date
Link to Other Correspondence
Concerned Persons
```

الأزرار:

```text
Clear Fields
Save as Draft
Print Barcode
Next
Previous
```

## الخطوة الثانية: Attachments

تعرض:

```text
Scan
Attach from Device
Document Type
Document Category
File
Upload
Main Letter
Attachments
Reply
Newest
Oldest
Grid View
List View
```

## الخطوة الثالثة: Referral

تعرض لكل صف:

```text
To
Routing Purpose
Priority Level
Due Date
Instructions
Private
Paper Correspondence
Send Copy
For Follow Up
```

الأزرار:

```text
Add Row
Multiple Referral
Send
Previous
```

---

# 23. Workspace المرحلة الأولى

اسم Workspace:

```text
Murasalat Office
```

القائمة:

```text
Murasalat Office
├── New Correspondence
│   ├── Register Internal Correspondence
│   ├── Internal Correspondence Drafts
│   ├── Register External Incoming Correspondence
│   └── Register External Outgoing Correspondence
├── Correspondence Box
│   ├── My Inbox
│   ├── Department Inbox
│   ├── Sent Referrals
│   ├── Completed Referrals
│   └── Follow-up
├── Search
│   ├── Simple Search
│   └── Advanced Search
├── Documents
│   └── Correspondence Documents
├── Delegations
│   ├── My Delegations
│   └── Delegated to Me
└── Setup
    ├── Murasalat Settings
    ├── Correspondence Types
    ├── External Parties
    ├── Confidentiality Levels
    ├── Priority Levels
    ├── Routing Purposes
    ├── Document Categories
    └── Numbering Rules
```

---

# 24. خطوات التثبيت بعد وضع JSON

```bash
cd ~/frappe-bench

bench --site murasalat.local migrate
bench --site murasalat.local clear-cache
bench build --app murasalat_office
bench restart
```

وفي بيئة التطوير:

```bash
bench start
```

---

# 25. اختبارات قبول المرحلة الأولى

يجب ألا تُعتبر المرحلة الأولى مكتملة إلا بعد نجاح التالي:

1. إنشاء Internal Correspondence وحفظها كمسودة.
2. تسجيل External Incoming Correspondence بجميع الحقول الظاهرة في الصور.
3. تسجيل External Outgoing Correspondence.
4. توليد رقم معاملة فريد.
5. عدم السماح بإنشاء معاملة دون:
    - Subject.
    - Correspondence Type.
    - Confidentiality Level.
    - Priority Level.
6. فرض بيانات الجهة ورقم الخطاب حسب نوع المعاملة.
7. إظهار التاريخ الهجري المقابل.
8. ربط أكثر من معاملة.
9. جعل أول رابط هو المرجع الرئيسي عند عدم تحديد رابط رئيسي.
10. إضافة شخص معني داخلي أو خارجي.
11. إضافة Main Letter وAttachments وReply.
12. منع غير المخولين من قراءة Secret Attachment.
13. إنشاء إحالة إلى مستخدم.
14. إنشاء إحالة إلى إدارة.
15. إنشاء عدة إحالات من Multiple Referral.
16. ظهور الإحالة في صندوق المستلم.
17. استلام الإحالة وإنجازها.
18. ظهور الإحالات المتأخرة.
19. تطبيق التفويض في الفترة المحددة فقط.
20. البحث برقم المعاملة والموضوع ورقم الخطاب.
21. ظهور جميع التغييرات في Version Log.
22. عدم حذف المعاملة بعد التسجيل.
23. عمل الواجهة باللغة الإنجليزية.
24. عمل الترجمة العربية واتجاه RTL.
25. نجاح Print Format للباركود.

---

# 26. ملف `ar.csv`

المسار:

```text
apps/murasalat_office/murasalat_office/translations/ar.csv
```

يستخدم Frappe ملف ترجمة لكل لغة داخل مجلد `translations`، ويتكون CSV من النص الأصلي والترجمة والسياق الاختياري:  
[https://docs.frappe.io/framework/user/en/guides/basics/translations](https://docs.frappe.io/framework/user/en/guides/basics/translations)

```csv
"Murasalat Office","مكتب المراسلات",""
"Murasalat Settings","إعدادات المراسلات",""
"Murasalat Correspondence","معاملة المراسلات",""
"Murasalat Correspondence Type","نوع معاملة المراسلات",""
"Murasalat External Party","جهة خارجية",""
"Murasalat Confidentiality Level","مستوى السرية",""
"Murasalat Priority Level","درجة الأهمية",""
"Murasalat Routing Purpose","غرض التوجيه",""
"Murasalat Document Category","تصنيف المستند",""
"Murasalat Numbering Rule","قاعدة ترقيم المراسلات",""
"Murasalat Correspondence Link","رابط معاملة",""
"Murasalat Concerned Person","الشخص المعني",""
"Murasalat Correspondence Document","مستند المعاملة",""
"Murasalat Referral","إحالة",""
"Murasalat Delegation","تفويض",""
"Organization","المؤسسة",""
"Company","الشركة",""
"Default Department","الإدارة الافتراضية",""
"Defaults","القيم الافتراضية",""
"Default Confidentiality","السرية الافتراضية",""
"Default Priority","الأهمية الافتراضية",""
"Default Routing Purpose","غرض التوجيه الافتراضي",""
"Dates","التواريخ",""
"Enable Hijri Dates","تفعيل التواريخ الهجرية",""
"Default Due Days","أيام الاستحقاق الافتراضية",""
"Attachments","المرفقات",""
"Maximum Attachment Size MB","الحد الأقصى لحجم المرفق بالميجابايت",""
"Allow Secret Attachments","السماح بالمرفقات السرية",""
"Allowed File Extensions","امتدادات الملفات المسموحة",""
"Controls","الضوابط",""
"Prevent Registered Correspondence Deletion","منع حذف المعاملات المسجلة",""
"Enable Barcode","تفعيل الباركود",""
"Enable Audit Log","تفعيل سجل التدقيق",""
"Type Name","اسم النوع",""
"Code","الرمز",""
"Direction","اتجاه المعاملة",""
"Internal","داخلي",""
"Incoming","وارد",""
"Outgoing","صادر",""
"Requires External Party","يتطلب جهة خارجية",""
"Requires Letter Number","يتطلب رقم خطاب",""
"Requires Letter Date","يتطلب تاريخ خطاب",""
"Is Active","نشط",""
"Description","الوصف",""
"Party Name","اسم الجهة",""
"Short Name","الاسم المختصر",""
"Party Type","نوع الجهة",""
"Government","حكومية",""
"Private","خاصة",""
"Individual","فرد",""
"Other","أخرى",""
"Parent Party","الجهة الأم",""
"City","المدينة",""
"Country","الدولة",""
"Contact Information","معلومات الاتصال",""
"Email","البريد الإلكتروني",""
"Phone","الهاتف",""
"Address","العنوان",""
"Notes","ملاحظات",""
"Level Name","اسم المستوى",""
"Rank","الترتيب",""
"Color","اللون",""
"Restrict Access","تقييد الوصول",""
"Normal","عادي",""
"Confidential","سري",""
"Secret","سري للغاية",""
"Top Secret","سري جدًا",""
"Priority Name","اسم درجة الأهمية",""
"Urgent","عاجل",""
"Very Urgent","عاجل جدًا",""
"Immediate","حالًا",""
"Purpose Name","غرض التوجيه",""
"Requires Response","يتطلب ردًا",""
"Closes on Completion","يغلق عند الإنجاز",""
"For Signature","للتوقيع",""
"For Necessary Action","لإكمال اللازم",""
"For Review","للمشاهدة",""
"For Approval","للموافقة",""
"For Circulation","للتعميم",""
"For Study and Opinion","للدراسة وإبداء الرأي",""
"Category Name","اسم التصنيف",""
"Display Order","ترتيب العرض",""
"Allow Multiple","السماح بأكثر من ملف",""
"Main Letter","الخطاب الرئيسي",""
"Reply","الرد",""
"Rule Name","اسم قاعدة الترقيم",""
"Correspondence Type","نوع المعاملة",""
"Prefix","بادئة الرقم",""
"Number of Digits","عدد الخانات",""
"Include Year","تضمين السنة",""
"Year Type","نوع السنة",""
"Gregorian","ميلادي",""
"Hijri","هجري",""
"Is Default","افتراضي",""
"Linked Correspondence","المعاملة المرتبطة",""
"Relationship Type","نوع العلاقة",""
"Related","مرتبطة",""
"Reply To","رد على",""
"Follow-up To","متابعة لـ",""
"Reference","مرجع",""
"Supersedes","تحل محل",""
"Primary Reference","المرجع الرئيسي",""
"Person Type","نوع الشخص",""
"Employee","الموظف",""
"External Person","شخص خارجي",""
"Full Name","الاسم الكامل",""
"National ID","رقم الهوية",""
"Mobile Number","رقم الجوال",""
"Relationship","الصفة أو العلاقة",""
"Correspondence Identity","هوية المعاملة",""
"Correspondence Number","رقم المعاملة",""
"Workflow State","حالة سير العمل",""
"Status","الحالة",""
"Draft","مسودة",""
"Registered","مسجلة",""
"In Progress","قيد المعالجة",""
"Completed","منجزة",""
"Closed","مغلقة",""
"Cancelled","ملغاة",""
"Subject Information","بيانات الموضوع",""
"Subject","الموضوع",""
"Classification","التصنيف",""
"Confidentiality Level","درجة السرية",""
"Priority Level","درجة الأهمية",""
"Due Date","تاريخ الاستحقاق",""
"Due Date Hijri","تاريخ الاستحقاق الهجري",""
"External Correspondence Information","بيانات المعاملة الخارجية",""
"External Party","الجهة الخارجية",""
"Recipient Department","الجهة المرسل إليها",""
"Letter Number","رقم الخطاب",""
"Letter Date","تاريخ الخطاب",""
"Letter Date Hijri","تاريخ الخطاب الهجري",""
"Additional Details","تفاصيل إضافية",""
"Page Count","عدد الصفحات",""
"Links","الروابط",""
"Link to Other Correspondence","اربط بمعاملة أخرى",""
"Correspondence Links","روابط المعاملات",""
"Concerned Persons","بيانات الشخص المعني",""
"System Information","معلومات النظام",""
"Owner Department","الإدارة المالكة",""
"Registered By","مسجل المعاملة",""
"Registered On","تاريخ ووقت التسجيل",""
"Closed On","تاريخ ووقت الإغلاق",""
"Current Department","الإدارة الحالية",""
"Current User","المستخدم الحالي",""
"Barcode","الباركود",""
"QR Code","رمز الاستجابة السريعة",""
"Document Information","بيانات المستند",""
"Correspondence","المعاملة",""
"Document Category","تصنيف المستند",""
"Document Type","نوع المستند",""
"File","الملف",""
"File Name","اسم الملف",""
"Document Security","أمان المستند",""
"Is Secret","مرفق سري",""
"Version Information","معلومات الإصدار",""
"Document Version","إصدار المستند",""
"Is Main Document","المستند الرئيسي",""
"Uploaded By","أُرفق بواسطة",""
"Uploaded On","تاريخ ووقت الإرفاق",""
"Referral Reference","مرجع الإحالة",""
"Referral Source","مصدر الإحالة",""
"From User","من المستخدم",""
"From Department","من الإدارة",""
"Referral Recipient","مستلم الإحالة",""
"Recipient Type","نوع المستلم",""
"User","مستخدم",""
"Department","إدارة",""
"To User","إلى المستخدم",""
"To Department","إلى الإدارة",""
"Routing Details","تفاصيل التوجيه",""
"Routing Purpose","التوجيه",""
"Instructions","تعليمات للمستقبل",""
"Referral Options","خيارات الإحالة",""
"Paper Correspondence","مراسلة ورقية",""
"Send Copy","صورة",""
"For Follow Up","للمتابعة",""
"Tracking Information","معلومات التتبع",""
"Sent","مرسلة",""
"Received","مستلمة",""
"Returned","معادة",""
"Withdrawn","مسحوبة",""
"Sent On","تاريخ الإرسال",""
"Received On","تاريخ الاستلام",""
"Completed On","تاريخ الإنجاز",""
"Response Notes","ملاحظات الإجراء",""
"Response Document","مستند الرد",""
"Delegation Information","بيانات التفويض",""
"Delegator","المفوِّض",""
"Delegate","المفوَّض إليه",""
"Valid From","صالح من",""
"Valid To","صالح إلى",""
"Active","نشط",""
"Expired","منتهي",""
"Delegated Permissions","صلاحيات التفويض",""
"Allow Read","السماح بالقراءة",""
"Allow Referral","السماح بالإحالة",""
"Allow Complete","السماح بالإنجاز",""
"Maximum Confidentiality","أعلى درجة سرية",""
"Reason","السبب",""
"New Correspondence","مراسلة جديدة",""
"Register Internal Correspondence","تسجيل معاملة داخلية",""
"Internal Correspondence Drafts","مسودات المعاملات الداخلية",""
"Register External Incoming Correspondence","تسجيل معاملة واردة خارجية",""
"Register External Outgoing Correspondence","تسجيل معاملة صادرة خارجية",""
"Correspondence Box","صندوق المعاملات",""
"My Inbox","صندوق الوارد",""
"Department Inbox","صندوق الإدارة",""
"Sent Referrals","الإحالات المرسلة",""
"Completed Referrals","الإحالات المنجزة",""
"Follow-up","المتابعة",""
"Search","بحث",""
"Simple Search","بحث بسيط",""
"Advanced Search","بحث متقدم",""
"Documents","المستندات",""
"Delegations","التفويضات",""
"My Delegations","تفويضاتي",""
"Delegated to Me","المفوّض إليّ",""
"Setup","الإعدادات",""
"Correspondence Types","أنواع المعاملات",""
"External Parties","الجهات الخارجية",""
"Confidentiality Levels","مستويات السرية",""
"Priority Levels","درجات الأهمية",""
"Routing Purposes","أغراض التوجيه",""
"Document Categories","تصنيفات المستندات",""
"Numbering Rules","قواعد الترقيم",""
"Data","البيانات",""
"Clear Fields","تفريغ الحقول",""
"Save as Draft","حفظ كمسودة",""
"Print Barcode","طباعة باركود",""
"Next","التالي",""
"Previous","السابق",""
"Scan","مسح ضوئي",""
"Attach from Device","إرفاق من جهازك",""
"Upload","تحميل",""
"Newest","الأحدث",""
"Oldest","الأقدم",""
"Grid View","عرض شبكي",""
"List View","عرض قائمة",""
"Referral","إحالة",""
"Add Row","إضافة صف",""
"Multiple Referral","إحالة متعددة",""
"Send","إرسال",""
"Mark as Received","تأكيد الاستلام",""
"Start Processing","بدء المعالجة",""
"Complete","إنجاز",""
"Return","إعادة",""
"Withdraw","سحب",""
"Cancel","إلغاء",""
"Register","تسجيل",""
"Start Processing","بدء المعالجة",""
"Reopen","إعادة فتح",""
"Close","إغلاق",""
```

بعد إضافة الملف:

```bash
bench --site murasalat.local clear-cache
bench build --app murasalat_office
bench restart
```

هذه هي **Baseline المرحلة الأولى**: الهوية الجديدة، جميع DocTypes الأساسية، الحقول المطابقة للصور، الإحالات المستقلة، المرفقات السرية، التفويضات، الترقيم، الصلاحيات الأولية، والواجهة الإنجليزية مع ملف ترجمة عربية جاهز.