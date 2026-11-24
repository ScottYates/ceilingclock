// node shoot.js <base-url> <jobs.json> : renders each job with render.html and writes its PNG.
// jobs: [{ out, model, floor, cam: [x,y,z], target: [x,y,z], fov }]  (model is a URL path on the server)
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const [base, jobsFile] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(base + '/hardware/pb_render/render.html');
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  for (const j of jobs) {
    const t0 = Date.now();
    const url = await page.evaluate(job => window.shot(job), j);
    fs.writeFileSync(j.out, Buffer.from(url.split(',')[1], 'base64'));
    console.log(j.out, ((Date.now() - t0) / 1000).toFixed(1) + ' s');
  }
  if (errors.length) console.log('errors:', errors.join('\n'));
  await browser.close();
})();
