const m = await import(process.argv[2]);
const pick = (arr, kind) => arr.map(x => ({ kind, id: x.id, name: x.name, endpoint: x.endpoint || x.id, imageField: x.imageField, lastImageField: x.lastImageField,
  hasPrompt: x.hasPrompt, category: x.category, provider: x.provider_name || x.provider || x.family,
  inputs: Object.fromEntries(Object.entries(x.inputs || {}).map(([k, v]) => [k, { type: v.type, enum: v.enum, default: v.default, min: v.minValue, max: v.maxValue }])) }));
const out = [...pick(m.t2vModels, "t2v"), ...pick(m.i2vModels, "i2v"), ...pick(m.v2vModels, "v2v"), ...pick(m.lipsyncModels, "lipsync"), ...pick(m.t2iModels, "t2i"), ...pick(m.i2iModels, "i2i")];
process.stdout.write(JSON.stringify(out, null, 1));
