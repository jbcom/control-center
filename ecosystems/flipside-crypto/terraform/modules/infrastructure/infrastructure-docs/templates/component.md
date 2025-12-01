# ${component_name}

This is a record of all outputs from existing assets for this component.

<table>
<tr>
<th>Key</th>
<th>Value</th>
</tr>
%{ for k, v in component_data ~}
%{ if v != null && v != "" && v != [] && v != {} ~}
<tr>
<td>${k}</td>
<td>
%{ if try(merge(v, {}), null) != null ~}
<table>
<tr>
<th>Key</th>
<th>Value</th>
</tr>
%{ for kk, vv in v ~}
<tr>
<td>${kk}</td>
%{ if try(tostring(vv), null) != null ~}
<td>${tostring(vv)}</td>
%{ else ~}
<td>

```yaml
${yamlencode(vv)}
```

</td>
%{ endif ~}
</tr>
%{ endfor ~}
</table>
%{ else ~}
%{ if try(concat(v, []), null) != null ~}
<ol>
%{ for elem in v ~}
%{ if try(tostring(elem), null) != null ~}
<li>${tostring(elem)}</li>
%{ else ~}
<li>

```yaml
${yamlencode(elem)}
```

</li>
%{ endif ~}
%{ endfor ~}
</ol>
%{ else ~}
%{ if try(tostring(v), null) != null ~}
${tostring(v)}
%{ else ~}

```yaml
${yamlencode(v)}
```

%{ endif ~}
%{ endif ~}
%{ endif ~}
</td>
</tr>
%{ endif ~}
%{ endfor ~}
</table>
