import io
import os
import unittest
from app import create_app, parse_csv, Base
from sqlalchemy import create_engine

class LedgerTests(unittest.TestCase):
    def setUp(self):
        url=os.environ.get('TEST_DATABASE_URL','sqlite:///:memory:')
        if url != 'sqlite:///:memory:': Base.metadata.drop_all(create_engine(url))
        self.app=create_app(url)
        self.client=self.app.test_client()
    def upload(self,text):
        return self.client.post('/api/import',data={'file':(io.BytesIO(text.encode()),'bank.csv')})
    def test_totals_duplicates_and_category_correction(self):
        text='date,description,amount\n2026-09-01,Payroll,3000\n2026-09-02,Whole Foods,-100\n2026-09-02,Whole Foods,-100\n2026-09-03,Transfer,-500\n'
        self.assertEqual(self.upload(text).json['imported'],4)
        self.assertEqual(self.upload(text).json['skipped'],4)
        d=self.client.get('/api/dashboard?month=2026-09').json
        self.assertEqual((d['income'],d['expenses'],d['savings']),(3000,200,2800))
        self.assertAlmostEqual(d['savings_rate'],93.3333333)
        ident=next(t['id'] for t in d['transactions'] if t['category']=='Groceries')
        self.assertEqual(self.client.patch(f'/api/transactions/{ident}',json={'category':'Dining'}).status_code,200)
        d=self.client.get('/api/dashboard?month=2026-09').json
        self.assertEqual(d['spending']['Dining'],100)
    def test_atomic_invalid_import(self):
        r=self.upload('date,description,amount\n2026-09-01,Payroll,100\nwrong,Oops,NaN\n')
        self.assertEqual(r.status_code,400)
        self.assertEqual(self.client.get('/api/dashboard').json['total_records'],0)
    def test_budget_and_recurring(self):
        self.upload('date,description,amount\n2026-07-05,Netflix,-15.49\n2026-08-05,Netflix,-15.49\n2026-09-05,Netflix,-15.49\n')
        for amount in [50,70]:
            self.assertEqual(self.client.put('/api/budgets',json=dict(month='2026-09',category='Entertainment',amount=amount)).status_code,200)
        d=self.client.get('/api/dashboard?month=2026-09').json
        self.assertEqual(len(d['budgets']),1)
        self.assertEqual(d['budgets'][0]['amount'],70)
        self.assertEqual(d['budgets'][0]['spent'],15.49)
        self.assertEqual(d['recurring'][0]['cadence'],'Monthly')
        self.assertIsNone(d['savings_rate'])
    def test_parser_and_validation(self):
        self.assertEqual(float(parse_csv('date,merchant,debit,credit\n09/01/2026,Shop,25,\n')[0]['amount']),-25)
        self.assertEqual(float(parse_csv('date,description,amount\n2026-09-01,Shop,25\n',True)[0]['amount']),-25)
        for value in ['NaN','Infinity','1.001']:
            with self.assertRaises(ValueError):parse_csv(f'date,description,amount\n2026-09-01,Shop,{value}\n')
        self.assertEqual(self.client.get('/api/dashboard?month=no').status_code,400)
        self.assertEqual(self.client.put('/api/budgets',json=dict(month='2026-09',category='Dining',amount=-1)).status_code,400)
    def test_origin_and_page(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.put('/api/budgets',headers={'Origin':'https://other.example'},json={}).status_code,403)

if __name__=='__main__':unittest.main()
