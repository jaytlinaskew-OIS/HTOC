const fs=require('node:fs');
const {createRequire}=require('node:module');
const req=createRequire('C:/Users/jaskew/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/package.json');
const root='//cscso1fsappv01/home/jaskew/HTOC/dashboards/ThreatAssessment';
const state=JSON.parse(fs.readFileSync(root+'/design_reference_state.json','utf8'));
const theme=JSON.parse(fs.readFileSync(state.theme,'utf8'));
const schema=JSON.parse(fs.readFileSync(root+'/native_validation/theme_schema_2_139.json','utf8'));
const Ajv=req('ajv');const ajv=new Ajv({strict:false,validateFormats:false,allErrors:true});
const validate=ajv.compile(schema);if(!validate(theme)){throw new Error(JSON.stringify(validate.errors));}
if(theme.background!=='#171722'||theme.foreground!=='#D9D9D9'||theme.dataColors.some(c=>c!=='#303366'))throw new Error('Palette mismatch');
console.log('Theme schema and requested palette validation passed.');
