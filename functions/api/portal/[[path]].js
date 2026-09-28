const ALLOWED = /^\/v1\/(?:auth\/(?:activate|login|staff\/(?:activate|login)|logout|me|csrf|sessions(?:\/[0-9a-f-]+)?)|me\/(?:academy|workspace|(?:party|duty)-workspace(?:\/assignments)?|students\/[^/]+\/current|transfers(?:\/[0-9a-f-]+\/consent)?|profile(?:\/months\/\d{4}-\d{2})?|requests(?:\/[0-9a-f-]+\/events)?|notifications(?:\/socket)?|transfer-recipients)|chat\/(?:(?:general|council)\/messages(?:\/[0-9a-f-]+\/moderate)?|restrictions)|instructions(?:\/[0-9a-f-]+\/acknowledge)?|cases(?:\/(?:teachers|targets)|\/[0-9a-f-]+(?:\/events)?)?)$/i;

export async function onRequest(context) {
  if (!context.env.PORTAL_API || typeof context.env.PORTAL_API.fetch !== 'function') {
    return Response.json({success:false,error:'portal_service_unavailable'}, {status:503, headers:{'Cache-Control':'private, no-store'}});
  }
  const suffix = Array.isArray(context.params.path) ? context.params.path.join('/') : String(context.params.path || '');
  const upstreamPath = '/v1/' + suffix.replace(/^v1\//, '');
  const governance=/^\/v1\/(?:admin\/(?:audit|party-policy)|me\/audit-events|party-governance(?:\/(?:pacts(?:\/[0-9a-f-]+\/(?:sign|terminate|review))?|bonds(?:\/[0-9a-f-]+\/sign)?|exits(?:\/[0-9a-f-]+\/review)?))?)$/i;
  const media=/^\/v1\/(?:gallery|me\/media|media\/(?:portraits|[0-9a-f-]+))$/i;
  if (!ALLOWED.test(upstreamPath)&&!governance.test(upstreamPath)&&!media.test(upstreamPath)) return Response.json({success:false,error:'not_found'}, {status:404});
  const incoming = new URL(context.request.url);
  const upstream = new URL('https://portal-api.internal' + upstreamPath + incoming.search);
  return context.env.PORTAL_API.fetch(new Request(upstream, context.request));
}
