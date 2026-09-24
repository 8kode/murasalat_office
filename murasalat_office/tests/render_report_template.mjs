// Render a report print template through Frappe's own browser template engine.
//
// A report layout is not rendered by Jinja. Frappe hands the template text to the browser
// (frappe.desk.query_report.get_script -> report_settings.html_format) and renders it with
// frappe/public/js/frappe/microtemplate.js, whose grammar is much smaller than Jinja's:
// it rewrites {{ }}, {% if %}, {% else %}, {% endif %}, {% for x in y %} and {% endfor %}
// into JavaScript and evaluates that. Anything else - {% set %}, {% elif %}, filters,
// loop.index0 - is left in place, the generated JavaScript fails to compile, and the report
// prints nothing at all. Jinja passing a template therefore proves nothing about a report
// layout; this runner executes the template in the engine that actually renders it.
//
// Usage: node tests/render_report_template.mjs <microtemplate.js> <template.html> [more.html ...]
// Exits non-zero with the failing checks listed, so it can guard the layout in CI.

import fs from "node:fs";

const [engine_path, ...templates] = process.argv.slice(2);

if (!engine_path || !templates.length) {
	console.error("usage: node render_report_template.mjs <microtemplate.js> <template.html> ...");
	process.exit(2);
}

// --- the slices of Frappe the engine touches while compiling --------------------------
let counter = 0;
globalThis.frappe = {
	utils: {
		// The engine builds its loop variables from this, so every value must be unique and
		// must be a valid identifier - real Frappe returns a letter-first random string.
		get_random: (len) => "v" + (counter++).toString(36).padStart(len - 1, "0"),
	},
	template: { compiled: {}, debug: {} },
};

// eslint-disable-next-line no-eval
eval(fs.readFileSync(engine_path, "utf8"));

// --- a report-shaped fixture ----------------------------------------------------------
const columns = [
	{ fieldname: "unit", label: "الوحدة التنظيمية", fieldtype: "Data" },
	{ fieldname: "received", label: "تم الاستلام", fieldtype: "Int" },
	{ fieldname: "open_now", label: "Open Now", fieldtype: "Int" },
	{ fieldname: "avg_close_days", label: "Average Days to Close", fieldtype: "Float" },
];

const data = [
	{ unit: "القسم المالي", received: 12, open_now: 3, avg_close_days: 2.5 },
	{ unit: "القسم القانوني", received: 0, open_now: 0, avg_close_days: null },
	{ unit: "الإجمالي", received: 12, open_now: 3, avg_close_days: 1.25 },
];

const filters_line = '<div class="filter-row"><strong>From</strong> 2026-09-01</div>';
const base = {
	title: "الملخّص الإداري",
	subtitle: filters_line,
	filters: { from_date: "2026-09-01" },
	data,
	columns,
	original_data: data,
	report: {},
	print_settings: {},
};

let failures = 0;

function check(ok, label) {
	if (!ok) failures += 1;
	console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
}

for (const path of templates) {
	const source = fs.readFileSync(path, "utf8");
	console.log(`\n--- ${path} ---`);

	let html;
	try {
		html = frappe.render_template(source, base);
	} catch (error) {
		check(false, `render threw: ${(error && error.message) || error}`);
		continue;
	}

	// <thead>/<tbody> split keeps the header check from counting <thead> as a header cell.
	const head = html.split("<tbody>")[0] || "";
	const body = html.split("<tbody>")[1] || "";

	check(html.includes('class="mo-rpt"'), "A4 container rendered");
	check(html.includes('dir="rtl"'), "right-to-left document rendered");
	check(html.includes("الملخّص الإداري"), "title rendered");
	check(html.includes("mo-rpt-foot"), "footer rendered");
	check(!/\{%|\{\{/.test(html), "no template tag left in the output");
	check(!html.includes("undefined"), "no undefined leaked into the output");

	check((head.match(/<th[\s>]/g) || []).length === columns.length, "one header cell per column");
	check(
		(body.match(/<td[\s>]/g) || []).length === data.length * columns.length,
		"one body cell per value"
	);
	check(head.includes('class="num"'), "numeric columns are centred");
	check(body.includes('class="num"'), "numeric values are centred");

	check(body.includes("القسم المالي"), "row label rendered");
	check(body.includes("2.5"), "decimal value rendered");
	check(body.includes("1.25"), "the total row keeps its value");
	check(body.includes("mo-dash"), "a missing measurement renders as a dash, not as a zero");
	check((body.match(/class="total"/g) || []).length === 1, "the total row is marked once");

	check(html.includes("2026-09-01"), "the filter line the framework builds is kept");

	const empty = frappe.render_template(source, { ...base, subtitle: null, data: [] });
	check(empty.includes("لا توجد بيانات"), "an empty period prints a message instead of breaking");
	check(empty.includes(`colspan="${columns.length}"`), "the empty state spans every column");
	check(!empty.includes("2026-09-01"), "the filter strip is dropped when there are none");
	check(!empty.includes('class="total"'), "no total row is invented for an empty period");
}

console.log(`\n${failures === 0 ? "EXIT=0" : `EXIT=1 (${failures} failing checks)`}`);
process.exit(failures === 0 ? 0 : 1);
