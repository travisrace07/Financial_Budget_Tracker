"""Build an allowlisted, sample-only static site for GitHub Pages."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs'


def main():
    (DEST / 'static').mkdir(parents=True, exist_ok=True)
    html = (ROOT / 'templates/index.html').read_text()
    html = html.replace('<html lang="en">', '<html lang="en" data-portfolio-demo="true">')
    html = html.replace('/static/', './static/').replace('href="/"', 'href="./"')
    html = html.replace('Ledger · Personal finance', 'Ledger · Portfolio demo')
    html = html.replace('PERSONAL WORKSPACE', 'PORTFOLIO DEMO')
    html = html.replace('Review and correct automatic categories.', 'Explore fictional transactions. Category editing is available in the full app.')
    (DEST / 'index.html').write_text(html)
    for name in ('app.js', 'style.css', 'favicon.svg', 'sample.csv'):
        shutil.copyfile(ROOT / 'static' / name, DEST / 'static' / name)
    (DEST / '.nojekyll').touch()
    print('Built sample-only demo in docs/')


if __name__ == '__main__':
    main()
