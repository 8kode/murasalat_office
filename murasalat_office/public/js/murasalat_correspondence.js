frappe.ui.form.on('Murasalat Correspondence', {
  refresh(frm) {
    frm.page.set_indicator(frm.doc.status || __('Draft'), frm.doc.status === 'Closed' ? 'green' : 'blue');
    if (frm.is_new()) return;

    const active = (frm.doc.referrals || []).filter(r => ['Pending','Sent','Received','In Progress','Overdue'].includes(r.status));
    const choose_referral = (label, method, needs_reason=false) => {
      frm.add_custom_button(label, () => {
        if (!active.length) return frappe.msgprint(__('No active referral is available.'));
        const d = new frappe.ui.Dialog({
          title: label,
          fields: [
            {fieldname:'referral_number', label:__('Referral'), fieldtype:'Select', options: active.map(r => `${r.referral_number} — ${r.status}`).join('\n'), reqd:1},
            ...(needs_reason ? [{fieldname:'reason', label:__('Reason / Note'), fieldtype:'Small Text', reqd:1}] : [])
          ],
          primary_action_label: __('Confirm'),
          primary_action(values) {
            const referral_number = values.referral_number.split(' — ')[0];
            frappe.call({method, args:{correspondence:frm.doc.name, referral_number, note:values.reason, reason:values.reason}})
              .then(() => { d.hide(); frm.reload_doc(); });
          }
        }); d.show();
      }, __('Operations'));
    };

    choose_referral(__('Receive Referral'), 'murasalat_office.api.operations.receive');
    choose_referral(__('Start Referral'), 'murasalat_office.api.operations.start');
    choose_referral(__('Complete Referral'), 'murasalat_office.api.operations.complete');
    choose_referral(__('Reject Referral'), 'murasalat_office.api.operations.reject', true);
    choose_referral(__('Return Referral'), 'murasalat_office.api.operations.return_referral', true);

    const reason_action = (label, method) => frm.add_custom_button(label, () => {
      frappe.prompt([{fieldname:'reason', label:__('Reason / Note'), fieldtype:'Small Text', reqd:1}], values => {
        frappe.call({method, args:{correspondence:frm.doc.name, reason:values.reason, note:values.reason}}).then(() => frm.reload_doc());
      }, label, __('Confirm'));
    }, __('Operations'));

    reason_action(__('Withdraw Correspondence'), 'murasalat_office.api.operations.withdraw');
    reason_action(__('Reopen Correspondence'), 'murasalat_office.api.operations.reopen');

    frm.add_custom_button(__('Request Approval'), () => {
      frappe.new_doc('Murasalat Approval Request', {correspondence: frm.doc.name});
    }, __('Approval'));

    frm.add_custom_button(__('Close Correspondence'), () => frappe.call({
      method:'murasalat_office.api.operations.close', args:{correspondence:frm.doc.name}
    }).then(() => frm.reload_doc()), __('Operations'));

    frm.add_custom_button(__('Open Work Queue'), () => {
      frappe.set_route('query-report', 'Murasalat Work Queue', { correspondence: frm.doc.name });
    }, __('Navigate'));

    frm.add_custom_button(__('Open Inbox'), () => {
      frappe.set_route('query-report', 'Murasalat Inbox');
    }, __('Navigate'));

    frm.add_custom_button(__('Registration Checklist'), () => {
      frappe.call({
        method:'murasalat_office.api.journey.registration_checklist',
        args:{correspondence:frm.doc.name},
        freeze:true
      }).then(r => {
        const m = r.message || {};
        frappe.msgprint({
          title: m.ready ? __('Ready for Registration') : __('Registration Checklist'),
          indicator: m.ready ? 'green' : 'orange',
          message: m.ready ? __('All registration requirements are satisfied.') : `<ul>${(m.errors || []).map(x => `<li>${frappe.utils.escape_html(x)}</li>`).join('')}</ul>`
        });
      });
    }, __('Registration Journey'));

    frm.add_custom_button(__('Register Correspondence'), () => {
      frappe.call({method:'murasalat_office.api.journey.register', args:{correspondence:frm.doc.name}, freeze:true, freeze_message:__('Registering correspondence...')})
        .then(() => frm.reload_doc());
    }, __('Registration Journey'));

    frm.add_custom_button(__('Send Referrals'), () => {
      frappe.call({method:'murasalat_office.api.journey.send', args:{correspondence:frm.doc.name}, freeze:true, freeze_message:__('Sending referrals...')})
        .then(() => frm.reload_doc());
    }, __('Registration Journey'));

    frm.add_custom_button(__('Operational Summary'), () => {
      frappe.call({
        method:'murasalat_office.api.operations.operational_summary',
        args:{correspondence:frm.doc.name},
        freeze:true
      }).then(r => {
        const m = r.message || {};
        const holder = m.current_holder_user || m.current_holder || __('Unassigned');
        frappe.msgprint({
          title: __('Operational Summary'),
          indicator: m.overdue_referrals ? 'red' : (m.open_referrals ? 'orange' : 'green'),
          message: `<div><b>${__('Current holder')}:</b> ${frappe.utils.escape_html(holder)}<br>` +
            `<b>${__('Open referrals')}:</b> ${m.open_referrals || 0}<br>` +
            `<b>${__('Overdue referrals')}:</b> ${m.overdue_referrals || 0}<br>` +
            `<b>${__('Next due date')}:</b> ${m.next_due_date || __('None')}<br>` +
            `<b>${__('Record sealed')}:</b> ${m.sealed ? __('Yes') : __('No')}<br>` +
            `<b>${__('Integrity')}:</b> ${m.integrity_valid ? __('Valid') : __('Not verified')}</div>`
        });
      });
    }, __('Navigate'));

    frm.add_custom_button(__('Verify Record Integrity'), () => {
      frappe.call({
        method: 'murasalat_office.api.operations.verify_record_integrity',
        args: { correspondence: frm.doc.name },
        freeze: true,
        freeze_message: __('Verifying record integrity...')
      }).then(r => {
        const ok = r.message && r.message.valid;
        frappe.msgprint({
          title: ok ? __('Integrity Verified') : __('Integrity Warning'),
          indicator: ok ? 'green' : 'red',
          message: ok ? __('The current record matches its sealed integrity snapshot.') : __('The current record does not match its sealed integrity snapshot.')
        });
      });
    }, __('Security'));
  }
});
