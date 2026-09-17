import csv
import hashlib
import io
import os
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from flask import Flask, jsonify, request, render_template
from sqlalchemy import create_engine, String, Integer, Date, Numeric, select, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

CATEGORIES = ['Income', 'Housing', 'Groceries', 'Dining', 'Transport', 'Shopping', 'Entertainment', 'Utilities', 'Health', 'Transfers', 'Other']
RULES = {'Income': ['payroll', 'salary', 'direct deposit'], 'Housing': ['rent', 'mortgage'], 'Groceries': ['whole foods', 'trader joe', 'grocery', 'kroger', 'aldi', 'safeway'], 'Dining': ['restaurant', 'coffee', 'starbucks', 'doordash', 'chipotle', 'cafe'], 'Transport': ['uber', 'lyft', 'shell', 'chevron', 'gas', 'transit'], 'Entertainment': ['netflix', 'spotify', 'hulu', 'cinema', 'apple music'], 'Utilities': ['electric', 'internet', 'water', 'verizon', 'comcast'], 'Health': ['pharmacy', 'cvs', 'doctor', 'gym'], 'Transfers': ['transfer', 'credit card payment'], 'Shopping': ['amazon', 'target', 'walmart', 'store']}

def categorize(description, amount):
    for category, words in RULES.items():
        if any(word in description.lower() for word in words):
            return category
    return 'Income' if amount > 0 else 'Other'

