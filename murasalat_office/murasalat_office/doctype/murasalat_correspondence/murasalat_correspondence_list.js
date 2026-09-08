frappe.listview_settings['Murasalat Correspondence'] = {
  add_fields: ['status', 'subject', 'importance', 'due_date', 'current_holder', 'current_holder_user', 'confidentiality'],
  hide_name_column: false,
  get_indicator(doc) {
    if (doc.status === 'Closed') return [__('Closed'), 'green', 'status,=,Closed'];
    if (doc.status === 'Withdrawn') return [__('Withdrawn'), 'grey', 'status,=,Withdrawn'];
    if (doc.status === 'Reopened') return [__('Reopened'), 'orange', 'status,=,Reopened'];
    return [doc.status || __('Draft'), 'blue', `status,=,${doc.status || 'Draft'}`];
  },
  button: {
    show(doc) { return !!doc.name; },
    get_label() { return __('Open'); },
    get_description(doc) { return __('Open correspondence {0}', [doc.name]); },
    action(doc) { frappe.set_route('Form', 'Murasalat Correspondence', doc.name); }
  }
};
