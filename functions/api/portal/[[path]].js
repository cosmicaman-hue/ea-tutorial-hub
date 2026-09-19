const ALLOWED = /^\/v1\/(?:auth\/(?:activate|login|logout|me|csrf|sessions(?:\/[0-9a-f-]+)?)|me\/(?:profile(?:\/months\/\d{4}-\d{2})?|requests(?:\/[0-9a-f-]+\/events)?|notifications(?:\/socket)?|transfer-recipients))$/i;

export async function onRequest(context) {
  if (!context.env.PORTAL_API || typeof context.env.PORTAL_API.fetch !== 'function') {
    return Response.json({success:false,error:'portal_service_unavailable'}, {status:503, headers:{'Cache-Control':'private, no-store'}});
  }
  const suffix = Array.isArray(context.params.path) ? context.params.path.join('/') : String(context.params.path || '');
  const upstreamPath = '/v1/' + suffix.replace(/^v1\//, '');
  if (!ALLOWED.test(upstreamPath)) return Response.json({success:false,error:'not_found'}, {status:404});
  const incoming = new URL(context.request.url);
  const upstream = new URL('https://portal-api.internal' + upstreamPath + incoming.search);
  return context.env.PORTAL_API.fetch(new Request(upstream, context.request));
}
