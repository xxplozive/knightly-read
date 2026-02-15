export default {
  async fetch(request) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders(),
      });
    }

    const url = new URL(request.url);
    const location = url.searchParams.get('location');
    const country = url.searchParams.get('country') || 'US';
    const lang = url.searchParams.get('lang') || 'en';

    if (!location) {
      return jsonResponse({ error: 'location parameter required' }, 400);
    }

    // Build locale: e.g. "en-US", "de", "fr"
    const hl = country === 'US' ? 'en-US' : lang;
    const googleUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(location)}&hl=${hl}&gl=${country}&ceid=${country}:${lang}`;

    try {
      const resp = await fetch(googleUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
      });

      if (!resp.ok) {
        return jsonResponse({ error: `Google News returned ${resp.status}` }, 502);
      }

      const xml = await resp.text();
      return new Response(xml, {
        headers: {
          ...corsHeaders(),
          'Content-Type': 'application/xml',
          'Cache-Control': 'public, max-age=300',
        },
      });
    } catch (err) {
      return jsonResponse({ error: 'Failed to fetch news' }, 502);
    }
  },
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...corsHeaders(),
      'Content-Type': 'application/json',
    },
  });
}
