#!/usr/bin/env python3
"""Development-only browser checks; requires Playwright, Pillow and Chromium.
Run a local server first. See RESPONSIVE_QA.md for commands and coverage.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import argparse
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
LAYOUT_ASSERTIONS = r"""()=>{
      const errors=[],width=innerWidth;
      if(document.documentElement.scrollWidth>width)errors.push('document overflow '+document.documentElement.scrollWidth);
      for(const el of document.querySelectorAll('body *')){
        const r=el.getBoundingClientRect(),s=getComputedStyle(el);
        if(!r.width||s.display==='none'||el.tagName==='SCRIPT')continue;
        if(r.left<-.5||r.right>width+.5)errors.push('outside viewport '+el.tagName+'.'+el.className);
        if(el.scrollWidth>el.clientWidth+2&&s.display!=='inline')errors.push('clipped content '+el.tagName+'.'+el.className);
      }
      if(width<=1100){
        for(const el of document.querySelectorAll('a,button')){
          const r=el.getBoundingClientRect();if(r.width&&(r.width<44||r.height<44))errors.push('small target '+el.textContent);
        }
        if(getComputedStyle(document.querySelector('.links')).display==='none')errors.push('missing nav');
        for(const i of document.querySelectorAll('.mockup-grid img'))if(Math.abs(i.width/i.height-i.naturalWidth/i.naturalHeight)>.02)errors.push('cropped mockup '+i.alt);
      }
      for(const grid of document.querySelectorAll('.nav-inner,.links,.nav-actions,.grid-3,.process,.moscow-grid,.tool-grid,.design-system-grid')){
        const boxes=[...grid.children].map(el=>({el,r:el.getBoundingClientRect()})).filter(({r})=>r.width&&r.height);
        for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
          const a=boxes[i].r,b=boxes[j].r;
          if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)errors.push('overlapping siblings '+grid.className);
        }
      }
      return [...new Set(errors)];
    }"""

parser = argparse.ArgumentParser(description='Audit the served portfolio at responsive breakpoints.')
parser.add_argument('--url', default='http://127.0.0.1:8000')
parser.add_argument('--baseline', default='origin/main', help='Git ref for desktop CSS comparison')
parser.add_argument('--output', default='/tmp/portfolio-responsive-audit')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
baseline_css = subprocess.check_output(['git', 'show', args.baseline + ':style.css'], cwd=root, text=True)
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
issues = []
count = 0
widths = (320, 360, 375, 390, 430, 560, 600, 620, 621, 767, 768, 834, 960, 961, 1024, 1100, 1101, 1280, 1440)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'), args=['--no-sandbox'])
    context = b.new_context()
    page = context.new_page()
    page.on('pageerror', lambda e: issues.append(str(e)))
    for w in widths:
        page.set_viewport_size({'width': w, 'height': 900})
        for f in ('index', 'meddone', 'vertex', 'ecommerce'):
            page.goto(f'{args.url}/{f}.html')
            for lang in ('en', 'it'):
                if page.locator('html').get_attribute('lang') != lang:
                    page.locator('[data-language-toggle]').click()
                errors = page.evaluate(LAYOUT_ASSERTIONS)
                issues.extend((f'{w} {f} {lang}: {e}' for e in errors))
                count += 1
                if w in (375, 768, 1024, 1440):
                    path = out / f'after-{f}-{lang}-{w}.png'
                    page.mouse.move(0, 0)
                    page.screenshot(path=str(path), full_page=w == 375, animations='disabled')
                    if w == 1440:
                        after = out / f'desktop-current-{f}-{lang}.png'
                        geometry = page.locator('body *').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')
                        page.screenshot(path=str(after), full_page=True, animations='disabled')
                        page.route('**/style.css', lambda route: route.fulfill(body=baseline_css, content_type='text/css'))
                        page.reload()
                        before = out / f'desktop-baseline-{f}-{lang}.png'
                        page.screenshot(path=str(before), full_page=True, animations='disabled')
                        a, z = (Image.open(after), Image.open(before))
                        baseline_geometry = page.locator('body *').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})')
                        if geometry != baseline_geometry:
                            issues.append(f'Desktop geometry differs: {f} {lang}')
                        if a.size != z.size or any((high > 3 for low, high in ImageChops.difference(a, z).getextrema())):
                            issues.append(f'Desktop appearance differs: {f} {lang}')
                        page.unroute('**/style.css')
                        page.reload()
    fresh = b.new_context(locale='it-IT', reduced_motion='reduce', has_touch=True, viewport={'width': 390, 'height': 844})
    phone = fresh.new_page()
    phone.goto(args.url + '/index.html')
    assert phone.locator('html').get_attribute('lang') == 'en'
    phone.locator('[data-language-toggle]').focus()
    phone.keyboard.press('Enter')
    assert phone.locator('html').get_attribute('lang') == 'it'
    phone.reload()
    assert phone.locator('html').get_attribute('lang') == 'it'
    phone.locator('.links a[href="index.html#about"]').click()
    assert phone.locator('#about').bounding_box()['y'] >= phone.locator('.nav').bounding_box()['height']
    phone.locator('a[href="meddone.html"]').click()
    assert phone.locator('html').get_attribute('lang') == 'it'
    phone.locator('.actions a[href="#process"]').click()
    assert phone.locator('#process').bounding_box()['y'] >= phone.locator('.nav').bounding_box()['height']
    phone.go_back()
    phone.go_back()
    assert phone.locator('html').get_attribute('lang') == 'it'
    second = fresh.new_page()
    second.goto(args.url + '/vertex.html')
    phone.locator('[data-language-toggle]').click()
    second.wait_for_function("document.documentElement.lang==='en'")
    phone.set_viewport_size({'width': 844, 'height': 390})
    phone.goto(args.url + '/ecommerce.html')
    assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert phone.locator('[data-language-toggle]').is_visible()
    assert phone.evaluate("getComputedStyle(document.documentElement).scrollBehavior==='auto'")
    blocked = b.new_context()
    blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}})")
    bp = blocked.new_page()
    bp.goto(args.url + '/')
    bp.locator('[data-language-toggle]').click()
    assert bp.locator('html').get_attribute('lang') == 'it'
    print('Keyboard, navigation, anchor clearance, preferences, cross-tab sync, blocked storage, reduced motion and landscape checks passed.')
    b.close()
(out / 'results.json').write_text(json.dumps({'combinations': count, 'widths': widths, 'issues': issues}, indent=2))
print(f'{count} page/language/viewport combinations checked.')
for e in issues:
    print(e)
raise SystemExit(bool(issues))