class Base(DeclarativeBase): pass
class Transaction(Base):
    __tablename__ = 'transactions'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    category: Mapped[str] = mapped_column(String(40))
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
class Budget(Base):
    __tablename__ = 'budgets'
    __table_args__ = (UniqueConstraint('month', 'category'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[str] = mapped_column(String(7))
    category: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

def money(raw):
    value = str(raw).strip().replace('$', '').replace(',', '')
    if value.startswith('(') and value.endswith(')'): value = '-' + value[1:-1]
    try: result = Decimal(value or '0')
    except InvalidOperation: raise ValueError('Invalid amount')
    if not result.is_finite() or abs(result) > Decimal('999999999999.99'): raise ValueError('Amount is out of range')
    if result != result.quantize(Decimal('.01')): raise ValueError('Amounts may have at most two decimal places')
    return result

def parse_csv(content, positive_expenses=False):
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames: raise ValueError('The CSV is empty')
    aliases = {'transaction date': 'date', 'posted date': 'date', 'merchant': 'description', 'memo': 'description', 'details': 'description'}
    fields = [aliases.get(f.strip().lower(), f.strip().lower()) for f in reader.fieldnames]
    if len(fields) != len(set(fields)): raise ValueError('Duplicate column names')
    reader.fieldnames = fields
    if not {'date', 'description'}.issubset(fields) or not ('amount' in fields or {'debit', 'credit'}.issubset(fields)):
        raise ValueError('Use date, description, amount columns, or date, description, debit, credit')
    result, occurrences = [], defaultdict(int)
    for number, row in enumerate(reader, 2):
        if number > 10001: raise ValueError('Maximum 10,000 transactions per file')
        try:
            if None in row or any(v is None for v in row.values()): raise ValueError('Column count does not match header')
            parsed = None
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
                try: parsed = datetime.strptime(row['date'].strip(), fmt).date(); break
                except ValueError: pass
            if parsed is None: raise ValueError('Use YYYY-MM-DD or MM/DD/YYYY dates')
            description = row['description'].strip()
            if not description or len(description) > 255: raise ValueError('Description must be 1–255 characters')
            if 'amount' in fields:
                amount = money(row['amount']) * (-1 if positive_expenses else 1)
            else:
                debit, credit = money(row['debit']), money(row['credit'])
                if debit < 0 or credit < 0 or (debit and credit): raise ValueError('Use positive debit or credit, not both')
                amount = credit - debit
            category = row.get('category', '').strip() or categorize(description, amount)
            if category not in CATEGORIES: raise ValueError('Unknown category: ' + category)
            key = f'{parsed}|{description.lower()}|{amount:.2f}'
            occurrences[key] += 1
            fingerprint = hashlib.sha256(f'{key}|{occurrences[key]}'.encode()).hexdigest()
            result.append(dict(date=parsed, description=description, amount=amount, category=category, fingerprint=fingerprint))
        except ValueError as e: raise ValueError(f'Row {number}: {e}')
    if not result: raise ValueError('No transactions found')
    return result

def create_app(database_url=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    url = database_url or os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('Set DATABASE_URL to mysql+pymysql://user:password@localhost/ledger (see README)')
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    app.config['DB_SESSION'] = Session
    @app.errorhandler(413)
    def too_large(e): return jsonify(error='File must be smaller than 5 MB'), 413
    @app.before_request
    def same_origin():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'): return jsonify(error='Cross-origin request blocked'), 403
    @app.get('/')
    def home(): return render_template('index.html')
    @app.get('/api/dashboard')
    def dashboard():
        month = request.args.get('month', date.today().strftime('%Y-%m'))
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month): return jsonify(error='Invalid month'), 400
        with Session() as session:
            records = session.scalars(select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())).all()
            selected = [t for t in records if t.date.strftime('%Y-%m') == month]
            income = sum((t.amount for t in selected if t.amount > 0 and t.category != 'Transfers'), Decimal(0))
            expenses = -sum((t.amount for t in selected if t.amount < 0 and t.category != 'Transfers'), Decimal(0))
            spending = defaultdict(Decimal)
            for t in selected:
                if t.amount < 0 and t.category != 'Transfers': spending[t.category] -= t.amount
            trend = []
            y, m = map(int, month.split('-'))
            for offset in range(5, -1, -1):
                index = y * 12 + m - 1 - offset
                key = f'{index // 12:04}-{index % 12 + 1:02}'
                items = [t for t in records if t.date.strftime('%Y-%m') == key and t.category != 'Transfers']
                inc = sum((t.amount for t in items if t.amount > 0), Decimal(0))
                exp = -sum((t.amount for t in items if t.amount < 0), Decimal(0))
                trend.append(dict(month=key, income=float(inc), expenses=float(exp), savings_rate=float((inc-exp)/inc*100) if inc else None))
            groups = defaultdict(list)
            for t in records:
                if t.amount < 0 and t.category != 'Transfers': groups[re.sub(r'\s+', ' ', t.description.lower()).strip()].append(t)
            recurring = []
            for name, items in groups.items():
                items = sorted(items, key=lambda t:t.date)
                if len(items) < 3: continue
                recent = items[-3:]
                gaps = [(b.date-a.date).days for a,b in zip(recent, recent[1:])]
                amounts = [abs(t.amount) for t in recent]
                cadence = next((label for low,high,label in [(6,8,'Weekly'), (13,15,'Every 2 weeks'), (26,35,'Monthly')] if all(low <= g <= high for g in gaps)), None)
                if cadence and max(amounts)-min(amounts) <= max(Decimal('1'), max(amounts)*Decimal('.1')) and recent[-1].date.strftime('%Y-%m') == month:
                    recurring.append(dict(description=recent[-1].description, amount=float(amounts[-1]), cadence=cadence, category=recent[-1].category))
            budgets = [dict(category=b.category, amount=float(b.amount), spent=float(spending[b.category])) for b in session.scalars(select(Budget).where(Budget.month==month))]
            return jsonify(month=month, categories=CATEGORIES, income=float(income), expenses=float(expenses), savings=float(income-expenses), savings_rate=float((income-expenses)/income*100) if income else None, spending={k:float(v) for k,v in spending.items()}, trend=trend, recurring=recurring, budgets=budgets, transactions=[dict(id=t.id,date=t.date.isoformat(),description=t.description,amount=float(t.amount),category=t.category) for t in selected], total_records=len(records))
    @app.post('/api/import')
    def import_csv():
        file = request.files.get('file')
        if not file: return jsonify(error='Choose a CSV file'), 400
        try: rows = parse_csv(file.read().decode('utf-8-sig'), request.form.get('positive_expenses') == 'true')
        except (ValueError, UnicodeError) as e: return jsonify(error=str(e)), 400
        with Session.begin() as session:
            existing = set(session.scalars(select(Transaction.fingerprint)))
            new = [r for r in rows if r['fingerprint'] not in existing]
            session.add_all(Transaction(**r) for r in new)
        return jsonify(imported=len(new), skipped=len(rows)-len(new), month=max(r['date'] for r in rows).strftime('%Y-%m'))
    @app.patch('/api/transactions/<int:ident>')
    def update_transaction(ident):
        category = (request.get_json(silent=True) or {}).get('category')
        if category not in CATEGORIES: return jsonify(error='Invalid category'), 400
        with Session.begin() as session:
            item = session.get(Transaction, ident)
            if not item: return jsonify(error='Transaction not found'), 404
            item.category = category
        return jsonify(ok=True)
    @app.put('/api/budgets')
    def budget():
        data = request.get_json(silent=True) or {}
        try:
            month, category = data.get('month', ''), data.get('category')
            if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month) or category not in CATEGORIES or category in ('Income', 'Transfers'): raise ValueError('Choose a valid month and spending category')
            amount = money(data.get('amount', ''))
            if amount <= 0: raise ValueError('Budget must be greater than zero')
        except ValueError as e: return jsonify(error=str(e)), 400
        with Session.begin() as session:
            b = session.scalar(select(Budget).where(Budget.month==month, Budget.category==category))
            if b: b.amount = amount
            else: session.add(Budget(month=month, category=category, amount=amount))
        return jsonify(ok=True)
    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=8000)
