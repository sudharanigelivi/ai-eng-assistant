DEMO_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f6f7fc">
  <title>Sudha Gelvi — URL Shortener</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #20233a; background: #f6f7fc; font-synthesis: none; }
    * { box-sizing: border-box; }
    body { min-height: 100vh; margin: 0; padding: 36px 20px 50px; }
    main { width: min(100%, 760px); margin: 0 auto; }
    .hero { padding: 8px 0 24px; text-align: center; }
    .brand { display: inline-flex; align-items: center; gap: 10px; margin-bottom: 30px; color: #252943; font-weight: 750; }
    .brand-mark { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 12px; background: linear-gradient(135deg, #7658ed, #5149ca); color: white; font-size: 1.1rem; box-shadow: 0 7px 18px #6654dc45; }
    .eyebrow { margin-bottom: 10px; color: #6253d8; font-size: .76rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(2.15rem, 7vw, 3.35rem); letter-spacing: -.055em; line-height: 1.05; }
    .tagline { margin: 14px 0 0; color: #6d7289; font-size: 1.05rem; }
    .card, .info-card { border: 1px solid #e8e9f2; border-radius: 20px; background: #fff; box-shadow: 0 16px 48px #29265c0d; }
    .card { padding: clamp(22px, 5vw, 34px); }
    label { display: block; margin: 0 0 8px; color: #343750; font-size: .88rem; font-weight: 750; }
    input { width: 100%; height: 49px; margin-bottom: 19px; padding: 0 14px; border: 1px solid #dfe1ec; border-radius: 10px; background: #fff; color: #22253d; font: inherit; outline: none; transition: border-color .16s, box-shadow .16s; }
    input::placeholder { color: #a0a3b4; }
    input:focus { border-color: #7564e6; box-shadow: 0 0 0 3px #7564e620; }
    .result-row { display: flex; gap: 9px; }
    .result-row input { min-width: 0; margin-bottom: 0; background: #f8f8fc; }
    button { min-height: 48px; border: 0; border-radius: 10px; font: inherit; font-weight: 750; cursor: pointer; transition: transform .12s, background .15s, opacity .15s; }
    button:hover:not(:disabled) { transform: translateY(-1px); }
    button:disabled { opacity: .52; cursor: not-allowed; }
    #copy { flex: 0 0 auto; padding: 0 16px; background: #eeecff; color: #5345c4; }
    #create { width: 100%; margin-top: 19px; background: linear-gradient(110deg, #705be4, #554bc9); color: #fff; box-shadow: 0 8px 18px #6255d62b; }
    #status { min-height: 24px; margin: 12px 0 0; color: #b42318; font-size: .88rem; }
    #status.success { color: #16834a; }
    .info-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }
    .info-card { padding: 21px 23px; }
    h2 { margin: 0 0 14px; font-size: 1rem; letter-spacing: -.015em; }
    ol, ul { display: grid; gap: 11px; margin: 0; padding: 0; color: #686d82; font-size: .88rem; list-style: none; }
    ol li { display: flex; align-items: center; gap: 10px; }
    ol span { display: grid; width: 23px; height: 23px; flex: 0 0 auto; place-items: center; border-radius: 8px; background: #f0edff; color: #5e4bd2; font-size: .76rem; font-weight: 800; }
    ul li::before { content: "✓"; margin-right: 9px; color: #6656da; font-weight: 800; }
    footer { margin-top: 16px; color: #85899c; font-size: .78rem; text-align: center; }
    @media (max-width: 560px) { body { padding: 24px 15px 34px; } .info-grid { grid-template-columns: 1fr; } .result-row { flex-direction: column; } #copy { min-height: 44px; } }
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div class="brand"><span class="brand-mark" aria-hidden="true">S</span><span>Sudha Gelvi</span></div>
      <div class="eyebrow">Smart links</div>
      <h1>URL Shortener</h1>
      <p class="tagline">Shorten links. Share smarter.</p>
    </header>
    <section class="card" aria-label="URL Shortener">
      <form id="shorten-form">
        <label for="url">Drop Link</label>
        <input id="url" name="url" type="url" placeholder="Paste your long URL here" required maxlength="2048">
        <label for="alias">Short Name <span style="color:#9295a7;font-weight:500">(optional)</span></label>
        <input id="alias" name="alias" type="text" placeholder="e.g. demo-link" minlength="4" maxlength="32" pattern="[A-Za-z0-9_\\-]{4,32}" title="Use 4–32 letters, numbers, hyphens, or underscores">
        <label for="short-url">Shortened URL</label>
        <div class="result-row">
          <input id="short-url" type="url" placeholder="Your short URL will appear here" readonly aria-live="polite">
          <button id="copy" type="button" disabled>Copy Link</button>
        </div>
        <button id="create" type="submit">Create Short Link</button>
        <p id="status" aria-live="polite" role="status"></p>
      </form>
    </section>
    <section class="info-grid" aria-label="How it works and features">
      <article class="info-card">
        <h2>How It Works</h2>
        <ol><li><span>1</span>Paste your original link.</li><li><span>2</span>Choose an optional short name.</li><li><span>3</span>Create and share your new link.</li></ol>
      </article>
      <article class="info-card">
        <h2>Features</h2>
        <ul><li>Custom aliases</li><li>Fast redirects</li><li>Demo links (temporary storage)</li><li>Click analytics</li></ul>
      </article>
    </section>
    <footer>Public demo — link creation is rate-limited. Don’t use for sensitive or permanent links.</footer>
  </main>
  <script>
    const form = document.querySelector('#shorten-form');
    const createButton = document.querySelector('#create');
    const copyButton = document.querySelector('#copy');
    const shortUrl = document.querySelector('#short-url');
    const status = document.querySelector('#status');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      shortUrl.value = '';
      copyButton.disabled = true;
      status.className = '';
      status.textContent = '';
      createButton.disabled = true;
      createButton.textContent = 'Creating…';
      const payload = { url: form.elements.url.value.trim() };
      if (form.elements.alias.value.trim()) payload.custom_alias = form.elements.alias.value.trim();
      try {
        const response = await fetch('/api/v1/links', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the URL and try again.');
        shortUrl.value = data.short_url;
        copyButton.disabled = false;
        status.className = 'success';
        status.textContent = 'Short link created — open it to test the redirect.';
      } catch (error) {
        status.textContent = error.message || 'Could not create the short link. Please try again.';
      } finally {
        createButton.disabled = false;
        createButton.textContent = 'Create Short Link';
      }
    });
    copyButton.addEventListener('click', async () => {
      if (!shortUrl.value) return;
      try {
        await navigator.clipboard.writeText(shortUrl.value);
        status.className = 'success';
        status.textContent = 'Short link copied to clipboard.';
      } catch {
        shortUrl.select();
        document.execCommand('copy');
        status.className = 'success';
        status.textContent = 'Short link copied to clipboard.';
      }
    });
  </script>
</body>
</html>
"""

PROTECTED_HOME_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>URL Shortener API</title></head>
<body><h1>URL Shortener API</h1><p>Link creation is available through the authenticated API.</p>
<p><a href="/docs">Open API documentation</a></p></body></html>
"""
