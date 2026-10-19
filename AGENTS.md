# ThreatConnect Playbook Files

When creating or updating ThreatConnect `.pbx` or `.pbxz` files:

- Start from a Playbook exported from the target ThreatConnect instance whenever possible. Reuse its app catalog definitions instead of inventing app metadata.
- For each app, preserve the exact `appCatalogItem.id`, `programName`, `displayName`, and `programVersion` from a known-good local export.
- Use the native **ThreatConnect Get Indicators** app with action `TQL` for indicator queries. Do not substitute the generic ThreatConnect API app unless the user explicitly requests it.
- Inspect the actual Get Indicators raw output before writing JMESPath. On this instance, Description is returned as the top-level `description` field; use Attribute-based locations only as fallbacks.
- When JMESPath `strip_quotes` is enabled, every String expression must always return a string. Wrap optional fields with a string fallback, for example `to_string(not_null(description, ''))`; a `null` result can raise `'NoneType' object has no attribute 'replace'`.
- Keep credentials, API tokens, sessions, and environment-specific secrets out of exported files.
- A `.pbxz` file is a ZIP archive containing `playbook.pbx`; include `preview.png` when producing a standard visual import package.
- Update the standalone `.pbx` and the copy packaged inside `.pbxz` together, then verify they match byte-for-byte.

## Required PBX serialization

Several PBX properties contain JSON encoded as strings. They must always encode arrays, including when empty or when containing one item:

```json
"outputVariables": "[]"
"layoutRequiredInputParams": "[\"json_data\"]"
"layoutDisplayedInputParams": "[\"json_data\",\"strip_quotes\"]"
```

Never serialize these properties as `null`, a scalar string, a single object, or a nested array. Incorrect shapes can cause ThreatConnect to import a completely blank Playbook.

The same rule applies to app parameters that contain encoded lists, including `array_inputs`, `array_outputs`, `string_expressions`, `string_array_expressions`, and `output_array`.

## Validation before delivery

- Parse the outer PBX document as JSON.
- Parse every encoded JSON-string field and confirm that list fields begin with `[` and end with `]`.
- Confirm every required app parameter has a non-empty value.
- Confirm every `#App:<id>:<output>!<type>` reference points to an existing upstream job and declared output.
- Confirm every connection references existing job or trigger IDs and that Iterator loops have valid `StartLoop` and `EndLoop` connections.
- Confirm job and trigger IDs are unique.
- Open the PBXZ and confirm it contains a readable `playbook.pbx`, the packaged PBX matches the standalone source, and any `preview.png` is readable.
- Keep production Timer triggers disabled until the WebHook test path imports and runs successfully.
- If a PBXZ behaves unexpectedly, import the standalone `.pbx` as a diagnostic because ThreatConnect supports both formats.
