# ${heading}

<dl>
%{ for variable_name, variable_data in variables ~}
<dt>${variable_name}</dt>
<dd>
<dl>
%{ for k, v in variable_data ~}
%{ if v != null ~}
<dt>${k}</dt>
<dd>
${v}
</dd>
%{ endif ~}
%{ endfor ~}
</dl>
</dd>
%{ endfor ~}
</dl>