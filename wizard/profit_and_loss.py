from openerp import fields, models, api
from openerp.report import report_sxw
import time
from datetime import datetime
from mx.DateTime import DateTime as mxDateTime, RelativeDateTime as mxRelativeDateTime

class profit_and_loss_report(models.TransientModel):
    _name = 'report.profit.and.loss.detail'
    _description = 'Profit and Loss detail'

    def compute_default_company_id(self):
        return self.env['res.users'].browse(self.env.uid).company_id.id

    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=compute_default_company_id)
    date_start = fields.Date(string='Start date', required=True)
    date_end = fields.Date(string='End date', required=True)
    
    def format_decimal_number(self, number, point_numbers=2, separator=','):
        number_string = str(round(round(number, point_numbers+1),point_numbers))
        for x in range(0, point_numbers):
            if len(number_string[number_string.rfind('.')+1:]) < 2:
                number_string += '0'
            else:
                break
        number_string = number_string.replace('.',separator)
        if (len(number_string) > 6 and number>=0) or (len(number_string) > 7 and number<0):
            number_string = number_string[:len(number_string)-6] + '.' + number_string[len(number_string)-6:]
        return number_string
    
    @api.model
    def _get_data(self):
        account_account_env = self.env['account.account']
        
        date_format = "%Y-%m-%d"
        date_start_datetime = datetime.strptime(self.date_start, date_format)
        date_end_datetime = datetime.strptime(self.date_end, date_format)

        #represents a table of string dates. All date starts at the first day of a month
        account_periods = []
                
        #start with the report start date
        date_period_string = datetime.strptime(self.date_start, date_format).strftime("%Y-%m-01")
        date_period_datetime = datetime.strptime(date_period_string, date_format)

        while True:
            if date_period_datetime > date_end_datetime:
                break
            
            account_periods.append(date_period_string)

            date_period_mxDateTime = mxDateTime(date_period_datetime.year, date_period_datetime.month, date_period_datetime.day)+mxRelativeDateTime(months=1)
            date_period_datetime = datetime(date_period_mxDateTime.year, date_period_mxDateTime.month, date_period_mxDateTime.day)
            date_period_string = date_period_datetime.strftime("%Y-%m-%d")

        codes = [{'code':6, 'codes': [{'code':60},{'code':61},{'code':62},{'code':63},{'code':64},{'code':65},{'code':66},{'code':67},{'code':68},{'code':69}]},{'code':7, 'codes': [{'code':70},{'code':71},{'code':72},{'code':73},{'code':74},{'code':75},{'code':76},{'code':77},{'code':78},{'code':79}]}]
        
        def _init_code(code):
            code['name'] = ""
            code['sum'] = 0
            code['display'] = True
            code['periods'] = []
            search_code = str(code['code'])
            while len(search_code)<6:
                search_code += '0'
            account_account = account_account_env.search([('code','=',search_code),('company_id','=',self.company_id.id)], limit=1)
            if account_account:
                code['name'] = account_account.name
            for account_period in account_periods:
                code['periods'].append({'date': account_period, 'sum': 0})
        
        for code in codes:
            _init_code(code)
            for subcode in code['codes']:
                _init_code(subcode)
        
        cr = self.env.cr
        for code in codes:
            if str(code['code']) == '7':               
                cr.execute('''SELECT SUM(l.debit-l.credit) AS line_sum, l.date AS period_date, pc.name AS cat_name
                              FROM account_move_line l
                              LEFT JOIN account_move am ON (l.move_id=am.id)
                              LEFT JOIN account_account acc ON (l.account_id = acc.id)
                              LEFT JOIN product_product p ON (l.product_id = p.id)
                              LEFT JOIN product_template pt ON (p.product_tmpl_id = pt.id)
                              LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
                              WHERE l.date >= %s
                              AND l.date <= %s
                              AND l.company_id = %s
                              AND acc.code LIKE %s
                              AND am.state = %s
                              GROUP BY l.date, pc.name''', (self.date_start, self.date_end, self.company_id.id, str(code['code'])+'%','posted'))
                
                product_cat_dict = {}
                categories = []
                for row in cr.dictfetchall():
                    if row['line_sum']:
                        category_name = row['cat_name']
                        if product_cat_dict.has_key(category_name):
                            cat_dict_tmp = product_cat_dict[category_name]
                            for x in range(len(account_periods)):
                                if str(cat_dict_tmp['periods'][x]['date']) == datetime.strptime(str(row['period_date']), date_format).strftime("%Y-%m-01"):
                                    cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                    break  
                            cat_dict_tmp['sum'] += row['line_sum']
                        else:
                            cat_dict_tmp = {'name': category_name, 'sum': row['line_sum']}
                            cat_dict_tmp['periods'] = []
                            for account_period in account_periods:
                                cat_dict_tmp['periods'].append({'date': account_period, 'sum': 0})
                            for x in range(len(account_periods)):
                                if str(cat_dict_tmp['periods'][x]['date']) == datetime.strptime(str(row['period_date']), date_format).strftime("%Y-%m-01"):
                                    cat_dict_tmp['periods'][x]['sum'] += row['line_sum']
                                    break
                            product_cat_dict[category_name] = cat_dict_tmp
                
                keys = product_cat_dict.keys()
                product_cat_list = []
                for name in keys:
                    product_cat_list.append(product_cat_dict[name])
                product_cat_list.sort(lambda x,y : cmp(x['name'], y['name']))
                code['categories'] = product_cat_list
                
            for subcode in code['codes']:
                cr.execute('''SELECT SUM(l.credit-l.debit) AS line_sum, l.date AS period_date
                              FROM account_move_line l
                              LEFT JOIN account_account acc ON (l.account_id = acc.id)
                              LEFT JOIN account_move am ON (l.move_id=am.id)
                              WHERE l.date >= %s
                              AND l.date <= %s
                              AND l.company_id = %s
                              AND acc.code LIKE %s
                              AND am.state = %s
                              GROUP BY l.date''', (self.date_start, self.date_end, self.company_id.id, str(subcode['code'])+'%','posted'))                   

                for row in cr.dictfetchall():
                    if row['line_sum']:
                        for x in range(len(account_periods)):
                            if str(account_periods[x]) == datetime.strptime(str(row['period_date']), date_format).strftime("%Y-%m-01"):
                                subcode['periods'][x]['sum'] += row['line_sum']
                                code['periods'][x]['sum'] += row['line_sum']
                                break
                        subcode['sum']+= row['line_sum']
                code['sum'] += subcode['sum']
        
        for code in codes:
            for subcode in code['codes']:
                display = False
                for period in subcode['periods']:
                    if period['sum']!=0:
                        display = True
                        break
                subcode['display'] = display
        
        total = {}
        total['name'] = "Total"
        total['sum'] = 0
        total['periods'] = []
        for account_period in account_periods:
            total['periods'].append({'date': account_period, 'sum': 0})
        
        for code in codes:
            for x in range(len(account_periods)):
                total['periods'][x]['sum'] += code['periods'][x]['sum']
            total['sum'] += code['sum']
        
        account_periods_names = []
        for account_period in account_periods:
            account_periods_names.append(account_period[:-3])

        result = {}
        result.update({
                        'company_name': self.company_id.name,
                        'date_start': self.date_start,
                        'date_end':  self.date_end,})
        result['codes'] = codes
        result['periods'] = account_periods_names
        result['total'] = total
        result['currency_symbol'] = self.company_id.currency_id.symbol
        result['landscape'] = True
        return result

    @api.multi
    def print_report(self):           
        data = {
                'ids': self.ids,
                'model': 'report.profit.and.loss.detail',
                'form': self._get_data(),
               }
        return self.env['report'].get_action(self, 'report_profit_and_loss.report_profitandloss', data=data)

class profit_and_loss_report_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(profit_and_loss_report_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

class wrapped_profit_and_loss_report_print(models.AbstractModel):
    _name = 'report.report_profit_and_loss.report_profitandloss'
    _inherit = 'report.abstract_report'
    _template = 'report_profit_and_loss.report_profitandloss'
    _wrapped_report_class = profit_and_loss_report_print
