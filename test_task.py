from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import _, fields, models
from odoo.tools.misc import parse_date
import re

"""
Exercise 1:
a) What does the function _refactor_exercise of class Exercise1 do? Please give a general outline.

- _refactor_exercise updates subscription information based on subscription and order.
- extends _refactor_exercise via super for case when we have subscription_id,
   updates values (do not trigger corresponding validations), 
b) Name some simple refactoring measures that would increase the readability, maintainability and extensibility of this function and describe their benefits.
- move function out of _refactor_solution so we can extend it and 'play' with results
- change variable names to more explict so we understand what are we dealing with
- if we have same values assigned to one variable we can do it as one-liner
- move update part to one place.
- move some of functionality to smaller functions, so code is more maintainable
c) Refactor _refactor_exercise by applying the measures from b).
- made surface-refactoring so it is more maintainable,
 it is possible to do it even better.
"""


class Excercise1(models.Model):

    def _refactor_exercise(self, **kwargs):
        res = super(Excercise1, self)._refactor_exercise(**kwargs)
        if self.subscription_id:
            res.update(subscription_id=self.subscription_id.id)
            periods = {
                'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            ndate = self.subscription_id.recurring_next_date
            pdate = ndate - relativedelta(**{periods[self.subscription_id.recurring_rule_type]: self.subscription_id.recurring_interval})
            period_msg = True if _("Invoicing period") in self.name else False
            if self.order_id.subscription_management != 'upsell':
                sdate = pdate
                sdate_display = pdate
                edate = ndate - relativedelta(days=1)
            else:
                sdate, sdate_display, edate = None, None, None
                if period_msg:
                    try:
                        regexp = _("Invoicing period") + ": (.*) - (.*)"
                        m = re.search(regexp, self.name)
                        sdate = parse_date(self.env, m.group(1))
                        sdate_display = sdate
                        edate = parse_date(self.env, m.group(2))
                        if not isinstance(sdate, date) or not isinstance(edate, date):
                            sdate, edate = None, None
                    except AttributeError:
                        pass
                if not sdate or not sdate_display or not edate:
                    tdays = (ndate - pdate).days
                    days = round((1 - self.discount / 100.0) * tdays)
                    sdate = ndate - relativedelta(days=days+1)
                    sdate_display = ndate - relativedelta(days=days)
                    edate = ndate - relativedelta(days=1)
            if not period_msg:
                lang = self.order_id.partner_invoice_id.lang
                fdate = self.env['ir.qweb.field.date'].with_context(lang=lang).value_to_html
                if lang:
                    self = self.with_context(lang=lang)
                msg = _("Invoicing period") + ": %s - %s" % (
                    fdate(fields.Date.to_string(sdate_display), {}), fdate(fields.Date.to_string(edate), {}))
                res.update({
                    'name': res['name'] + '\n' + msg,
                })
            res.update({
                'subscription_start_date': sdate,
                'subscription_end_date': edate,
            })
            if self.subscription_id.analytic_account_id:
                res['analytic_account_id'] = self.subscription_id.analytic_account_id.id
        return res


class Solution1(models.Model):

    def _get_periods(self):
        """Gets periods based on subscription"""
        periods = {
            'daily': 'days', 'weekly': 'weeks', 'monthly': 'months',
            'yearly': 'years'
        }
        next_date = self.subscription_id.recurring_next_date
        prev_date = next_date - relativedelta(
            **{periods[
                self.subscription_id.recurring_rule_type]:
                    self.subscription_id.recurring_interval})
        return next_date, prev_date

    def _get_invoice_period_from_name(self):
        """Gets invoice period based on name via regex"""
        try:
            regexp = _("Invoicing period") + ": (.*) - (.*)"
            match = re.search(regexp, self.name)
            start_date = parse_date(self.env, match.group(1))
            end_date = parse_date(self.env, match.group(2))
            if not isinstance(start_date, date) or not isinstance(
                    end_date, date):
                start_date = end_date = None
        except AttributeError:
            return None, None, None
        return start_date, start_date, end_date

    def _generate_period_msg(self, startdate_display, end_date):
        """Generates period string for name"""
        lang = self.order_id.partner_invoice_id.lang
        field_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        if lang:
            self = self.with_context(lang=lang)
        msg = f"Invoicing period: " \
              f"{field_date(fields.Date.to_string(startdate_display), {})} - " \
              f"{field_date(fields.Date.to_string(end_date), {})}"
        return self.name + '\n' + msg

    def _update_subscription_info(self, res):
        """Updates subscription info based on subscription and order."""
        update_dict = {}
        if self.subscription_id.analytic_account_id:
            update_dict['analytic_account_id'] = \
                self.subscription_id.analytic_account_id.id
        next_date, prev_date = self._get_periods()
        period_msg = _("Invoicing period") in self.name
        start_date, startdate_display, end_date = False, False, False
        if self.order_id.subscription_management != 'upsell':
            start_date = prev_date
            end_date = next_date - relativedelta(days=1)
        else:
            start_date, startdate_display, end_date = \
                self._get_invoice_period_from_name()
            if period_msg:
                if not start_date or not startdate_display or not end_date:
                    total_days = (next_date - prev_date).days
                    days = round((1 - self.discount / 100.0) * total_days)
                    start_date = next_date - relativedelta(days=days + 1)
                    startdate_display = next_date - relativedelta(days=days)
                    end_date = next_date - relativedelta(days=1)
        if not period_msg:
            update_dict['name'] = self._generate_period_msg(startdate_display, end_date)
        res.update({
            'subscription_id': self.subscription_id.id,
            'subscription_start_date': start_date,
            'subscription_end_date': end_date,
            **update_dict
        })
        return res

    def _refactor_solution(self, **kwargs):
        """Injects update of subscription info"""
        res = super(Solution1, self)._refactor_solution(**kwargs)
        if self.subscription_id:
            return self._update_subscription_info(res)
        return res


"""
Exercise 2:
a) Explain the meaning of cognitive complexity.
- Cognitive complexity is about lowering complexity whenever it is readable and suits us.
The lower - the better, but we should not "overdo" it so code is readable.
b) Take a look at the 4 methods of the class Excercise2 and refactor them to reduce their cognitive complexity.
"""


class Excercise2(models.Model):

    def _cognitive_complexity_1(self):
        for record in self:
            for line in record.order_id.order_line:
                if line.qty > 10:
                    return True
        return False

    def _cognitive_complexity_2(self):
        for record in self:
            if record.state == "done":
                record.is_done = True
            else:
                record.is_done = False

    def _cognitive_complexity_3(self):
        partner_ids = self.env["res.partner"]
        for record in self:
            for line in record.registration_id.login_ids:
                partner_ids |= line.partner_id
        return partner_ids

    def _cognitive_complexity_4(self):
        for record in self:
            partner_login_ids = record.registration_id.login_ids.filtered(
                lambda r: r.partner_id == record.partner_id)
            if partner_login_ids and record.partner_id.contact_type == "contact" and record.partner_id.email:
                continue
            record._create_partner_login()
        return


class Solution2(models.Model):

    def _cognitive_complexity_1(self):
        return any(
            line.qty > 10 for record in self for line in record.order_id.order_line)

    def _cognitive_complexity_2(self):
        for record in self:
            record.is_done = record.state == "done"

    def _cognitive_complexity_3(self):
        partner_ids = self.env["res.partner"]
        for rec in self:
            partner_ids += rec.registration_id.login_ids
        return partner_ids
        # or this
        # return self.env["res.partner"].concatenate(
        #     [line.partner_id for record in self for line in
        #      record.registration_id.login_ids])

    def _cognitive_complexity_4(self):
        for record in self:
            if record.partner_id.contact_type != "contact" and not \
                    record.partner_id.email and not \
                    record.registration_id.login_ids.filtered(
                        lambda r: r.partner_id == record.partner_id):
                record._create_partner_login()
