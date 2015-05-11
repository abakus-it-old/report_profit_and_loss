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

        codes = [{'code':6, 'codes': [{'code':60},{'code':61},{'code':62},{'code':63},{'code':64},{'code':65},{'code':66},{'code':67},{'code':68},{'code':69}]},{'code':7, 'codes': [{'code':70},{'code':71},{'code':72},{'code':73},{'code':74},{'code':75},{'code':76},{'code':77},{'code':78},{'code':79}]}]
        
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
            if str(code['code']) == '7':
                cr.execute('''SELECT SUM(l.debit-l.credit) AS line_sum, l.period_id AS period_id, pc.name AS cat_name
                              FROM account_move_line l
                              LEFT JOIN account_account acc ON (l.account_id = acc.id)
                              LEFT JOIN product_product p ON (l.product_id = p.id)
                              LEFT JOIN product_template pt ON (p.product_tmpl_id = pt.id)
                              LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
                              WHERE l.period_id IN %s
                              AND l.company_id = %s
                              AND acc.code LIKE %s
                              GROUP BY l.period_id, pc.name''', (tuple(account_period_ids), wiz_data.company_id.id, str(code['code'])+'%'))
                
                product_cat_dict = {}
                categories = []
                for row in cr.dictfetchall():
                    if row['line_sum']:
                        category_name = row['cat_name']
                        if product_cat_dict.has_key(category_name):
                            cat_dict_tmp = product_cat_dict[category_name]
                            for x in range(len(account_periods)):
                                if str(cat_dict_tmp['periods'][x]['id']) == str(row['period_id']):
                                    cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                    break  
                            cat_dict_tmp['sum'] += row['line_sum']
                        else:
                            cat_dict_tmp = {'name': category_name, 'sum': row['line_sum']}
                            cat_dict_tmp['periods'] = []
                            for account_period in account_periods:
                                cat_dict_tmp['periods'].append({'id': account_period['id'], 'sum': 0})
                            for x in range(len(account_periods)):
                                if str(cat_dict_tmp['periods'][x]['id']) == str(row['period_id']):
                                    cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                    break
                            product_cat_dict[category_name] = cat_dict_tmp
                        break
                
                keys = product_cat_dict.keys()
                product_cat_list = []
                for name in keys:
                    product_cat_list.append(product_cat_dict[name])
                product_cat_list.sort(lambda x,y : cmp(x['name'], y['name']))
                code['categories'] = product_cat_list
                
            for subcode in code['codes']:
                """
                if str(code['code']) == '70':
                    cr.execute('''SELECT SUM(l.debit-l.credit) AS line_sum, l.period_id AS period_id, pc.name AS cat_name
                                  FROM account_move_line l
                                  LEFT JOIN account_account acc ON (l.account_id = acc.id)
                                  LEFT JOIN product_product p ON (l.product_id = p.id)
                                  LEFT JOIN product_template pt ON (p.product_tmpl_id = pt.id)
                                  LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
                                  WHERE l.period_id IN %s
                                  AND l.company_id = %s
                                  AND acc.code LIKE %s
                                  GROUP BY l.period_id, pc.name''', (tuple(account_period_ids), wiz_data.company_id.id, str(subcode['code'])+'%'))
                    
                    product_cat_dict = {}
                    categories = []
                    for row in cr.dictfetchall():
                        if row['line_sum']:
                            for x in range(len(account_periods)):
                                if str(account_periods[x]['id']) == str(row['period_id']):
                                    subcode['periods'][x]['sum'] += row['line_sum']
                                    code['periods'][x]['sum'] += row['line_sum']
                                    category_name = row['cat_name']
                                    if product_cat_dict.has_key(category_name):
                                        cat_dict_tmp = product_cat_dict[category_name]
                                        for x in range(len(account_periods)):
                                            if str(cat_dict_tmp['periods'][x]['id']) == str(row['period_id']):
                                                cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                                break  
                                        cat_dict_tmp['sum'] += row['line_sum']
                                    else:
                                        cat_dict_tmp = {'name': category_name, 'sum': row['line_sum']}
                                        cat_dict_tmp['periods'] = []
                                        for account_period in account_periods:
                                            cat_dict_tmp['periods'].append({'id': account_period['id'], 'sum': 0})
                                        for x in range(len(account_periods)):
                                            if str(cat_dict_tmp['periods'][x]['id']) == str(row['period_id']):
                                                cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                                break
                                        product_cat_dict[category_name] = cat_dict_tmp
                                    break
                            subcode['sum']+= row['line_sum']
                    code['sum'] += subcode['sum']
                    
                    keys = product_cat_dict.keys()
                    product_cat_list = []
                    for name in keys:
                        product_cat_list.append(product_cat_dict[name])
                    product_cat_list.sort(lambda x,y : cmp(x['name'], y['name']))
                    subcode['categories'] = product_cat_list

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
        
        total = {}
        total['name'] = "Total"
        total['sum'] = 0
        total['periods'] = []
        for account_period in account_periods:
            total['periods'].append({'id': account_period['id'], 'sum': 0})
        
        for code in codes:
            for x in range(len(account_periods)):
                total['periods'][x]['sum'] += code['periods'][x]['sum']
            total['sum'] += code['sum']
        
        result = {}
        result.update({
                        'company_name': wiz_data.company_id.name,
                        'period_start': wiz_data.period_from.name,
                        'period_end':  wiz_data.period_to.name,})
        result['codes'] = codes
        result['periods'] = account_periods
        result['total'] = total
        result['currency_symbol'] = wiz_data.company_id.currency_id.symbol
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
