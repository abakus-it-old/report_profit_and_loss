from openerp.osv import fields, osv
from openerp.report import report_sxw
import time


class profit_and_loss_report(osv.osv_memory):
    _name = 'report.profit.and.loss'
    _description = 'Profit and Loss'

    _columns = {
        'company_id': fields.many2one('res.company', string='Company'),
        'consolidated': fields.boolean(string='Consolidated', default=False),
        'period_from': fields.many2one('account.period', string='Start period'),
        'period_to': fields.many2one('account.period', string='End period'),
    }

    def _get_datas(self, cr, uid, ids, context=None):
        account_account_obj = self.pool.get('account.account')
        account_period_obj = self.pool.get('account.period')
        wiz_data = self.browse(cr, uid, ids[0], context=context)
        
        account_periods = []
        account_period_ids = account_period_obj.search(cr, uid, [('date_start','>=',wiz_data.period_from.date_start),('date_stop','<=',wiz_data.period_to.date_stop),('company_id','=',wiz_data.company_id.id)], order='date_start')
        if not account_period_ids:
            return {
                'warning': {
                            'title': "Search error",
                            'message': "No account periods found",
                            },
            }
            
        for account_period in account_period_obj.browse(cr, uid, account_period_ids):
            account_periods.append({'id':account_period.id, 'name':account_period.name})

        codes = [{'code':6, 'codes': [{'code':60},{'code':61},{'code':62},{'code':63},{'code':64},{'code':64},{'code':65}]},{'code':7, 'codes': [{'code':70},{'code':71},{'code':72},{'code':73},{'code':74},{'code':75}]}]
        
        def _init_code(code):
            code['name'] = ""
            code['sum'] = 0
            code['periods'] = []
            account_account_id = account_account_obj.search(cr, uid, [('code','=',str(code['code'])),('company_id','=',str(wiz_data.company_id.id))])
            if account_account_id:
                account_account = account_account_obj.browse(cr, uid, account_account_id[0])
                code['name'] = account_account.name
            for account_period in account_periods:
                code['periods'].append({'id': account_period['id'], 'sum': 0})
        
        for code in codes:
            _init_code(code)
            for subcode in code['codes']:
                _init_code(subcode)
        
        for code in codes:
            for subcode in code['codes']:
                """
                if str(subcode['code']) == '70':
                    cr.execute('''SELECT SUM(l.debit-l.credit) AS line_sum, l.period_id AS period_id, pc.name AS cat_name
                                  FROM account_move_line l
                                  LEFT JOIN account_account acc ON (l.account_id = acc.id)
                                  LEFT JOIN producd_product p ON (l.product_id = p.id)
                                  LEFT JOIN producd_template pt ON (p.product_tmpl_id = pt.id)
                                  LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
                                  WHERE l.period_id IN %s
                                  AND l.company_id = %s
                                  AND acc.code LIKE %s
                                  GROUP BY l.period_id''', (tuple(account_period_ids), wiz_data.company_id.id, str(subcode['code'])+'%'))
                    
                    product_cat = {}
                    for row in cr.dictfetchall():
                        if row['line_sum']:
                            tmp = "\n\nsubcode: %s, line_sum: %s, period_id: %s, code_query: %s,\n\n" % (subcode['code'], str(row['line_sum']),str(row['period_id']),str(subcode['code'])+'%')
                            with open('/var/log/odoo/odoo-server.log', 'a') as f:
                                f.write(tmp)
                            for x in range(len(account_periods)):
                                if str(account_periods[x]['id']) == str(row['period_id']):
                                    subcode['periods'][x]['sum'] += row['line_sum']
                                    code['periods'][x]['sum'] += row['line_sum']
                                    break
                            subcode['sum']+= row['line_sum']
                    code['sum'] += subcode['sum']

                else:  
                """
                cr.execute('''SELECT SUM(l.debit-l.credit) AS line_sum, l.period_id AS period_id
                              FROM account_move_line l
                              LEFT JOIN account_account acc ON (l.account_id = acc.id)
                              WHERE l.period_id IN %s
                              AND l.company_id = %s
                              AND acc.code LIKE %s
                              GROUP BY l.period_id''', (tuple(account_period_ids), wiz_data.company_id.id, str(subcode['code'])+'%'))                      

                for row in cr.dictfetchall():
                    if row['line_sum']:
                        """
                        tmp = "\n\nsubcode: %s, line_sum: %s, period_id: %s, code_query: %s,\n\n" % (subcode['code'], str(row['line_sum']),str(row['period_id']),str(subcode['code'])+'%')
                        with open('/var/log/odoo/odoo-server.log', 'a') as f:
                            f.write(tmp)
                        """    
                        for x in range(len(account_periods)):
                            if str(account_periods[x]['id']) == str(row['period_id']):
                                subcode['periods'][x]['sum'] += row['line_sum']
                                code['periods'][x]['sum'] += row['line_sum']
                                break
                        subcode['sum']+= row['line_sum']
                code['sum'] += subcode['sum']
        
        result = {}
        result.update({
                        'company_name': wiz_data.company_id.name,
                        'period_start': wiz_data.period_from.name,
                        'period_end':  wiz_data.period_to.name,})
        result['codes'] = codes
        result['periods'] = account_periods
        return result
        
    def check_report(self, cr, uid, ids, context=None):     
        datas = {
            'ids': ids,
            'model': 'report.profit.and.loss',
            'form': self._get_datas(cr, uid, ids)
        }

        return self.pool['report'].get_action(cr, uid, [], 'report_profit_and_loss.report_profitandloss', data=datas, context=context)

class profit_and_loss_report_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(profit_and_loss_report_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

class wrapped_profit_and_loss_report_print(osv.AbstractModel):
    _name = 'report.report_profit_and_loss.report_profitandloss'
    _inherit = 'report.abstract_report'
    _template = 'report_profit_and_loss.report_profitandloss'
    _wrapped_report_class = profit_and_loss_report_print
